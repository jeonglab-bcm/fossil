"""Look for a new home for software whose cited location is dead (tiers D and E, iCite RCR >= 1).

Candidate tool names come from tool_names.py (title, dead own-resource links, abstract). Each name is looked up in:
  Bioconductor and CRAN   today's package lists (R's available.packages()), then CRAN's archive
                          (DESCRIPTION read from the newest archived tarball)
  PyPI                    https://pypi.org/pypi/<name>/json
  bio.tools               https://bio.tools/api/tool/?q=<name> (ELIXIR registry), exact name matches
A hit counts only when the package or registry page names the paper: its DOI, PMID or PMCID, a
link to the article, or most of the title's distinctive words; or the paper's first author's surname
together with a few title words. The homepage found is then checked with check_urls.check().

Writes new_homes.csv: one row per paper with the best verified hit (or none) and the evidence.
"""
import csv
import io
import json
import re
import tarfile
import subprocess
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from check_urls import check  # noqa: E402
from classify import classify  # noqa: E402
from tool_names import candidates  # noqa: E402

UA = "fossil-link-audit/0.1 (+https://github.com/jeonglab-bcm/fossil)"
S = requests.Session()
S.headers["User-Agent"] = UA
STOP = set("""a an and the of for in on to with by from using use based via its their is are be as at or new novel approach
method methods tool tools software package analysis data system framework web server database model models
prediction predicting predict improved efficient fast accurate large scale genome genomic sequence sequences protein
proteins gene genes expression identification detection integrated comprehensive automated""".split())


def words(text):
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP and len(w) > 2}


def get(url, **kw):
    for attempt in range(3):
        try:
            r = S.get(url, timeout=60, **kw)
            time.sleep(0.3)
            return r
        except requests.RequestException:
            time.sleep(2 ** attempt)
    return None


def first_authors(pmids):
    out = {}
    for i in range(0, len(pmids), 200):
        r = S.post("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                   data={"db": "pubmed", "id": ",".join(pmids[i:i + 200]), "retmode": "json"}, timeout=60)
        time.sleep(0.4)
        for uid, d in r.json().get("result", {}).items():
            if uid != "uids" and isinstance(d, dict) and d.get("authors"):
                out[uid] = d["authors"][0]["name"].split()[0]
    return out


def r_packages():
    expr = ('a <- available.packages(repos=BiocManager::repositories()); '
            'write.csv(data.frame(p=rownames(a), r=a[, "Repository"]), stdout(), row.names=FALSE)')
    out = subprocess.run(["Rscript", "-e", expr], capture_output=True, text=True, timeout=600).stdout
    pk = {}
    for row in csv.DictReader(out.splitlines()):
        repo = "Bioconductor" if "bioconductor" in row["r"] else "CRAN"
        pk[row["p"].lower()] = (row["p"], repo)
    return pk


def evidence(text, paper, author):
    """How the page names the paper, or '' if it does not."""
    t = text.lower()
    doi = paper["doi"].lower()
    if doi and (doi in t or doi.split("/", 1)[-1] in t):
        return "DOI"
    if paper["pmid"] in t or paper["pmcid"].lower() in t:
        return "PMID/PMCID"
    tw = words(paper["title"])
    share = len(tw & words(text)) / max(1, len(tw))
    if share >= 0.6:
        return f"title words {share:.0%}"
    if author and author.lower() in t and share >= 0.3:
        return f"first author + title words {share:.0%}"
    return ""


def bioc_or_cran(name, pk, paper, author):
    hit = pk.get(name.lower())
    if not hit:
        return None
    pkg, repo = hit
    url = (f"https://bioconductor.org/packages/{pkg}" if repo == "Bioconductor"
           else f"https://cran.r-project.org/package={pkg}")
    pages = [f"https://bioconductor.org/packages/release/bioc/html/{pkg}.html"] if repo == "Bioconductor" else [
        f"https://cran.r-project.org/web/packages/{pkg}/index.html",
        f"https://cran.r-project.org/web/packages/{pkg}/citation.html",
        f"https://cran.r-project.org/web/packages/{pkg}/DESCRIPTION"]
    text = " ".join(r.text for r in (get(u) for u in pages) if r is not None and r.status_code == 200)
    ev = evidence(text, paper, author)
    return {"where": repo, "home": url, "evidence": ev} if ev else None


def cran_archive(name, paper, author):
    """A package removed from CRAN: read DESCRIPTION from its newest archived tarball."""
    base = f"https://cran.r-project.org/src/contrib/Archive/{name}/"
    r = get(base)
    if r is None or r.status_code != 200:
        return None
    tars = re.findall(r'href="([^"]+\.tar\.gz)"', r.text)
    if not tars:
        return None
    t = get(base + tars[-1])
    if t is None or t.status_code != 200:
        return None
    try:
        with tarfile.open(fileobj=io.BytesIO(t.content)) as tf:
            m = next(x for x in tf.getmembers() if x.name.endswith("/DESCRIPTION") and x.name.count("/") == 1)
            text = tf.extractfile(m).read().decode(errors="replace")
    except (tarfile.TarError, StopIteration, OSError):
        return None
    ev = evidence(text, paper, author)
    return {"where": "CRAN archive (removed from CRAN)", "home": base, "evidence": ev} if ev else None


def pypi(name, paper, author):
    r = get(f"https://pypi.org/pypi/{name}/json")
    if r is None or r.status_code != 200:
        return None
    info = r.json()["info"]
    text = " ".join(str(info.get(k) or "") for k in ("summary", "description", "home_page", "author"))
    text += " " + json.dumps(info.get("project_urls") or {})
    ev = evidence(text, paper, author)
    return {"where": "PyPI", "home": f"https://pypi.org/project/{info['name']}/", "evidence": ev} if ev else None


def biotools(name, paper, author):
    r = get("https://bio.tools/api/tool/", params={"q": name, "format": "json"})
    if r is None or r.status_code != 200:
        return None
    for t in r.json().get("list", [])[:10]:
        if t.get("name", "").lower() != name.lower() and t.get("biotoolsID", "").lower() != name.lower():
            continue
        text = json.dumps(t)
        ev = evidence(text, paper, author)
        if ev:
            links = [t.get("homepage")] + [x.get("url") for x in (t.get("download") or []) + (t.get("link") or [])]
            code = next((u for u in links if u and re.search(r"github|gitlab|bitbucket|sourceforge|bioconductor|cran", u)), None)
            return {"where": "bio.tools", "home": code or t.get("homepage"), "evidence": ev,
                    "registry": f"https://bio.tools/{t.get('biotoolsID')}"}
    return None


def main():
    papers = candidates()
    authors = first_authors([p["pmid"] for p in papers])
    pk = r_packages()
    rows = []
    for i, p in enumerate(papers):
        a = authors.get(p["pmid"], "")
        hit = None
        for src, name in p["names"][:4]:
            for fn in (lambda n: bioc_or_cran(n, pk, p, a), lambda n: pypi(n, p, a), lambda n: biotools(n, p, a)):
                hit = fn(name)
                if hit:
                    hit["name"] = name
                    break
            if hit:
                break
        if not hit:  # packages removed from CRAN, checked last
            for src, name in p["names"][:3]:
                hit = cran_archive(name, p, a)
                if hit:
                    hit["name"] = name
                    break
        status = ""
        if hit and hit.get("home"):
            st = check(hit["home"])
            status = classify(st)[0] if st.get("outcome") else ""
        rows.append({"pmcid": p["pmcid"], "year": p["year"], "rcr": p["rcr"], "title": p["title"],
                     "names_tried": "; ".join(n for _, n in p["names"][:4]),
                     "found": bool(hit), "tool_name": (hit or {}).get("name", ""), "where": (hit or {}).get("where", ""),
                     "new_home": (hit or {}).get("home", ""), "home_status": status,
                     "evidence": (hit or {}).get("evidence", ""), "registry": (hit or {}).get("registry", ""),
                     "dead_links": " ".join(p["dead_links"][:3])})
        print(i, p["pmcid"], rows[-1]["where"], rows[-1]["new_home"], rows[-1]["evidence"], file=sys.stderr, flush=True)
    with open("new_homes.csv", "w", newline="") as f:
        w = csv.DictWriter(f, list(rows[0]))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()

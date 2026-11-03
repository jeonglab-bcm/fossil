"""Fetch citation metrics and subject tags for every paper in papers.csv, in batches.

  OpenAlex     /works?filter=pmid:...      cited_by_count, counts_by_year, FWCI, citation percentile,
                                           primary topic, keywords   (100 PMIDs per request)
  iCite (NIH)  /api/pubs?pmids=...         citation_count, relative citation ratio (RCR), NIH percentile
                                           (100 PMIDs per request)
  PubMed       elink pubmed_pmc_refs       number of PMC articles citing the paper (50 PMIDs per request)
  Europe PMC   /search EXT_ID:... SRC:MED  citedByCount (100 PMIDs per request)
  PubMed       efetch (XML)                MeSH headings, major topics marked (200 PMIDs per request)

Each source is cached in cache/citations/<source>.json, so a source that fails (OpenAlex without
an API key shares a small daily budget per network) can be fetched again later without
re-fetching the others. Environment: FOSSIL_CONTACT_EMAIL (contact address sent to OpenAlex and
NCBI), OPENALEX_API_KEY (optional). Writes citations.csv with the retrieval dates.
"""
import csv
import json
import os
import re
import sys
import time
from datetime import date
from pathlib import Path

import requests

EMAIL = os.environ.get("FOSSIL_CONTACT_EMAIL", "")
OPENALEX_KEY = os.environ.get("OPENALEX_API_KEY", "")
CACHE = Path("cache/citations")
S = requests.Session()
S.headers["User-Agent"] = "fossil-citation-audit/0.1 (+https://github.com/jeonglab-bcm/fossil)" + (
    f"; mailto:{EMAIL}" if EMAIL else "")
LAST5 = range(date.today().year - 5, date.today().year)  # last five complete years
# MeSH check tags and other headings that describe the study, not its subject.
CHECK_TAGS = {"Humans", "Animals", "Male", "Female", "Mice", "Rats", "Adult", "Middle Aged", "Aged", "Child",
              "Adolescent", "Young Adult", "Infant", "Child, Preschool", "Aged, 80 and over", "Infant, Newborn",
              "Pregnancy", "Cattle", "Dogs", "Cats", "Swine", "Rabbits", "Sheep", "Guinea Pigs", "Cricetinae"}


class OutOfBudget(Exception):
    pass


def call(method, url, pause, **kw):
    for attempt in range(5):
        try:
            r = S.request(method, url, timeout=120, **kw)
            if r.status_code == 200:
                time.sleep(pause)
                return r
            if r.status_code == 429 and "openalex" in url and r.headers.get("X-RateLimit-Remaining") == "0":
                raise OutOfBudget(r.text[:200])  # OpenAlex's daily budget, not a per-second limit
            if r.status_code == 429:  # NCBI and others: per-second limits, so wait and retry
                time.sleep(5 * (attempt + 1))
                continue
            print("HTTP", r.status_code, url, r.text[:150], file=sys.stderr)
            if r.status_code in (400, 401, 402, 403):
                return None
        except requests.RequestException as e:
            print("retry", attempt + 1, type(e).__name__, file=sys.stderr)
        time.sleep(2 ** attempt)
    return None


def chunks(xs, n):
    for i in range(0, len(xs), n):
        yield xs[i:i + n]


def openalex(pmids):
    out = {}
    select = "id,ids,cited_by_count,counts_by_year,fwci,citation_normalized_percentile,primary_topic,keywords"
    for part in chunks(pmids, 100):
        params = {"filter": "pmid:" + "|".join(part), "per-page": 100, "select": select}
        if EMAIL:
            params["mailto"] = EMAIL
        if OPENALEX_KEY:
            params["api_key"] = OPENALEX_KEY
        r = call("GET", "https://api.openalex.org/works", 0.2, params=params)
        for w in (r.json() if r else {}).get("results", []):
            pmid = (w.get("ids") or {}).get("pmid", "").rsplit("/", 1)[-1]
            by_year = {c["year"]: c["cited_by_count"] for c in w.get("counts_by_year") or []}
            topic = w.get("primary_topic") or {}
            pct = w.get("citation_normalized_percentile") or {}
            out[pmid] = {
                "openalex_id": w["id"].rsplit("/", 1)[-1],
                "oa_cited_by": w.get("cited_by_count"),
                "oa_cited_by_last5y": sum(by_year.get(y, 0) for y in LAST5),
                "oa_fwci": w.get("fwci"),
                "oa_citation_percentile": round(pct["value"], 4) if pct.get("value") is not None else "",
                "oa_top10pct": pct.get("is_in_top_10_percent", ""),
                "oa_topic": topic.get("display_name", ""),
                "oa_subfield": (topic.get("subfield") or {}).get("display_name", ""),
                "oa_field": (topic.get("field") or {}).get("display_name", ""),
                "oa_keywords": "; ".join(k["display_name"] for k in (w.get("keywords") or [])[:4]),
            }
        print("openalex", len(out), file=sys.stderr, flush=True)
    return out


def icite(pmids):
    out = {}
    fl = "pmid,citation_count,relative_citation_ratio,nih_percentile,citations_per_year,expected_citations_per_year"
    for part in chunks(pmids, 100):
        r = call("GET", "https://icite.od.nih.gov/api/pubs", 0.3, params={"pmids": ",".join(part), "fl": fl})
        for p in (r.json() if r else {}).get("data", []):
            rnd = lambda k, n: round(p[k], n) if p.get(k) is not None else ""  # noqa: E731
            out[str(p["pmid"])] = {
                "icite_citations": p.get("citation_count"), "icite_rcr": rnd("relative_citation_ratio", 3),
                "icite_nih_percentile": p.get("nih_percentile"),
                "icite_citations_per_year": rnd("citations_per_year", 2),
                "icite_expected_per_year": rnd("expected_citations_per_year", 2)}
    print("icite", len(out), file=sys.stderr)
    return out


def pmc_citing(pmids):
    out = {}
    for part in chunks(pmids, 50):
        data = [("dbfrom", "pubmed"), ("linkname", "pubmed_pmc_refs"), ("retmode", "json"), ("tool", "fossil")]
        if EMAIL:
            data.append(("email", EMAIL))
        data += [("id", p) for p in part]  # one id parameter each, so links come back per paper
        r = call("POST", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi", 0.4, data=data)
        for ls in (r.json() if r else {}).get("linksets", []):
            dbs = ls.get("linksetdbs") or []
            out[str(ls["ids"][0])] = {"pmc_citing": len(dbs[0].get("links", [])) if dbs else 0}
    print("pmc", len(out), file=sys.stderr)
    return out


def europepmc(pmids):
    out = {}
    for part in chunks(pmids, 100):
        q = "(" + " OR ".join(f"EXT_ID:{p}" for p in part) + ") AND SRC:MED"
        r = call("GET", "https://www.ebi.ac.uk/europepmc/webservices/rest/search", 0.3,
                 params={"query": q, "format": "json", "resultType": "lite", "pageSize": 1000})
        for x in (((r.json() if r else {}).get("resultList") or {}).get("result", [])):
            out[str(x.get("pmid"))] = {"europepmc_cited_by": x.get("citedByCount")}
    print("europepmc", len(out), file=sys.stderr)
    return out


def mesh(pmids):
    out = {}
    for part in chunks(pmids, 200):
        data = {"db": "pubmed", "id": ",".join(part), "retmode": "xml", "tool": "fossil"}
        if EMAIL:
            data["email"] = EMAIL
        r = call("POST", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi", 0.4, data=data)
        for art in re.findall(r"(?s)<PubmedArticle>.*?</PubmedArticle>", r.text if r else ""):
            pmid = re.search(r'<PMID Version="\d+">(\d+)</PMID>', art).group(1)
            major, other = [], []
            for block in re.findall(r"(?s)<MeshHeading>(.*?)</MeshHeading>", art):
                d = re.search(r'<DescriptorName[^>]*MajorTopicYN="(\w)"[^>]*>([^<]+)</DescriptorName>', block)
                if not d or d.group(2) in CHECK_TAGS:
                    continue
                is_major = d.group(1) == "Y" or 'QualifierName UI="' in block and 'MajorTopicYN="Y"' in block.split(
                    "</DescriptorName>", 1)[1]
                (major if is_major else other).append(d.group(2))
            out[pmid] = {"mesh_major": "; ".join(major), "mesh_other": "; ".join(other)}
    print("mesh", len(out), file=sys.stderr)
    return out


SOURCES = {"openalex": openalex, "icite": icite, "pmc": pmc_citing, "europepmc": europepmc, "mesh": mesh}


def main(*only):
    CACHE.mkdir(parents=True, exist_ok=True)
    with open("papers.csv") as f:
        papers = list(csv.DictReader(l for l in f if not l.startswith("#")))
    pmids = [p["pmid"] for p in papers]
    results, dates = {}, {}
    for name, fn in SOURCES.items():
        path = CACHE / f"{name}.json"
        if path.exists() and name not in only:
            cached = json.loads(path.read_text())
            results[name], dates[name] = cached["data"], cached["retrieved"]
            continue
        try:
            data = fn(pmids)
        except OutOfBudget as e:
            print(f"{name}: out of budget, skipped ({e})", file=sys.stderr)
            continue
        path.write_text(json.dumps({"retrieved": str(date.today()), "data": data}))
        results[name], dates[name] = data, str(date.today())
    fields = ["pmid", "pmcid", "openalex_id", "oa_cited_by", "oa_cited_by_last5y", "oa_fwci", "oa_citation_percentile",
              "oa_top10pct", "oa_topic", "oa_subfield", "oa_field", "oa_keywords", "icite_citations", "icite_rcr",
              "icite_nih_percentile", "icite_citations_per_year", "icite_expected_per_year", "pmc_citing",
              "europepmc_cited_by", "mesh_major", "mesh_other"]
    with open("citations.csv", "w", newline="") as f:
        f.write("# retrieved: " + ", ".join(f"{k} {v}" for k, v in dates.items()) +
                ("" if "openalex" in dates else "; openalex not yet fetched") + "\n")
        w = csv.DictWriter(f, fields)
        w.writeheader()
        for p in papers:
            row = {"pmid": p["pmid"], "pmcid": "PMC" + p["pmcid"].removeprefix("PMC")}
            for data in results.values():
                row.update(data.get(p["pmid"], {}))
            w.writerow(row)
    print("coverage:", {k: len(v) for k, v in results.items()}, "of", len(pmids), file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:])

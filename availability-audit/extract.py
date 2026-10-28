"""Extract URLs, repository accessions, and supplementary files from each paper's JATS XML.

Reads cache/articles/<PMCID>.xml and .json (from fetch_articles.py). Looks only at the abstract,
body, and back matter; reference lists, citations, and license/permissions text are dropped, so a
URL counts only when the paper's own text names it.

Writes:
  urls.csv         one row per paper x distinct URL, with the section it first appears in
  accessions.csv   one row per paper x distinct accession
  supplements.csv  one row per supplementary file named in the XML, and whether the PMC dataset has it
"""
import csv
import glob
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

from lxml import etree

XLINK = "{http://www.w3.org/1999/xlink}href"
DROP = {"ref-list", "ref", "element-citation", "mixed-citation", "citation", "permissions", "license",
        "copyright-statement", "self-uri", "related-article", "contrib-group", "aff", "author-notes",
        "funding-group", "kwd-group"}
PARA = {"p", "title", "td", "th", "label", "def", "preformat", "code", "attrib", "list-item", "fn"}
URL_RE = re.compile(r"(?i)\b(?:(?:https?|ftp)://|www\d{0,3}\.)[^\s<>\"'“”‘’ ]+")
TRAIL = ".,;:!?'\"*>»"
# Repository accessions (patterns are specific enough to use on free text).
ACC_RE = {
    "GEO": re.compile(r"\bG(?:SE|SM|PL|DS)\d{1,7}\b"),
    "SRA/ENA/DDBJ": re.compile(r"\b[SED]R[APRSXZ]\d{6,9}\b"),
    "BioProject": re.compile(r"\bPRJ(?:NA|EB|DB)\d{1,7}\b"),
    "BioSample": re.compile(r"\bSAM(?:N|EA|D)\d{5,9}\b"),
    "ArrayExpress": re.compile(r"\bE-[A-Z]{4}-\d{1,6}\b"),
    "dbGaP": re.compile(r"\bphs\d{6}(?:\.v\d+\.p\d+)?\b"),
    "EGA": re.compile(r"\bEGA[SD]\d{11}\b"),
    "RefSeq": re.compile(r"\b(?:NC|NG|NM|NP|NR|NT|NW|XM|XP|XR|YP|WP)_\d{6,9}(?:\.\d+)?\b"),
}
# PDB IDs are four characters and collide with ordinary words, so take them only after "PDB".
PDB_CTX = re.compile(r"(?:\bPDB\b|Protein Data Bank)[^.;\n]{0,80}")
PDB_ID = re.compile(r"\b[1-9](?=[0-9A-Za-z]{0,2}[A-Za-z])[0-9A-Za-z]{3}\b")
EXT_TYPES = {"gen": "GenBank", "genbank": "GenBank", "pdb": "PDB", "geo": "GEO", "uniprot": "UniProt",
             "sprot": "UniProt", "embl": "GenBank", "ensembl": "Ensembl", "arrayexpress": "ArrayExpress"}
AVAIL = re.compile(r"(?i)availab|software|implement|download|requirement|source code|web ?server|"
                   r"data access|url|resource|program|package|tool")


def clean_url(u):
    u = u.strip().replace("​", "")
    while u and u[-1] in TRAIL:
        u = u[:-1]
    while u.endswith(")") and u.count("(") < u.count(")"):
        u = u[:-1]
    while u.endswith("]") and u.count("[") < u.count("]"):
        u = u[:-1]
    if u.lower().startswith("www"):
        u = "http://" + u
    try:
        p = urlsplit(u)
    except ValueError:
        return None
    if p.scheme.lower() not in ("http", "https", "ftp") or "." not in (p.hostname or ""):
        return None
    return u


def url_key(u):
    p = urlsplit(u)
    host = (p.hostname or "").lower()
    port = f":{p.port}" if p.port and p.port not in (80, 443, 21) else ""
    return f"{host}{port}{p.path.rstrip('/')}{'?' + p.query if p.query else ''}"


def section_path(el, region):
    titles = []
    for a in el.iterancestors():
        if a.tag in ("sec", "app", "boxed-text", "abstract"):
            t = a.find("title")
            if t is not None and "".join(t.itertext()).strip():
                titles.append(" ".join("".join(t.itertext()).split())[:60])
    return " > ".join([region] + titles[::-1])


def regions(root):
    meta = root.find("front/article-meta")
    if meta is not None:
        for ab in meta.findall("abstract"):
            yield "abstract", ab
    for tag in ("body", "back"):
        el = root.find(tag)
        if el is not None:
            yield tag, el


def parse(pmcid):
    xml = Path(f"cache/articles/{pmcid}.xml")
    meta = json.loads(Path(f"cache/articles/{pmcid}.json").read_text())["chosen"]
    root = etree.parse(str(xml), etree.XMLParser(resolve_entities=False, no_network=True,
                                                  huge_tree=True)).getroot()
    # JATS from PMC has an <article> root; some files wrap it.
    if root.tag != "article":
        root = root.find(".//article")
    for el in list(root.iter(*DROP)):
        if el.getparent() is not None:
            el.getparent().remove(el)

    urls, accs, supps = {}, {}, []

    def add_url(raw, sec, ext):
        u = clean_url(raw)
        if u:
            k = url_key(u)
            if k not in urls:
                urls[k] = {"url": u, "section": sec, "ext_link": ext}
            elif ext and not urls[k]["ext_link"]:
                urls[k].update(url=u, ext_link=True)

    def add_acc(kind, acc, how):
        acc = acc.strip()
        if acc and (kind, acc.upper()) not in accs:
            accs[(kind, acc.upper())] = {"type": kind, "accession": acc, "found_by": how}

    for region, el in regions(root):
        for link in el.iter("ext-link", "uri"):
            sec = section_path(link, region)
            href = link.get(XLINK) or "".join(link.itertext())
            etype = (link.get("ext-link-type") or "uri").lower()
            if etype in EXT_TYPES:
                add_acc(EXT_TYPES[etype], href.split("/")[-1], "ext-link")
            elif href:
                add_url(href, sec, True)
        for p in el.iter(*PARA):
            text = " ".join("".join(p.itertext()).split())
            if not text:
                continue
            sec = section_path(p, region)
            for m in URL_RE.finditer(text):
                add_url(m.group(0), sec, False)
            for kind, rx in ACC_RE.items():
                for m in rx.finditer(text):
                    add_acc(kind, m.group(0), "text")
            for ctx in PDB_CTX.finditer(text):
                for m in PDB_ID.finditer(ctx.group(0)):
                    add_acc("PDB", m.group(0), "text")

    media = {u.split("/")[-1].split("?")[0]: u for u in (meta.get("media_urls") or [])}
    for sm in root.iter("supplementary-material"):
        hrefs = [sm.get(XLINK)] + [m.get(XLINK) for m in sm.iter("media", "inline-supplementary-material")]
        caption = " ".join("".join(sm.find("caption").itertext()).split())[:200] if sm.find("caption") is not None else ""
        for h in dict.fromkeys(h for h in hrefs if h):
            name = h.split("/")[-1]
            s3 = media.get(name, "")
            supps.append({"href": h, "caption": caption, "in_dataset": bool(s3),
                          "s3_url": s3.split("?")[0], "md5": s3.split("md5=")[-1] if "md5=" in s3 else ""})

    for u in urls.values():
        u["host"] = (urlsplit(u["url"]).hostname or "").lower()
        u["availability_section"] = bool(u["section"].startswith("abstract") or AVAIL.search(u["section"]))
    return pmcid, meta, list(urls.values()), list(accs.values()), supps


def main():
    files = sorted(glob.glob("cache/articles/*.xml"))
    out = {name: open(f"{name}.csv", "w", newline="") for name in ("urls", "accessions", "supplements")}
    writers = {
        "urls": csv.DictWriter(out["urls"], ["pmcid", "url", "host", "section", "availability_section",
                                              "ext_link"]),
        "accessions": csv.DictWriter(out["accessions"], ["pmcid", "type", "accession", "found_by"]),
        "supplements": csv.DictWriter(out["supplements"], ["pmcid", "href", "caption", "in_dataset",
                                                            "s3_url", "md5"]),
    }
    for w in writers.values():
        w.writeheader()
    errors = 0
    for i, f in enumerate(files):
        pmcid = Path(f).stem
        try:
            _, meta, urls, accs, supps = parse(pmcid)
        except Exception as e:  # noqa: BLE001
            errors += 1
            print(pmcid, "parse error:", e, file=sys.stderr)
            continue
        for u in urls:
            writers["urls"].writerow({"pmcid": pmcid, **u})
        for a in accs:
            writers["accessions"].writerow({"pmcid": pmcid, **a})
        for s in supps:
            writers["supplements"].writerow({"pmcid": pmcid, **s})
        if i % 1000 == 0:
            print(i, file=sys.stderr)
    for f in out.values():
        f.close()
    print(len(files), "papers,", errors, "parse errors", file=sys.stderr)


if __name__ == "__main__":
    main()

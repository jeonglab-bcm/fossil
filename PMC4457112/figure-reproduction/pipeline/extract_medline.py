#!/usr/bin/env python3
"""Stream the PubMed baseline and keep the human-related citations of 1987-2012.

For each baseline file: download it (or read a local copy), check its MD5 against NCBI's .md5
file, record its SHA-256, parse it, keep the records whose publication year is 1987-2012 and
whose MeSH headings include Humans (D006801), and write them to one Parquet file. The
downloaded file is deleted afterwards unless --keep is given, so the scan needs only a few GB.

The language and abstract flags are kept as columns, so the dataset query
(humans[mh] AND hasabstract AND english[la], see the README) is applied later, not here.

Usage:
  extract_medline.py --out DIR [--files 1-1334] [--workers 4] [--keep] [--local DIR]
"""
import argparse
import gzip
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import pyarrow as pa
import pyarrow.parquet as pq
from lxml import etree

BASE = "https://ftp.ncbi.nlm.nih.gov/pubmed/baseline/"
PREFIX = "pubmed26n"
HUMANS = "D006801"
RCT_PT = "D016449"
YEAR_RE = re.compile(r"(1[89]\d\d|20\d\d)")
ARTICLE_RE = re.compile(rb"<PubmedArticle>.*?</PubmedArticle>", re.S)
PUBDATE_RE = re.compile(rb"<PubDate>(.*?)</PubDate>", re.S)
YEAR_B_RE = re.compile(rb"(1[89]\d\d|20\d\d)")
HUMANS_B = b'UI="D006801"'
PARSER = etree.XMLParser(huge_tree=True, resolve_entities=False)

SCHEMA = pa.schema([
    ("pmid", pa.int64()),
    ("year", pa.int16()),
    ("english", pa.bool_()),
    ("has_abstract", pa.bool_()),
    ("title", pa.string()),
    ("abstract", pa.string()),
    ("journal", pa.string()),
    ("authors", pa.string()),      # "Last Initials" joined by "|"
    ("n_authors", pa.int32()),
    ("mesh", pa.string()),         # descriptor UI joined by "|", "*" prefix for major topic
    ("mesh_qual", pa.string()),    # descriptor UI/qualifier UI pairs joined by "|"
    ("pubtypes", pa.string()),     # publication type UI joined by "|"
    ("chemicals", pa.string()),    # substance UI joined by "|"
    ("keywords", pa.string()),     # author keywords, lower case, joined by "|"
    ("rct", pa.bool_()),
])


def text_of(el):
    return "".join(el.itertext()).strip() if el is not None else ""


def pub_year(art):
    pd = art.find("Journal/JournalIssue/PubDate")
    if pd is None:
        return None
    y = pd.findtext("Year")
    if y and y.strip().isdigit():
        return int(y.strip())
    m = YEAR_RE.search(pd.findtext("MedlineDate") or "")
    return int(m.group(1)) if m else None


def parse_record(cit):
    art = cit.find("Article")
    if art is None:
        return None
    mesh_el = cit.findall("MeshHeadingList/MeshHeading")
    desc = [m.find("DescriptorName") for m in mesh_el]
    uis = [d.get("UI") for d in desc if d is not None]
    if HUMANS not in uis:
        return None
    year = pub_year(art)
    if year is None or year < 1987 or year > 2012:
        return None
    mesh, mesh_qual = [], []
    for m in mesh_el:
        d = m.find("DescriptorName")
        if d is None:
            continue
        major = d.get("MajorTopicYN") == "Y" or any(q.get("MajorTopicYN") == "Y" for q in m.findall("QualifierName"))
        mesh.append(("*" if major else "") + d.get("UI"))
        for q in m.findall("QualifierName"):
            mesh_qual.append(d.get("UI") + "/" + q.get("UI"))
    parts = []
    for a in art.findall("Abstract/AbstractText"):
        t = text_of(a)
        lab = a.get("Label")
        if lab and lab.upper() not in ("UNLABELLED", "UNASSIGNED"):
            t = lab + ": " + t
        if t:
            parts.append(t)
    abstract = " ".join(parts)
    authors = []
    for au in art.findall("AuthorList/Author"):
        last = au.findtext("LastName")
        if last:
            authors.append((last + " " + (au.findtext("Initials") or "")).strip())
        else:
            coll = au.findtext("CollectiveName")
            if coll:
                authors.append(coll.strip())
    langs = [l.text or "" for l in art.findall("Language")]
    pts = [p.get("UI") for p in art.findall("PublicationTypeList/PublicationType")]
    journal = cit.findtext("MedlineJournalInfo/MedlineTA") or art.findtext("Journal/ISOAbbreviation") or ""
    return {
        "pmid": int(cit.findtext("PMID")),
        "year": year,
        "english": "eng" in langs,
        "has_abstract": bool(abstract),
        "title": text_of(art.find("ArticleTitle")),
        "abstract": abstract,
        "journal": journal.strip(),
        "authors": "|".join(authors),
        "n_authors": len(authors),
        "mesh": "|".join(mesh),
        "mesh_qual": "|".join(mesh_qual),
        "pubtypes": "|".join(p for p in pts if p),
        "chemicals": "|".join(c.get("UI") or "" for c in cit.findall("ChemicalList/Chemical/NameOfSubstance")),
        "keywords": "|".join(text_of(k).lower().replace("|", " ") for k in cit.findall("KeywordList/Keyword")),
        "rct": RCT_PT in pts,
    }


def fetch(url, dest):
    for attempt in range(6):
        r = subprocess.run(["curl", "-sS", "--retry", "5", "--retry-all-errors", "-o", dest, url])
        if r.returncode == 0:
            return
        time.sleep(5 * (attempt + 1))
    raise RuntimeError("download failed: " + url)


def process(n, out, keep, local, tmp):
    name = f"{PREFIX}{n:04d}.xml.gz"
    target = os.path.join(out, f"{PREFIX}{n:04d}.parquet")
    meta_path = target + ".json"
    if os.path.exists(target) and os.path.exists(meta_path):
        with open(meta_path) as fh:
            return json.load(fh)
    src = os.path.join(local, name) if local and os.path.exists(os.path.join(local, name)) else None
    if src is None:
        src = os.path.join(tmp, name)
        for attempt in range(3):
            fetch(BASE + name, src)
            fetch(BASE + name + ".md5", src + ".md5")
            with open(src + ".md5") as fh:
                want = fh.read().strip().split()[-1]
            got = hashlib.md5(open(src, "rb").read()).hexdigest()
            if got == want:
                break
        else:
            raise RuntimeError(f"MD5 mismatch for {name}")
    sha = hashlib.sha256(open(src, "rb").read()).hexdigest()
    rows, total = [], 0
    with gzip.open(src, "rb") as fh:
        data = fh.read()
    # Split into <PubmedArticle> records and parse only those that can pass the filter: the Humans
    # descriptor UI is present and the PubDate year can be 1987-2012. parse_record applies the
    # filter exactly; this only skips records that cannot pass it.
    for chunk in ARTICLE_RE.finditer(data):
        total += 1
        rec_bytes = chunk.group(0)
        if HUMANS_B not in rec_bytes:
            continue
        pd = PUBDATE_RE.search(rec_bytes)
        if pd is not None and not any(1987 <= int(y) <= 2012 for y in YEAR_B_RE.findall(pd.group(1))):
            continue
        el = etree.fromstring(rec_bytes, parser=PARSER)
        cit = el.find("MedlineCitation")
        rec = parse_record(cit) if cit is not None else None
        if rec is not None:
            rows.append(rec)
    del data
    table = pa.Table.from_pylist(rows, schema=SCHEMA)
    pq.write_table(table, target + ".tmp", compression="zstd")
    os.replace(target + ".tmp", target)
    meta = {"file": name, "sha256": sha, "records": total, "kept": len(rows),
            "rct": sum(r["rct"] for r in rows)}
    with open(meta_path, "w") as fh:
        json.dump(meta, fh)
    if not keep and not (local and src.startswith(local)):
        os.remove(src)
        if os.path.exists(src + ".md5"):
            os.remove(src + ".md5")
    return meta


def parse_range(s):
    out = []
    for part in s.split(","):
        a, _, b = part.partition("-")
        out.extend(range(int(a), int(b or a) + 1))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--files", default="1-1334")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--local", default=None, help="folder with already downloaded baseline files")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    tmp = os.path.join(a.out, "_download")
    os.makedirs(tmp, exist_ok=True)
    files = parse_range(a.files)
    done = 0
    with ProcessPoolExecutor(a.workers) as ex:
        futs = {ex.submit(process, n, a.out, a.keep, a.local, tmp): n for n in files}
        for f in as_completed(futs):
            m = f.result()
            done += 1
            print(f"{done}/{len(files)} {m['file']} records={m['records']} kept={m['kept']} rct={m['rct']}", flush=True)
    manifest = []
    for n in files:
        with open(os.path.join(a.out, f"{PREFIX}{n:04d}.parquet.json")) as fh:
            manifest.append(json.load(fh))
    with open(os.path.join(a.out, "manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=0)


if __name__ == "__main__":
    sys.exit(main())

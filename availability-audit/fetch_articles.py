"""Download each paper's JSON metadata and JATS XML from the PMC Article Datasets on AWS.

Source: s3://pmc-oa-opendata over HTTPS (https://pmc.ncbi.nlm.nih.gov/tools/pmcaws/). PMC lists
this Cloud Service among the services that may be used for automated retrieval. Files go to
cache/ (not committed: we do not redistribute the papers). Reruns skip files already present.
"""
import csv
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

S3 = "https://pmc-oa-opendata.s3.amazonaws.com/"
CACHE = Path("cache/articles")
session = requests.Session()


def get(url):
    for attempt in range(4):
        try:
            r = session.get(url, timeout=120)
            if r.status_code in (200, 404):
                return r
        except requests.RequestException:
            pass
    raise RuntimeError(url)


def versions(pmcid):
    r = get(f"{S3}?list-type=2&prefix={pmcid}.&delimiter=/")
    return sorted(int(v) for v in re.findall(rf"<Prefix>{pmcid}\.(\d+)/</Prefix>", r.text))


def fetch(pmcid):
    meta_path = CACHE / f"{pmcid}.json"
    if not meta_path.exists():
        metas = []
        for v in versions(pmcid):
            r = get(f"{S3}metadata/{pmcid}.{v}.json")
            if r.status_code == 200:
                metas.append(r.json())
        if not metas:
            return pmcid, "not in bucket"
        # Prefer the open-access, non-manuscript version; otherwise the latest.
        metas.sort(key=lambda m: (m.get("is_pmc_openaccess", False), not m.get("is_manuscript"), m["version"]))
        meta_path.write_text(json.dumps({"chosen": metas[-1], "all_versions": metas}))
    meta = json.loads(meta_path.read_text())["chosen"]
    xml_path = CACHE / f"{pmcid}.xml"
    if not xml_path.exists():
        r = get(meta["xml_url"].replace("s3://pmc-oa-opendata/", S3).split("?")[0])
        if r.status_code != 200:
            return pmcid, "xml missing"
        xml_path.write_bytes(r.content)
    return pmcid, "ok"


def main(papers="papers.csv"):
    CACHE.mkdir(parents=True, exist_ok=True)
    with open(papers) as f:
        ids = [f"PMC{r['pmcid'].removeprefix('PMC')}" for r in csv.DictReader(l for l in f if not l.startswith("#"))]
    status = {}
    with ThreadPoolExecutor(16) as ex:
        for i, (pmcid, s) in enumerate(ex.map(fetch, ids)):
            status[pmcid] = s
            if s != "ok":
                print(pmcid, s, file=sys.stderr)
            if i % 500 == 0:
                print(i, file=sys.stderr)
    print({s: sum(v == s for v in status.values()) for s in set(status.values())}, file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:])

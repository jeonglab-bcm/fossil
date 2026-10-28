"""Count PubMed Central articles per year that mention each keyword group.

Source: NCBI E-utilities esearch on db=pmc, which searches full text
(including references). Terms are pinned to [All Fields] so PMC's automatic
term mapping cannot widen them (e.g. "python" -> Boidae MeSH).
Writes counts.csv: year, group, query, count, total, share.
"""
import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import date

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
YEARS = range(2010, 2027)

GROUPS = {
    "GitHub + GitLab": '"github"[All Fields] OR "gitlab"[All Fields]',
    "SourceForge": '"sourceforge"[All Fields]',
    "NCBI GEO": '"gene expression omnibus"[All Fields] OR "ncbi geo"[All Fields]',
    "Python": '"python"[All Fields] NOT ("snake"[All Fields] OR "snakes"[All Fields] OR "boidae"[All Fields])',
    "CRAN + Bioconductor": '"cran"[All Fields] OR "bioconductor"[All Fields]',
}


def count(term):
    url = EUTILS + "?" + urllib.parse.urlencode(
        {"db": "pmc", "term": term, "retmax": 0, "retmode": "json"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                res = json.load(r)["esearchresult"]
            if res.get("errorlist"):
                raise RuntimeError(res["errorlist"])
            time.sleep(0.4)  # stay under 3 requests/s without an API key
            return int(res["count"])
        except Exception as e:  # noqa: BLE001
            print(f"retry {attempt + 1}: {e}", file=sys.stderr)
            time.sleep(2 ** attempt)
    raise RuntimeError(f"failed: {term}")


def main(out="counts.csv"):
    rows = []
    for year in YEARS:
        ydate = f"{year}[pdat]"
        total = count(ydate)
        for name, q in GROUPS.items():
            n = count(f"({q}) AND {ydate}")
            rows.append({"year": year, "group": name, "query": f"({q}) AND {ydate}",
                         "count": n, "total": total, "share": n / total})
            print(year, name, n, total, file=sys.stderr)
    with open(out, "w", newline="") as f:
        f.write(f"# PMC full-text counts, NCBI E-utilities, retrieved {date.today()}\n")
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main(*sys.argv[1:])

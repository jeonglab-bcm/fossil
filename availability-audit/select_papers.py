"""Select the open-access methodology papers to audit and write papers.csv.

Two PubMed queries, both limited to 2004-2015, research article types, and the PMC Open Access
Subset ("pubmed pmc open access"[filter]):
  mesh   - 17 core bioinformatics / biomedical informatics journals that are MEDLINE-indexed,
           restricted to papers indexed with the MeSH term Algorithms.
  tiab   - 5 core journals that were not MEDLINE-indexed in this period (no MeSH), restricted to
           papers with "algorithm*" or "method*" in the title or abstract.
Source: NCBI E-utilities esearch + esummary on db=pubmed.
"""
import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import date

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
MESH_JOURNALS = [
    "Bioinformatics", "BMC Bioinformatics", "PLoS Comput Biol", "Brief Bioinform", "Database (Oxford)",
    "J Comput Biol", "IEEE/ACM Trans Comput Biol Bioinform", "Stat Appl Genet Mol Biol", "BMC Syst Biol",
    "Pac Symp Biocomput", "J Bioinform Comput Biol", "J Am Med Inform Assoc", "J Biomed Inform",
    "BMC Med Inform Decis Mak", "Int J Med Inform", "AMIA Annu Symp Proc", "Methods Inf Med"]
TIAB_JOURNALS = ["Source Code Biol Med", "Algorithms Mol Biol", "BioData Min", "Cancer Inform",
                 "Evol Bioinform Online"]
NONRES = ('(review[pt] OR editorial[pt] OR comment[pt] OR letter[pt] OR news[pt] OR published erratum[pt]'
          ' OR retraction of publication[pt] OR retracted publication[pt] OR congress[pt] OR biography[pt])')
COMMON = f'2004:2015[dp] AND "pubmed pmc open access"[filter] NOT {NONRES}'


def journals(js):
    return "(" + " OR ".join(f'"{j}"[ta]' for j in js) + ")"


QUERIES = {
    "mesh": f"{journals(MESH_JOURNALS)} AND algorithms[mh] AND {COMMON}",
    "tiab": f"{journals(TIAB_JOURNALS)} AND (algorithm*[tiab] OR method*[tiab]) AND {COMMON}",
}


def call(tool, params):
    data = urllib.parse.urlencode({**params, "retmode": "json"}).encode()
    for attempt in range(6):
        try:
            with urllib.request.urlopen(EUTILS + tool, data=data, timeout=120) as r:
                res = json.load(r)
            time.sleep(0.4)  # stay under 3 requests/s without an API key
            return res
        except Exception as e:  # noqa: BLE001
            print(f"retry {attempt + 1}: {e}", file=sys.stderr)
            time.sleep(2 ** attempt)
    raise RuntimeError(f"failed: {tool} {params}")


def main(out="papers.csv"):
    rows = []
    for rule, q in QUERIES.items():
        ids = call("esearch.fcgi", {"db": "pubmed", "term": q, "retmax": 10000})["esearchresult"]["idlist"]
        print(rule, len(ids), file=sys.stderr)
        for i in range(0, len(ids), 200):
            res = call("esummary.fcgi", {"db": "pubmed", "id": ",".join(ids[i:i + 200])})["result"]
            for uid in res["uids"]:
                d = res[uid]
                aid = {a["idtype"]: a["value"] for a in d.get("articleids", [])}
                rows.append({"pmid": uid, "pmcid": aid.get("pmc", ""), "doi": aid.get("doi", ""),
                             "journal": d.get("source", ""), "year": d.get("pubdate", "")[:4],
                             "rule": rule, "title": d.get("title", "")})
    rows.sort(key=lambda r: (r["year"], int(r["pmid"])))
    with open(out, "w", newline="") as f:
        f.write(f"# PubMed, NCBI E-utilities, retrieved {date.today()}\n")
        for rule, q in QUERIES.items():
            f.write(f"# {rule}: {q}\n")
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "papers;", sum(not r["pmcid"] for r in rows), "without PMCID", file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:])

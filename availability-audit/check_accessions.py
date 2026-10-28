"""Check whether each distinct accession in accessions.csv still resolves in its repository.

  GEO (GSE/GSM/GPL/GDS)   NCBI E-utilities esummary on db=gds (the UID is derived from the accession)
  RefSeq, GenBank         NCBI E-utilities esearch [ACCN] on db=nuccore, then db=protein
  SRA/ENA/DDBJ            ENA Browser API summary (INSDC mirror of SRA, ENA and DDBJ)
  BioProject, dbGaP       NCBI E-utilities esearch on db=bioproject / db=gap
  ArrayExpress            EBI BioStudies API
  PDB                     RCSB holdings API (CURRENT / OBSOLETE / REMOVED / UNRELEASED)
  UniProt                 UniProt REST (entryType "Inactive" = deleted or merged)
  EGA                     EGA metadata API

Writes accession_status.csv: type, accession, status (live | obsolete | not_found | error), detail.
"not_found" for PDB IDs is often an extraction false positive (4 characters after "PDB").
"""
import csv
import re
import sys
import time

import requests

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
S = requests.Session()
S.headers["User-Agent"] = "fossil-link-audit/0.1 (+https://github.com/jeonglab-bcm/fossil)"


def get(url, params=None, pause=0.0, ok=(200, 404, 400)):
    for attempt in range(5):
        try:
            r = S.get(url, params=params, timeout=60)
            if r.status_code in ok:
                time.sleep(pause)
                return r
        except requests.RequestException:
            pass
        time.sleep(2 ** attempt)
    return None


def eutil(tool, params):
    r = get(EUTILS + tool, {**params, "retmode": "json"}, pause=0.4, ok=(200,))
    return r.json() if r is not None else None


def geo(accs):
    prefix = {"GSE": 200000000, "GPL": 100000000, "GSM": 300000000, "GDS": 0}
    out = {}
    uid_of = {a: str(prefix[a[:3]] + int(a[3:])) for a in accs}
    uids = list(uid_of.values())
    found = {}
    for i in range(0, len(uids), 200):
        res = eutil("esummary.fcgi", {"db": "gds", "id": ",".join(uids[i:i + 200])})
        if res is None:
            continue
        for uid, d in res.get("result", {}).items():
            if uid != "uids" and isinstance(d, dict) and "accession" in d:
                found[uid] = d["accession"]
    for a, uid in uid_of.items():
        out[a] = ("live", "") if found.get(uid, "").upper() == a.upper() else ("not_found", "")
    return out


def entrez_accn(accs, dbs):
    out = {}
    for a in accs:
        status = ("not_found", "")
        for db in dbs:
            res = eutil("esearch.fcgi", {"db": db, "term": f"{a}[ACCN]"})
            if res is None:
                status = ("error", db)
                break
            if int(res["esearchresult"].get("count", 0)) > 0:
                status = ("live", db)
                break
        out[a] = status
    return out


def entrez_all(accs, db):
    out = {}
    for a in accs:
        res = eutil("esearch.fcgi", {"db": db, "term": f"{a.split('.')[0]}[All Fields]"})
        out[a] = ("error", db) if res is None else (
            ("live", db) if int(res["esearchresult"].get("count", 0)) > 0 else ("not_found", db))
    return out


def ena(accs):
    out = {}
    for a in accs:
        if a[2] in "AZ":  # submissions (SRA/ERA/DRA) and analyses: the summary endpoint answers 500
            r = get(f"https://www.ebi.ac.uk/ena/browser/api/xml/{a}", pause=0.2, ok=(200, 400, 404, 500))
            live = r is not None and r.status_code == 200 and b"<ERROR" not in r.content[:2000] and len(r.content) > 200
            out[a] = ("error", "") if r is None else (("live", "xml") if live else ("not_found", str(r.status_code)))
            continue
        r = get(f"https://www.ebi.ac.uk/ena/browser/api/summary/{a}", pause=0.2, ok=(200, 400, 404, 500))
        if r is None:
            out[a] = ("error", "")
        elif r.status_code == 200 and r.json().get("summaries"):
            s = r.json()["summaries"][0]
            out[a] = ("live", s.get("dataType", "") or s.get("statusDescription", ""))
        else:
            out[a] = ("not_found", str(r.status_code))
    return out


def arrayexpress(accs):
    out = {}
    for a in accs:
        r = get(f"https://www.ebi.ac.uk/biostudies/api/v1/studies/{a}", pause=0.2)
        out[a] = ("error", "") if r is None else (("live", "") if r.status_code == 200 else ("not_found", str(r.status_code)))
    return out


def pdb(accs):
    out = {}
    for a in accs:
        r = get(f"https://data.rcsb.org/rest/v1/holdings/status/{a.upper()}", pause=0.15)
        if r is None:
            out[a] = ("error", "")
        elif r.status_code == 200:
            st = r.json().get("rcsb_repository_holdings_combined", {}).get("status", "")
            out[a] = ("live" if st == "CURRENT" else "obsolete", st)
        else:
            out[a] = ("not_found", str(r.status_code))
    return out


def uniprot(accs):
    out = {}
    for a in accs:
        r = get(f"https://rest.uniprot.org/uniprotkb/{a}.json", pause=0.2)
        if r is None:
            out[a] = ("error", "")
        elif r.status_code == 200:
            d = r.json()
            inactive = d.get("entryType") == "Inactive"
            out[a] = ("obsolete" if inactive else "live",
                      d.get("inactiveReason", {}).get("inactiveReasonType", "") if inactive else "")
        else:
            out[a] = ("not_found", str(r.status_code))
    return out


def ega(accs):
    out = {}
    for a in accs:
        kind = "studies" if a.startswith("EGAS") else "datasets"
        r = get(f"https://metadata.ega-archive.org/{kind}/{a}", pause=0.2)
        out[a] = ("error", "") if r is None else (("live", "") if r.status_code == 200 else ("not_found", str(r.status_code)))
    return out


def main():
    with open("accessions.csv") as f:
        rows = list(csv.DictReader(f))
    by_type = {}
    for r in rows:
        by_type.setdefault(r["type"], set()).add(r["accession"].strip())
    results = []
    checkers = {
        "GEO": lambda a: geo([x.upper() for x in a]),
        "RefSeq": lambda a: entrez_accn(a, ["nuccore", "protein"]),
        "GenBank": lambda a: entrez_accn(a, ["nuccore", "protein"]),
        "SRA/ENA/DDBJ": ena,
        "BioProject": lambda a: entrez_all(a, "bioproject"),
        "dbGaP": lambda a: entrez_all(a, "gap"),
        "ArrayExpress": arrayexpress,
        "PDB": pdb,
        "UniProt": uniprot,
        "EGA": ega,
    }
    for kind, accs in sorted(by_type.items(), key=lambda kv: len(kv[1])):
        accs = sorted(a for a in accs if re.fullmatch(r"[A-Za-z0-9_.\-]+", a))
        print(kind, len(accs), file=sys.stderr, flush=True)
        if kind not in checkers:
            continue
        res = checkers[kind](accs)
        for a in accs:
            st, detail = res.get(a.upper() if kind == "GEO" else a, ("error", "unchecked"))
            results.append({"type": kind, "accession": a, "status": st, "detail": detail})
    with open("accession_status.csv", "w", newline="") as f:
        w = csv.DictWriter(f, ["type", "accession", "status", "detail"])
        w.writeheader()
        w.writerows(results)


if __name__ == "__main__":
    main()

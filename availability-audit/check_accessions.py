"""Check whether each distinct accession in accessions.csv still resolves in its repository.

  GEO (GSE/GSM/GPL/GDS)   NCBI E-utilities esummary on db=gds (the UID is derived from the accession)
  RefSeq, GenBank         NCBI E-utilities esearch [ACCN] (100 per query) on db=nuccore, then db=protein;
                          esummary by accession for the rest (suppressed records are obsolete)
  SRA/ENA/DDBJ            ENA Browser API summary (INSDC mirror of SRA, ENA and DDBJ)
  BioProject, dbGaP       NCBI E-utilities esearch on db=bioproject / db=gap
  ArrayExpress            EBI BioStudies API
  PDB                     RCSB holdings API (CURRENT / OBSOLETE / REMOVED / UNRELEASED)
  UniProt                 UniProt REST (entryType "Inactive" = deleted or merged)
  EGA                     EGA metadata API

Writes accession_status.csv: type, accession, status (live | obsolete | not_found | invalid | error),
detail.
"not_found" for PDB IDs is often an extraction false positive (4 characters after "PDB").
"""
import csv
import re
import sys
import time
from pathlib import Path

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


def entrez_accn_batch(accs, dbs, chunk=100):
    """Like entrez_accn, but 100 accessions per esearch; esummary maps UIDs back to accessions."""
    out = {a: ("not_found", "") for a in accs}
    left = list(accs)
    for db in dbs:
        found = set()
        for i in range(0, len(left), chunk):
            part = left[i:i + chunk]
            # Entrez indexes only the current version of a record, so search the base accession:
            # a superseded version (NC_000022.10 for GRCh37 chr22) is still the same, live record.
            terms = sorted({a.split(".")[0] for a in part})
            res = eutil("esearch.fcgi", {"db": db, "term": " OR ".join(f"{a}[ACCN]" for a in terms), "retmax": 10000})
            if res is None:
                for a in part:
                    out[a] = ("error", db)
                continue
            ids = res["esearchresult"].get("idlist", [])
            seen = set()
            for j in range(0, len(ids), 200):
                summ = eutil("esummary.fcgi", {"db": db, "id": ",".join(ids[j:j + 200])})
                for uid, d in (summ or {}).get("result", {}).items():
                    if uid != "uids" and isinstance(d, dict):
                        seen.add(str(d.get("caption", "")).upper())
                        seen.add(str(d.get("accessionversion", "")).upper())
            for a in part:
                if a.upper() in seen or a.split(".")[0].upper() in seen:
                    out[a] = ("live", db)
                    found.add(a)
        left = [a for a in left if a not in found]
    # Records withdrawn from Entrez search (suppressed, e.g. a RefSeq transcript retired by a
    # reannotation) are still served by accession; their summary says so. Ask for those directly.
    for db in dbs:
        for i in range(0, len(left), 100):
            part = left[i:i + 100]
            summ = eutil("esummary.fcgi", {"db": db, "id": ",".join(part)}) or {}
            for uid, d in summ.get("result", {}).items():
                if uid == "uids" or not isinstance(d, dict) or d.get("error"):
                    continue
                for a in part:
                    if a.split(".")[0].upper() == str(d.get("caption", "")).upper():
                        st = str(d.get("status", "")).lower()
                        out[a] = ("live", db) if st == "live" else ("obsolete", f"{st} in {db}")
        left = [a for a in left if out[a][0] == "not_found"]
    return out


INSDC = re.compile(r"^([A-Z]{1,2}\d{5,6}|[A-Z]{3}\d{5}|[A-Z]{4,6}\d{8,10}|[A-Z]{2}_\d{6,9})(\.\d+)?$")


def genbank(accs):
    """GenBank IDs from <ext-link ext-link-type="gen">: INSDC accessions, or bare GI numbers (an
    identifier NCBI stopped displaying in 2016, still usable as a UID). Anything else (coordinate
    ranges, Ensembl or PDB IDs in the wrong markup) is recorded as invalid and not counted."""
    out = {}
    acc = [a for a in accs if INSDC.match(a)]
    out.update(entrez_accn_batch(acc, ["nuccore", "protein"]))
    for a in accs:
        if a.isdigit():
            status = ("not_found", "GI")
            for db in ("nuccore", "protein"):
                res = eutil("esummary.fcgi", {"db": db, "id": a})
                d = (res or {}).get("result", {}).get(a, {})
                if isinstance(d, dict) and d.get("caption") and not d.get("error"):
                    status = ("live", f"GI resolves in {db}")
                    break
            out[a] = status
        elif a not in out:
            out[a] = ("invalid", "not an INSDC accession")
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
    checkers = {
        "GEO": lambda a: geo([x.upper() for x in a]),
        "RefSeq": lambda a: entrez_accn_batch(a, ["nuccore", "protein"]),
        "GenBank": genbank,
        "SRA/ENA/DDBJ": ena,
        "BioProject": lambda a: entrez_all(a, "bioproject"),
        "dbGaP": lambda a: entrez_all(a, "gap"),
        "ArrayExpress": arrayexpress,
        "PDB": pdb,
        "UniProt": uniprot,
        "EGA": ega,
    }
    out = Path("accession_status.csv")
    done = set()
    if out.exists():
        with open(out) as f:
            done = {r["type"] for r in csv.DictReader(f)}
    new = not out.exists()
    # Results are appended one repository at a time, so an interrupted run resumes where it stopped.
    with open(out, "a", newline="") as f:
        w = csv.DictWriter(f, ["type", "accession", "status", "detail"])
        if new:
            w.writeheader()
        for kind, accs in sorted(by_type.items(), key=lambda kv: len(kv[1])):
            accs = sorted(a for a in accs if re.fullmatch(r"[A-Za-z0-9_.\-]+", a))
            print(kind, len(accs), "(done)" if kind in done else "", file=sys.stderr, flush=True)
            if kind not in checkers or kind in done:
                continue
            res = checkers[kind](accs)
            for a in accs:
                st, detail = res.get(a.upper() if kind == "GEO" else a, ("error", "unchecked"))
                w.writerow({"type": kind, "accession": a, "status": st, "detail": detail})
            f.flush()


if __name__ == "__main__":
    main()

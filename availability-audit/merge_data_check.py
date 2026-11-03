"""Combine the data check of the papers whose software was not found anywhere (software_new_homes.csv,
outcome "not found", or "partly found" when the paper's own models or tool are still missing) into
lost_software_data.csv.

The check was done by reading each paper: what input data its main results were computed from, and
whether that data can still be obtained (PMC supplement files opened and inspected, repository
accessions resolved, named public datasets and data links fetched). Rows come from
cache/data147/data_result_*.csv.

data_status: complete-in-pmc | complete-public | partial | results-only | not-available | no-external-data
readiness:   high (data complete and small enough to start reimplementing now) | medium | low
"""
import csv
import glob
from collections import Counter

ORDER = ["complete-in-pmc", "complete-public", "no-external-data", "partial", "results-only", "not-available"]

# Corrections found after the data check, by reading the data that later turned up.
CORRECTIONS = {
    "PMC3322362": {
        "data_needed": "RPI2241 and RPI369 RNA-protein pair benchmarks from PRIDB/PDB chains, with their negative pairs, "
                       "and 5,166 mRNA-protein pairs from Hogan et al. 2008",
        "where": "1471-2105-12-489-S2.TXT (2,241 positive pairs as PDB chain IDs); 1471-2105-12-489-S3.TXT (369 pairs); "
                 "RPI2241 positives and negatives with sequences in github.com/Dobbs-Lab/RPIMotif Data/ (commit 9cfa951)",
        "size_mb": "5.1",
        "note": "Supplements checked: tab-delimited protein_chain/RNA_chain PDB IDs (e.g. 1drz_A 1drz_B), 2,241 and 369 rows. "
                "The authors' RPIMotif repository has RPI2241 with sequences: its 2,241 positives equal S2 pair for pair, "
                "and it has 2,241 negative pairs (none overlap the positives); with them, fossil PR #12 matched the paper's "
                "RPI2241 SVM row. RPI369 negatives are not published anywhere (regenerate by the RPI2241 rule). "
                "Third dataset (Hogan et al. 2008 PLoS Biol supplement) not checked; NPInter link in paper is gone (moved).",
    },
}


def main():
    lost = {r["pmcid"]: r for r in csv.DictReader(open("software_new_homes.csv"))
            if r["outcome"] == "not found" or r["outcome"].startswith("partly found")}
    checked = {}
    for path in sorted(glob.glob("cache/data147/data_result_*.csv")):
        for r in csv.DictReader(open(path)):
            checked[r["pmcid"]] = r
    for pmcid, fix in CORRECTIONS.items():
        if pmcid in checked:
            checked[pmcid] = {**checked[pmcid], **fix}
    rows = []
    for pmcid, s in lost.items():
        c = checked.get(pmcid, {})
        rows.append({"pmcid": pmcid, "year": s["year"], "rcr": s["rcr"], "title": s["title"],
                     "data_needed": c.get("data_needed", ""), "data_status": c.get("data_status", "not checked"),
                     "where": c.get("where", ""), "size_mb": c.get("size_mb", ""), "reachable": c.get("reachable", ""),
                     "readiness": c.get("readiness", ""), "note": c.get("note", ""), "dead_software_links": s["dead_links"]})
    rank = {k: i for i, k in enumerate(ORDER)}
    ready = {"high": 0, "medium": 1, "low": 2}
    rows.sort(key=lambda r: (ready.get(r["readiness"], 3), rank.get(r["data_status"], 9), -float(r["rcr"])))
    with open("lost_software_data.csv", "w", newline="") as f:
        w = csv.DictWriter(f, list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "papers;", sum(r["data_status"] != "not checked" for r in rows), "checked")
    print(Counter(r["data_status"] for r in rows))
    print(Counter(r["readiness"] for r in rows))


if __name__ == "__main__":
    main()

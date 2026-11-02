"""Combine the data check of the papers whose software was not found anywhere (software_new_homes.csv,
outcome "not found") into lost_software_data.csv.

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


def main():
    lost = {r["pmcid"]: r for r in csv.DictReader(open("software_new_homes.csv")) if r["outcome"] == "not found"}
    checked = {}
    for path in sorted(glob.glob("cache/data147/data_result_*.csv")):
        for r in csv.DictReader(open(path)):
            checked[r["pmcid"]] = r
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

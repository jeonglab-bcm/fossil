"""Collect the SWSFS hypothesis tests (swsfs_variants.R) into one file.

usage: swsfs_summary.py VARIANT_DIR OUT_JSON [SIM_DIR]

For each forest setting (ntree500, mtry31, ntree2000), data-set group and stopping rule, the number
of SNPs selected on each data set and its median. With SIM_DIR, also checks that the ntree500
curves give the same k as the study itself (the same random numbers in the same order).
"""
import glob
import json
import os
import statistics
import sys


def main():
    vdir, out = sys.argv[1:3]
    sim_dir = sys.argv[3] if len(sys.argv) > 3 else None
    recs = []
    for f in sorted(glob.glob(os.path.join(vdir, "*.json"))):
        recs += json.load(open(f))
    groups = {}
    for r in recs:
        g = groups.setdefault((r["variant"], r["model"], r["maf"], r["r2"]), {"reps": [], "k": {}, "rank": []})
        g["reps"].append(r["rep"])
        g["rank"].append(r["rank"])
        for rule, k in r["k"].items():
            g["k"].setdefault(rule, []).append(k)
    rows = []
    for (variant, model, maf, r2), g in sorted(groups.items()):
        rows.append({"variant": variant, "model": model, "maf": maf, "r2": r2, "reps": g["reps"],
                     "disease_rank": g["rank"],
                     "k": g["k"], "median_k": {rule: statistics.median(v) for rule, v in g["k"].items()}})
    res = {"rows": rows, "curves": [{k: r[k] for k in ("variant", "model", "maf", "r2", "rep", "errors")} for r in recs]}
    if sim_dir:
        same = []
        for r in recs:
            if r["variant"] != "ntree500":
                continue
            path = os.path.join(sim_dir, f"m{r['model']}_maf{r['maf']:g}_r{r['r2']:g}.json")
            if os.path.exists(path):
                study = next((s for s in json.load(open(path)) if s["rep"] == r["rep"]), None)
                if study:
                    same.append(study["ef"]["k"] == r["k"]["paper"])
        res["ntree500_same_k_as_study"] = f"{sum(same)} of {len(same)}"
    with open(out, "w") as fh:
        json.dump(res, fh, indent=1)
    for row in rows:
        print(row["variant"], row["model"], row["maf"], row["r2"], row["k"])


if __name__ == "__main__":
    main()

"""Collect the first-forest hypothesis tests (rank_variants.R) into one file.

usage: rank_summary.py VARIANT_DIR OUT_JSON SIM_DIR

For each setting and forest setting: the share of data sets whose two disease markers both rank
within the top 46 (the published median number of SNPs SWSFS keeps), so they could be candidates
even under the paper's larger selections, and the median rank of the lower-ranked marker. Also
checks that the study's own setting (factor_ntree500) gives the study's ranks.
"""
import glob
import json
import os
import statistics
import sys

TOP = 46


def main():
    vdir, out, sim_dir = sys.argv[1:4]
    recs = []
    for f in sorted(glob.glob(os.path.join(vdir, "*.json"))):
        recs += json.load(open(f))
    groups, same = {}, []
    for r in recs:
        g = groups.setdefault((r["model"], r["maf"], r["r2"]), {"reps": [], "rank": {}})
        g["reps"].append(r["rep"])
        for v, rk in r["rank"].items():
            g["rank"].setdefault(v, []).append(rk)
        path = os.path.join(sim_dir, f"m{r['model']}_maf{r['maf']:g}_r{r['r2']:g}.json")
        study = next((s for s in json.load(open(path)) if s["rep"] == r["rep"]), None)
        if study:
            same.append(study["ef"]["rank"] == r["rank"]["factor_ntree500"])
    rows = []
    for (model, maf, r2), g in sorted(groups.items()):
        row = {"model": model, "maf": maf, "r2": r2, "reps": sorted(g["reps"]), "variants": {}}
        for v, rks in g["rank"].items():
            row["variants"][v] = {"both_in_top46": sum(max(x) <= TOP for x in rks), "of": len(rks),
                                  "median_lower_rank": statistics.median(max(x) for x in rks)}
        rows.append(row)
        print(model, maf, r2, {v: (s["both_in_top46"], s["median_lower_rank"]) for v, s in row["variants"].items()})
    res = {"rows": rows, "records": recs, "study_setting_same_ranks": f"{sum(same)} of {len(same)}"}
    with open(out, "w") as fh:
        json.dump(res, fh, indent=1)
    print("study setting gives the study's ranks:", res["study_setting_same_ranks"])


if __name__ == "__main__":
    main()

"""Compare data sets rerun from scratch with the committed chunk of the simulation.

usage: sim_check.py FRESH_PREFIX COMMITTED_PREFIX OUT_JSON
Reads FRESH_PREFIX_sums.csv / _post.csv and the committed ones; every number must agree to 1e-9
relative (the same code and seeds; only platform arithmetic may differ).
"""
import csv
import json
import math
import sys


def rows(path):
    with open(path) as fh:
        return list(csv.DictReader(fh))


def close(a, b):
    try:
        x, y = float(a), float(b)
    except ValueError:
        return a == b
    return abs(x - y) <= 1e-12 + 1e-9 * abs(y) or (math.isnan(x) and math.isnan(y))


fresh, committed, out = sys.argv[1:4]
report = {"data_sets": "1-50, noise SD 0.1", "files": [], "passed": True}
for suffix in ("_sums.csv", "_post.csv"):
    a, b = rows(fresh + suffix), rows(committed + suffix)
    diffs = []
    if len(a) != len(b):
        diffs.append(f"{len(a)} rows against {len(b)} committed")
    for i, (ra, rb) in enumerate(zip(a, b)):
        for k in rb:
            if not close(ra.get(k), rb[k]):
                diffs.append(f"row {i + 2} {k}: {ra.get(k)} against {rb[k]}")
    report["files"].append({"file": "chunk00" + suffix, "rows": len(b), "differences": diffs[:20],
                            "n_differences": len(diffs)})
    report["passed"] &= not diffs
json.dump(report, open(out, "w"), indent=1)
print("sim check:", "same as committed" if report["passed"] else "DIFFERS")

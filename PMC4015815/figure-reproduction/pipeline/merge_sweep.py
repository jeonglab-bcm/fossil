"""Merge a fresh sweep with the committed one: fresh rows win; dMAX values not run are copied from
the committed file, so every figure always has all ten points. Which dMAX values were copied is
printed (and the check step compares the fresh rows with the committed ones cell for cell).

usage: merge_sweep.py FRESH_CSV COMMITTED_CSV OUT_CSV
"""
import csv
import os
import sys

KEYS = ["dmax", "seed", "clip", "family", "roc", "roc50", "n_train", "n_pos_train", "n_test",
        "n_pos_test", "iterations", "support_vectors"]


def main(fresh, committed, out):
    rows = list(csv.DictReader(open(fresh)))
    have = {r["dmax"] for r in rows}
    copied = set()
    if os.path.exists(committed):
        for r in csv.DictReader(open(committed)):
            if r["dmax"] not in have:
                copied.add(r["dmax"])
                rows.append(r)
    rows.sort(key=lambda r: (int(r["dmax"]), r["family"]))
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=KEYS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"{out}: dMAX run here {sorted(have, key=int)}; copied from {committed}: "
          f"{sorted(copied, key=int) or 'none'}")


if __name__ == "__main__":
    main(*sys.argv[1:4])

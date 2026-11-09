"""Merge a fresh sweep with the committed one: fresh rows win; dMAX values not run are copied from
the committed file, so every figure always has all ten points. Which dMAX values were copied is
printed. It refuses (exit 1) when the copied rows differ from the fresh ones in seed, clip rule
or input (the fingerprint of the sequences trained on), so a run never mixes two setups.

usage: merge_sweep.py FRESH_CSV COMMITTED_CSV OUT_CSV
"""
import csv
import os
import sys

KEYS = ["dmax", "seed", "clip", "input", "family", "roc", "roc50", "n_train", "n_pos_train", "n_test",
        "n_pos_test", "iterations", "support_vectors"]


def main(fresh, committed, out):
    rows = list(csv.DictReader(open(fresh)))
    have = {r["dmax"] for r in rows}
    copied = set()
    if os.path.exists(committed):
        old = list(csv.DictReader(open(committed)))
        # Copied rows must come from the same setup as the fresh ones.
        for key in ("seed", "clip", "input"):
            new_vals = {r[key] for r in rows}
            old_vals = {r[key] for r in old if r["dmax"] not in have}
            if old_vals and old_vals != new_vals:
                sys.exit(f"merge_sweep.py: {key} differs between this run {sorted(new_vals)} and "
                         f"the committed rows {sorted(old_vals)} in {committed}; rerun all dMAX "
                         f"values or match the {key}")
        for r in old:
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

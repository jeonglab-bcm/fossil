"""Hypothesis tests for the RF1 bars of Fig. 1 at no LD (n0), where the paper's RF1 importances are
about 10% above RF0 although RF1 can exclude nothing when no SNPs are in LD (R = 0.5).

  rf1_variants.py OUT.json [--reps 30]

On the first replicates of the n0 and r4 data sets (incremental design), compare RF0 with:
  RF1 at R = 0.5 (ours), RF1 at R = 0.02 (a threshold low enough to drop noise SNPs correlated by
  chance), and RF1 with self-exclusion (every variable splits at most one node per tree).
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from snp_study import seeds  # noqa: E402
from rfld.forest import grow_forest, r2_matrix  # noqa: E402
from rfld.simulate import MODELS, snp_dataset  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("--reps", type=int, default=30)
a = ap.parse_args()
res = {}
for ld in ("n0", "r4"):
    rows = []
    for rep in range(a.reps):
        dseed, fseed = seeds(ld, rep)
        X, y, kinds = snp_dataset(np.random.default_rng(dseed), MODELS["H4M4"], ld)
        r2 = r2_matrix(X)
        row = {}
        for name, kw in [("RF0", {}), ("RF1_R0.5", dict(revised_tree=True, ld_threshold=0.5)),
                         ("RF1_R0.02", dict(revised_tree=True, ld_threshold=0.02)),
                         ("RF1_R0.5_drop_self", dict(revised_tree=True, ld_threshold=0.5, drop_self=True))]:
            f = grow_forest(X, y, seed=fseed, r2=r2, **kw)
            row[name] = {"im0": float(f["im0"][:4].mean()), "im1": float(f["im1"][:4].mean())}
        rows.append(row)
        print(ld, rep, {k: round(v["im0"], 3) for k, v in row.items()}, flush=True)
    summ = {}
    for name in rows[0]:
        for imk in ("im0", "im1"):
            d = np.array([r[name][imk] / r["RF0"][imk] for r in rows])
            summ[f"{name}/RF0 {imk}"] = {"mean_ratio": float(d.mean()), "se": float(d.std(ddof=1) / np.sqrt(len(d)))}
    res[ld] = {"reps": a.reps, "ratio_to_RF0": summ}
json.dump(res, open(a.out, "w"), indent=1)
print(json.dumps(res, indent=1))

"""Hypothesis tests for the haplotype figures (Figs 4-6), where the published true and predicted
haplotypes do much worse at low r^2 than ours.

  hap_variants.py OUT.json [--reps 30]

On the first replicates of the haplotype study (same data as the committed run, empirical-ratio
rule) at r^2 = 0, 0.5 and 1, grow the HAP forest (5000 trees) with the haplo-genotype
  categorical  (ours: any subset of its 10 codes can go left),
  ordered      (split at thresholds of the code, as Random Forests 5.1 splits a numeric variable;
                codes in our order: pairs (a, b), a <= b, of T-C, G-T, T-T, G-C), and
  ordered, shuffled codes (a fixed random order of the 10 codes),
and report the mean IM of the risk haplotypes and the share of replicates with all of them above
every noise SNP (Figs 4 and 5).
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hap_study import seeds  # noqa: E402
from rfld.forest import grow_forest  # noqa: E402
from rfld.simulate import MODELS, haplo_genotype_code, haplotype_dataset, haplotype_frequencies  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("--reps", type=int, default=30)
ap.add_argument("--r2", type=float, nargs="*", default=[0.0, 0.5, 1.0])
a = ap.parse_args()
shuffle = np.random.default_rng(2666661).permutation(10)
res = {"reps": a.reps, "shuffled_order": shuffle.tolist(), "levels": {}}
for r2 in a.r2:
    rows = []
    for rep in range(a.reps):
        dseed, fseed, _ = seeds(round(r2, 1), rep, "empirical_ratio")
        d = haplotype_dataset(np.random.default_rng(dseed), MODELS["H4M4"], haplotype_frequencies(r2, "empirical_ratio"))
        k = d["haps"].shape[1]
        h = haplo_genotype_code(d["haps"])
        ncat = np.r_[np.full(k, 10), np.full(d["noise"].shape[1], 3)]
        row = {}
        for name, codes, ordered in [("categorical", h, False), ("ordered", h, True),
                                     ("ordered_shuffled", shuffle[h], True)]:
            X = np.c_[codes, d["noise"]]
            o = np.r_[np.full(k, ordered), np.zeros(d["noise"].shape[1], bool)]
            f = grow_forest(X, d["y"], ntree=5000, mtry=35, seed=fseed + 1, ncat=ncat, ordered=o)
            im = f["im0"]
            row[name] = {"m": float(im[:k].mean()), "a": int(im[:k].min() > im[k:].max())}
        rows.append(row)
        print(r2, rep, {n: round(v["m"], 3) for n, v in row.items()}, flush=True)
    res["levels"][f"{r2:.1f}"] = {n: {"mean_im": float(np.mean([r[n]["m"] for r in rows])),
                                      "above_noise": float(np.mean([r[n]["a"] for r in rows]))}
                                  for n in rows[0]}
json.dump(res, open(a.out, "w"), indent=1)
print(json.dumps(res["levels"], indent=1))

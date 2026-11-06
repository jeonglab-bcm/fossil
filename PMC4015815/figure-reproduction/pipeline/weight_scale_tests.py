"""Hypothesis tests for the amplitude of Figures 4 and 5 (family 2.5.1.3).

usage: weight_scale_tests.py --fasta F --membership M --sequences residues|top1:FILE
                             --fig4 fig4_scores.json --fig5 fig5_published.json --panel B|A
                             --out OUT.json

Our discriminant weights come out about 1.3 times the published ones (Figure 4's colour-bar
maximum, Figure 5's bars). Each variant changes one thing and reports the L2 maximum, the
Spearman correlation with the published heatmap, and the least-squares scale of the published
(G,G) and (L,L) bars on ours (x = d + 1):
  seeds 2 and 3 (Gist seeds from the clock), Gist's clip rule instead of the cap, convergence
  threshold 1e-5 (Gist's help text) instead of 1e-6 (its code), and weights before rounding to
  4 significant digits.
"""
import argparse
import json

import numpy as np
from scipy import stats

import features
import gist_port
import run_sweep


def summary(X, alpha, dmax, pub_heat, pub_bars, A):
    W = alpha @ X
    comp = W[:20]
    pairs = W[20:].reshape(dmax, 20, 20)
    l2 = np.sqrt((pairs ** 2).sum(axis=0))
    for i in range(20):
        l2[i, i] = np.sqrt(l2[i, i] ** 2 + comp[i] ** 2)
    out = {"l2_max": round(float(l2.max()), 2),
           "spearman_heatmap": round(float(stats.spearmanr(l2.ravel(), pub_heat.ravel())[0]), 4)}
    for p, panel in (("G", pub_bars[0]), ("L", pub_bars[1])):
        i = A.index(p)
        ours = np.concatenate([[comp[i]], pairs[:, i, i]])
        pv = np.array(panel)
        a, b = pv[2:150], ours[1:149]
        out[f"scale_{p}{p}"] = round(float(np.dot(a, b) / np.dot(b, b)), 4)
        out[f"r_{p}{p}"] = round(float(np.corrcoef(a, b)[0, 1]), 4)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fasta", required=True)
    ap.add_argument("--membership", required=True)
    ap.add_argument("--sequences", default="residues")
    ap.add_argument("--fig4", required=True)
    ap.add_argument("--fig5", required=True)
    ap.add_argument("--panel", default="B")
    ap.add_argument("--family", default="2.5.1.3")
    ap.add_argument("--dmax", type=int, default=150)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    names, seqs, families, codes = features.load_benchmark(a.fasta, a.membership)
    seqs = run_sweep.load_sequences(a.sequences, names, seqs)
    j = families.index(a.family)
    c = codes[:, j]
    train = np.flatnonzero((c == 1) | (c == 2))
    X = features.feature_vectors([features.encode(seqs[i]) for i in train], a.dmax)
    K = X @ X.T
    pos = c[train] == 1
    f4 = json.load(open(a.fig4))
    pub_heat = np.array(f4["panels"][a.panel]["published_values"])
    pub_max = f4["panels"][a.panel]["published_max"]
    f5 = json.load(open(a.fig5))
    bars = ("A", "B") if a.panel == "A" else ("C", "D")
    pub_bars = [f5[b]["values"] for b in bars]
    A = features.ALPHABET
    variants = {
        "ours (seed 1, cap, threshold 1e-6, printed weights)": dict(seed=1),
        "seed 2": dict(seed=2),
        "seed 3": dict(seed=3),
        "Gist's clip rule (0 off the diagonal)": dict(seed=1, clip=gist_port.CLIP_GIST),
        "threshold 1e-5": dict(seed=1, threshold=1e-5),
    }
    res = {"family": a.family, "sequences": a.sequences, "published_l2_max": pub_max,
           "variants": {}}
    base_w = None
    for name, kw in variants.items():
        w, info = gist_port.train(K, pos, **kw)
        if base_w is None:
            base_w = w
        res["variants"][name] = {**summary(X, gist_port.printed(w), a.dmax, pub_heat, pub_bars, A),
                                 "support_vectors": info["support_vectors"]}
        print(name, res["variants"][name], flush=True)
    res["variants"]["weights before rounding"] = summary(X, base_w, a.dmax, pub_heat, pub_bars, A)
    json.dump(res, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()

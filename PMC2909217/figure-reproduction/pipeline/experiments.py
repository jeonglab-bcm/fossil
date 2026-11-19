"""The cross-validation experiments behind Figs 2-5.

    python experiments.py FEATURES.npz OUT.json [--repeats 5] [--jobs 4]

For each repeat (seed = repeat number): draw 1,500 SGI and 1,500 non-SGI pairs, split each class
into n folds, and run
  - 20% unlabelled (Fig. 2): 5 folds, train on 4, test on 1;
  - 50% unlabelled (Figs 3 and 5): 2 folds, train on 1, test on the other;
  - 80% unlabelled (Fig. 4): 5 folds, train on 1, test on the other 4.
SSL (label spreading, all 3,000 points in the graph, test labels hidden, sigma chosen on the
training labels only) and SVM (RBF, grid search
on the training folds) on the weighted-network features; SSL also on the binary-network features at
50% (Fig. 5). Test scores are pooled over the folds of a repeat; the five repeats are averaged at 26
score quantiles (threshold averaging), which also gives the markers of the drawn curves.
"""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from fgnssl import classify as K, ssl

N_PER_CLASS = 1500
SETTINGS = {"unlabelled20": (5, "train_rest"), "unlabelled50": (2, "train_rest"), "unlabelled80": (5, "train_one")}
QUANTILES = np.linspace(0.0, 1.0, 26)
FPR_GRID = np.round(np.linspace(0.0, 1.0, 101), 2)


def folds(rng, n_pos, n_neg, k):
    fp = np.array_split(rng.permutation(n_pos), k)
    fn = np.array_split(rng.permutation(n_neg) + n_pos, k)
    return [np.r_[a, b] for a, b in zip(fp, fn)]


def run_repeat(args):
    path, r = args
    d = np.load(path)
    y = d["y"]
    rng = np.random.default_rng(r)
    pos = rng.choice(np.where(y == 1)[0], N_PER_CLASS, replace=False)
    neg = rng.choice(np.where(y == 0)[0], N_PER_CLASS, replace=False)
    idx = np.r_[pos, neg]
    lab = y[idx].astype(int)
    feats = {net: K.scale_features(d[f"X_{net}"][idx]) for net in ("weighted", "binary")}
    out = {}
    for setting, (k, mode) in SETTINGS.items():
        parts = folds(rng, N_PER_CLASS, N_PER_CLASS, k)
        runs = [("ssl", "weighted"), ("svm", "weighted")]
        if setting == "unlabelled50":
            runs.append(("ssl", "binary"))
        for method, net in runs:
            F = feats[net]
            scores, labels, params = [], [], []
            for f in range(k):
                if mode == "train_rest":
                    test = parts[f]
                    train = np.concatenate([parts[g] for g in range(k) if g != f])
                else:
                    train = parts[f]
                    test = np.concatenate([parts[g] for g in range(k) if g != f])
                if method == "ssl":
                    yy = lab.copy()
                    yy[test] = -1
                    sigma = ssl.select_sigma(F, yy, seed=r)
                    s = ssl.label_spreading(F, yy, sigma=sigma)[test]
                    params.append({"sigma": sigma})
                else:
                    s, C, gamma = K.svm_scores(F[train], lab[train], F[test], seed=r)
                    params.append({"C": C, "gamma": gamma})
                scores.append(s)
                labels.append(lab[test])
            s = np.concatenate(scores)
            l = np.concatenate(labels)
            # put fold scores on one scale before pooling: rank within each fold
            ranks = [np.argsort(np.argsort(x, kind="mergesort"), kind="mergesort") / max(len(x) - 1, 1) for x in scores]
            s = np.concatenate(ranks)
            fpr, tpr = K.roc_curve(s, l)
            thr = np.quantile(s, 1.0 - QUANTILES)
            pts = [[float(np.mean(s[l == 0] >= t)), float(np.mean(s[l == 1] >= t))] for t in thr]
            out[f"{setting}/{method}/{net}"] = {
                "auc": K.auc(fpr, tpr),
                "tpr_at_fpr": [K.tpr_at(fpr, tpr, x) for x in FPR_GRID],
                "points": pts,
                "params": params,
            }
    return r, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("features")
    ap.add_argument("out")
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    with ProcessPoolExecutor(a.jobs) as ex:
        res = dict(ex.map(run_repeat, [(a.features, r) for r in range(a.repeats)]))
    keys = sorted(res[0])
    summary = {"fpr_grid": FPR_GRID.tolist(), "quantiles": QUANTILES.tolist(), "repeats": a.repeats,
               "n_per_class": N_PER_CLASS, "curves": {}}
    for key in keys:
        per = [res[r][key] for r in range(a.repeats)]
        pts = np.mean([p["points"] for p in per], axis=0)
        pts[0] = [0.0, 0.0]
        pts[-1] = [1.0, 1.0]
        tpr = np.mean([p["tpr_at_fpr"] for p in per], axis=0)
        summary["curves"][key] = {
            "auc_mean": round(float(np.mean([p["auc"] for p in per])), 6),
            "auc_repeats": [round(p["auc"], 6) for p in per],
            "tpr_at_fpr_mean": [round(float(v), 6) for v in tpr],
            "points": [[round(float(x), 6), round(float(v), 6)] for x, v in pts],
            "params": [p["params"] for p in per],
        }
    with open(a.out, "w") as f:
        json.dump(summary, f, indent=1)
    for key in keys:
        c = summary["curves"][key]
        print(f"{key:32s} AUC {c['auc_mean']:.3f}  TPR at FPR 0.09: {c['tpr_at_fpr_mean'][9]:.3f}")


if __name__ == "__main__":
    main()

"""Hypothesis tests for the gap between our ROC curves and the paper's (one input changed at a time).

    python hypotheses.py INPUTS FEATURES.npz OUT.json [JOBS]

All on the first repeat's 1,500 + 1,500 pairs at 50% unlabelled (2 folds), the setting of Fig. 3,
scored by the pooled area under the ROC curve and the TPR at FPR 0.09:

  baseline           our pipeline as in experiments.py
  random_negatives   non-SGI pairs drawn from all gene pairs of the network, not from tested pairs
  ppi_all            every physical interaction in the release (except Gavin and Ho) as the PPI part
  inverse_weights    1 / W of eq. 2 as the tie strength (W read as a distance)
  no_log             features z-scored without the log transform
  median_sigma       SSL with sigma = the median distance (no selection on the training labels)
  alpha_0.5          SSL with alpha = 0.5
  gene_identity      SVM and SSL on one-hot gene identity (which genes form the pair), no network
  weight_scale       Fig. 6 scale: median edge weight and the 99th percentile of the SGI pairs'
                     weighted-degree difference, with expression as is and standardized per gene
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from fgnssl import classify as K, fgn, network as N, ssl


def evaluate(F, lab, seed, scale=True, sigma_mode="select", alpha=ssl.ALPHA_DEFAULT):
    rng = np.random.default_rng(seed + 1000)
    n = len(lab) // 2
    parts = [np.r_[a, b] for a, b in zip(np.array_split(rng.permutation(n), 2),
                                           np.array_split(rng.permutation(n) + n, 2))]
    X = K.scale_features(F) if scale else (F - F.mean(0)) / np.where(F.std(0) == 0, 1, F.std(0))
    out = {}
    for method in ("ssl", "svm"):
        scores, labels = [], []
        for f in range(2):
            test, train = parts[f], parts[1 - f]
            if method == "ssl":
                yy = lab.copy()
                yy[test] = -1
                sig = ssl.select_sigma(X, yy, seed=seed, alpha=alpha) if sigma_mode == "select" else None
                s = ssl.label_spreading(X, yy, sigma=sig, alpha=alpha)[test]
            else:
                s, _, _ = K.svm_scores(X[train], lab[train], X[test], seed=seed)
            scores.append(np.argsort(np.argsort(s, kind="mergesort"), kind="mergesort") / (len(s) - 1))
            labels.append(lab[test])
        fpr, tpr = K.roc_curve(np.concatenate(scores), np.concatenate(labels))
        out[method] = {"auc": round(K.auc(fpr, tpr), 4), "tpr_at_0.09": round(K.tpr_at(fpr, tpr, 0.09), 4)}
    return out


def network_features(n, E, w, pairs, weighted=True):
    g = N.make_graph(n, E, w if weighted else None)
    props = N.node_properties(g, weighted)
    return N.pair_features(g, props, pairs, weighted)


def _setup(inputs, features):
    ind = Path(inputs)
    d = np.load(features)
    y = d["y"]
    rng = np.random.default_rng(0)
    pos = rng.choice(np.where(y == 1)[0], 1500, replace=False)
    neg = rng.choice(np.where(y == 0)[0], 1500, replace=False)
    idx = np.r_[pos, neg]
    return ind, d, y, idx, y[idx].astype(int), d["pairs"][idx]


def variant(args):
    name, inputs, features = args
    ind, d, y, idx, lab, pairs = _setup(inputs, features)
    X = np.load(ind / "expression.npy")
    n = X.shape[0]
    cpx = np.loadtxt(ind / "complex_edges.tsv", dtype=np.int64, ndmin=2)
    E = np.unique(np.sort(np.vstack([np.loadtxt(ind / "ppi_edges.tsv", dtype=np.int64, ndmin=2), cpx]), axis=1), axis=0)
    w = d["edge_weights"]
    if name == "baseline":
        return name, evaluate(d["X_weighted"][idx], lab, 0)
    if name == "random_negatives":
        nodes = np.unique(E)
        sgi = {tuple(sorted(map(int, p))) for p in d["pairs"][y == 1]}
        r2 = np.random.default_rng(7)
        rp = []
        while len(rp) < 1500:
            a, b = r2.choice(nodes, 2, replace=False)
            if tuple(sorted((int(a), int(b)))) not in sgi:
                rp.append((int(a), int(b)))
        return name, evaluate(network_features(n, E, w, np.vstack([pairs[:1500], np.array(rp)])), lab, 0)
    if name == "ppi_all":
        Ea = np.unique(np.sort(np.vstack([np.loadtxt(ind / "ppi_edges_all.tsv", dtype=np.int64, ndmin=2), cpx]), axis=1), axis=0)
        wa = fgn.edge_weights(X, d["clusters"], Ea)
        return name, evaluate(network_features(n, Ea, wa, pairs), lab, 0)
    if name == "inverse_weights":
        return name, evaluate(network_features(n, E, 1.0 / w, pairs), lab, 0)
    if name == "no_log":
        return name, evaluate(d["X_weighted"][idx], lab, 0, scale=False)
    if name == "median_sigma":
        return name, evaluate(d["X_weighted"][idx], lab, 0, sigma_mode="median")
    if name == "alpha_0.5":
        return name, evaluate(d["X_weighted"][idx], lab, 0, alpha=0.5)
    if name == "weight_scale":
        from scipy.stats import ks_2samp
        out = {}
        allp = d["pairs"]
        for label, M in (("as_is", X), ("gene_standardized",
                         (X - X.mean(1, keepdims=True)) / np.where(X.std(1, keepdims=True) == 0, 1, X.std(1, keepdims=True)))):
            lab_ = fgn.dcca(M)
            ww = fgn.edge_weights(M, lab_, E)
            st = np.zeros(n)
            np.add.at(st, E[:, 0], ww)
            np.add.at(st, E[:, 1], ww)
            dd = np.abs(st[allp[:, 0]] - st[allp[:, 1]])
            out[label] = {"median_weight": round(float(np.median(ww)), 3),
                          "sgi_degree_diff_p99": round(float(np.percentile(dd[y == 1], 99)), 1),
                          "ks_D": round(float(ks_2samp(dd[y == 1], dd[y == 0]).statistic), 4)}
        return name, out
    if name == "gene_identity":
        genes = np.unique(pairs)
        pos_of = {g: i for i, g in enumerate(genes)}
        G = np.zeros((len(pairs), len(genes)))
        for k, (a, b) in enumerate(pairs):
            G[k, pos_of[a]] = 1
            G[k, pos_of[b]] = 1
        return name, evaluate(G, lab, 0, scale=False)
    raise KeyError(name)


VARIANTS = ("baseline", "random_negatives", "ppi_all", "inverse_weights", "no_log", "median_sigma",
            "alpha_0.5", "gene_identity", "weight_scale")


def main(inputs: str, features: str, out: str, jobs: str = "4") -> None:
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(int(jobs)) as ex:
        res = dict(ex.map(variant, [(v, inputs, features) for v in VARIANTS]))
    for k in VARIANTS:
        print(k, res[k], flush=True)
    Path(out).write_text(json.dumps({k: res[k] for k in VARIANTS}, indent=1) + "\n")


if __name__ == "__main__":
    main(*sys.argv[1:5])

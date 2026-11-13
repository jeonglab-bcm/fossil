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
  genetic_other      our network plus the genetic interactions of other papers (BioGRID's genetic rows,
                     Tong 2004 excluded): many Tong SGI pairs are reported again there, so labels
                     become edges
  genetic_other_no_tong_pairs   the same with every Tong SGI pair removed from the added edges
  genetic_all        our network plus every genetic interaction, Tong 2004 included
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
    if name.startswith("genetic_"):
        genes = list(d["genes"])
        idx = {g: i for i, g in enumerate(genes)}
        add = [tuple(l.split("\t")) for l in (ind / "genetic_other.tsv").read_text().splitlines() if l]
        if name == "genetic_all":
            add += [tuple(l.split("\t")) for l in (ind / "sgi_pairs.tsv").read_text().splitlines() if l]
        if name == "genetic_other_no_tong_pairs":
            tong = {frozenset(l.split("\t")) for l in (ind / "sgi_pairs.tsv").read_text().splitlines() if l}
            add = [e for e in add if frozenset(e) not in tong]
        for a, b in add:
            for g in (a, b):
                if g not in idx:
                    idx[g] = len(genes)
                    genes.append(g)
        Xe = np.vstack([X, np.repeat(X.mean(0, keepdims=True), len(genes) - n, axis=0)])
        Ee = np.unique(np.sort(np.vstack([E, np.array([(idx[a], idx[b]) for a, b in add if a != b])]), axis=1), axis=0)
        lab_ = fgn.dcca(Xe)
        we = fgn.edge_weights(Xe, lab_, Ee)
        F = network_features(len(genes), Ee, we, pairs)
        out = evaluate(F, lab, 0)
        out["edges"] = int(len(Ee))
        out["genes"] = int(len(np.unique(Ee)))
        added = {frozenset(e) for e in add}
        out["sample_sgi_pairs_that_are_edges"] = int(sum(frozenset((genes[a], genes[b])) in added for a, b in pairs[lab == 1]))
        out["sample_nonsgi_pairs_that_are_edges"] = int(sum(frozenset((genes[a], genes[b])) in added for a, b in pairs[lab == 0]))
        return name, out
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
        out = evaluate(G, lab, 0, scale=False)
        # how much of a test pair the training pairs already show: the share of test pairs whose two
        # genes both occur in training pairs, for the 2-fold split evaluate() uses
        rng = np.random.default_rng(1000)
        m = len(lab) // 2
        parts = [np.r_[a, b] for a, b in zip(np.array_split(rng.permutation(m), 2), np.array_split(rng.permutation(m) + m, 2))]
        seen = set(pairs[parts[1]].ravel().tolist())
        test = pairs[parts[0]]
        out["test_pairs_with_both_genes_in_training"] = round(float(np.mean([a in seen and b in seen for a, b in test])), 4)
        out["test_pairs_with_one_gene_in_training"] = round(float(np.mean([(a in seen) or (b in seen) for a, b in test])), 4)
        return name, out
    raise KeyError(name)


VARIANTS = ("baseline", "random_negatives", "ppi_all", "inverse_weights", "no_log", "median_sigma",
            "alpha_0.5", "gene_identity", "genetic_other", "genetic_other_no_tong_pairs", "genetic_all",
            "weight_scale")


def main(inputs: str, features: str, out: str, jobs: str = "4") -> None:
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(int(jobs)) as ex:
        res = dict(ex.map(variant, [(v, inputs, features) for v in VARIANTS]))
    for k in VARIANTS:
        print(k, res[k], flush=True)
    Path(out).write_text(json.dumps({k: res[k] for k in VARIANTS}, indent=1) + "\n")


if __name__ == "__main__":
    main(*sys.argv[1:5])

"""The paper's experiments on one set of PSSMs, with the pssmdt package.

Usage:
  experiments.py benchmark PSSMS.npz OUTDIR [--jobs N]   Tables 1 and 2, Figs 3 and 4 (jackknife)
  experiments.py lg        PSSMS.npz OUTDIR [--jobs N]   Fig. 1 (5-fold CV for LG = 1..14)
  experiments.py independent PSSMS.npz FILTER.tsv BENCH.json OUTDIR   Table 4, Fig. 5
  experiments.py weights   PSSMS.npz BENCH.json OUTDIR   Fig. 2 (discriminant weights)

Every step chooses C and gamma by 5-fold cross-validated accuracy over LIBSVM's default grid
(log2 C = -5, -3, ..., 15; log2 gamma = 3, 1, ..., -15) after scaling each feature to [-1, 1]
on the benchmark, then runs the jackknife with those values.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed

import pssmdt
from pssmdt.svm import LOG2C, LOG2G, cv_decision, rbf, sq_dists

ENCODINGS = ["PSSM-DT", "PSSM-SDT", "PSSM-DDT", "AvePscore-20", "AvePscore-400", "Pscore-100", "ACC"]
LG = 5
SEED = 0


def load(npz):
    z = np.load(npz)
    offs = np.concatenate([[0], np.cumsum(z["length"])])
    pssms = [z["scores"][offs[i]:offs[i + 1]].astype(np.int64) for i in range(len(z["id"]))]
    return {"set": z["set"], "id": z["id"], "label": z["label"], "sequence": z["sequence"], "pssm": pssms}


def subset(D, name, keep=None):
    idx = [i for i, s in enumerate(D["set"]) if s == name and (keep is None or D["id"][i] in keep)]
    return idx


def features(D, idx, encoding, lg=LG):
    return np.array([pssmdt.encode(D["pssm"][i], str(D["sequence"][i]), encoding, lg) for i in idx])


def _cv_acc(D2, y, c, g, seed):
    dec = cv_decision(rbf(D2, 2.0 ** g), y, 2.0 ** c, 5, seed)
    return c, g, dec


def grid(X, y, jobs, seed=SEED):
    """Grid search in parallel; same result as pssmdt.grid_search (ties to the first in grid order)."""
    D2 = sq_dists(X)
    res = Parallel(n_jobs=jobs)(delayed(_cv_acc)(D2, y, c, g, seed) for c in LOG2C for g in LOG2G)
    table = []
    best = None
    for c, g, dec in res:
        a = float(np.mean((dec > 0) == (y > 0)))
        table.append([c, g, round(a, 6)])
        if best is None or a > best[2] + 1e-12:
            best = (c, g, a, dec)
    return {"log2C": best[0], "log2gamma": best[1], "cv_accuracy": best[2], "grid": table}, best[3]


def _loo_one(K, y, C, i):
    tr = np.delete(np.arange(len(y)), i)
    from sklearn.svm import SVC
    m = SVC(C=C, kernel="precomputed", tol=1e-3).fit(K[np.ix_(tr, tr)], y[tr])
    return float(m.decision_function(K[i:i + 1, tr])[0])


def jackknife(X, y, C, gamma, jobs):
    K = rbf(sq_dists(X), gamma)
    return np.array(Parallel(n_jobs=jobs, batch_size=16)(delayed(_loo_one)(K, y, C, i) for i in range(len(y))))


def rounded(m):
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in m.items()}


def cmd_benchmark(a):
    D = load(a.pssms)
    out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
    idx = subset(D, "benchmark")
    y = D["label"][idx]
    res = {"n": len(idx), "positives": int(y.sum()), "encodings": {}}
    decisions = {"id": [str(D["id"][i]) for i in idx], "label": y.tolist()}
    for enc in ENCODINGS:
        X = pssmdt.scale(features(D, idx, enc))
        g, _ = grid(X, y, a.jobs)
        dec = jackknife(X, y, 2.0 ** g["log2C"], 2.0 ** g["log2gamma"], a.jobs)
        res["encodings"][enc] = {"dimension": X.shape[1], **{k: g[k] for k in ("log2C", "log2gamma", "cv_accuracy")},
                                 "jackknife": rounded(pssmdt.metrics(y, dec)), "grid": g["grid"]}
        decisions[enc] = [round(float(v), 6) for v in dec]
        print(enc, res["encodings"][enc]["jackknife"], flush=True)
    (out / "benchmark.json").write_text(json.dumps(res, indent=1) + "\n")
    (out / "benchmark_decisions.json").write_text(json.dumps(decisions) + "\n")


def cmd_lg(a):
    D = load(a.pssms)
    out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
    idx = subset(D, "benchmark")
    y = D["label"][idx]
    rows = []
    for lg in range(1, 15):
        X = pssmdt.scale(features(D, idx, "PSSM-DT", lg))
        g, dec0 = grid(X, y, a.jobs)
        D2 = sq_dists(X)
        per_seed = [pssmdt.metrics(y, dec0)]
        for s in range(1, 5):
            per_seed.append(pssmdt.metrics(y, cv_decision(rbf(D2, 2.0 ** g["log2gamma"]), y, 2.0 ** g["log2C"], 5, s)))
        row = {"LG": lg, "log2C": g["log2C"], "log2gamma": g["log2gamma"],
               "ACC": round(per_seed[0]["ACC"] / 100, 4), "MCC": round(per_seed[0]["MCC"], 4),
               "ACC_seeds": [round(m["ACC"] / 100, 4) for m in per_seed],
               "MCC_seeds": [round(m["MCC"], 4) for m in per_seed]}
        rows.append(row)
        print(row, flush=True)
    (out / "lg_sweep.json").write_text(json.dumps(rows, indent=1) + "\n")


def cmd_independent(a):
    D = load(a.pssms)
    out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
    bench = json.loads(Path(a.bench).read_text())["encodings"]["PSSM-DT"]
    removed = {line.split("\t")[0] for line in Path(a.filter).read_text().splitlines()[1:] if line.strip()}
    tr = [i for i in subset(D, "benchmark") if str(D["id"][i]) not in removed]
    te = subset(D, "pdb186")
    Xtr, Xte = features(D, tr, "PSSM-DT"), features(D, te, "PSSM-DT")
    ytr, yte = D["label"][tr], D["label"][te]
    clf = pssmdt.PSSMDTClassifier(2.0 ** bench["log2C"], 2.0 ** bench["log2gamma"]).fit(Xtr, ytr)
    dec = clf.decision_function(Xte)
    res = {"training": {"n": len(tr), "positives": int(ytr.sum()), "removed": len(removed)},
           "log2C": bench["log2C"], "log2gamma": bench["log2gamma"],
           "pdb186": rounded(pssmdt.metrics(yte, dec))}
    # without the homology filter, for comparison
    tr_all = subset(D, "benchmark")
    clf_all = pssmdt.PSSMDTClassifier(2.0 ** bench["log2C"], 2.0 ** bench["log2gamma"]).fit(
        features(D, tr_all, "PSSM-DT"), D["label"][tr_all])
    res["pdb186_unfiltered_training"] = rounded(pssmdt.metrics(yte, clf_all.decision_function(Xte)))
    (out / "independent.json").write_text(json.dumps(res, indent=1) + "\n")
    (out / "pdb186_decisions.json").write_text(json.dumps(
        {"id": [str(D["id"][i]) for i in te], "label": yte.tolist(),
         "PSSM-DT": [round(float(v), 6) for v in dec]}) + "\n")
    print(res, flush=True)


def cmd_weights(a):
    D = load(a.pssms)
    out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
    bench = json.loads(Path(a.bench).read_text())["encodings"]["PSSM-DT"]
    idx = subset(D, "benchmark")
    clf = pssmdt.PSSMDTClassifier(2.0 ** bench["log2C"], 2.0 ** bench["log2gamma"]).fit(
        features(D, idx, "PSSM-DT"), D["label"][idx])
    W = clf.discriminant_weights()
    P = pssmdt.pair_weights(W, LG)
    aa = pssmdt.AMINO_ACIDS
    order = np.argsort(-P.ravel())
    top = [(aa[k // 20], aa[k % 20], round(float(P.ravel()[k]), 4)) for k in order[:20]]
    w = W.reshape(LG, 20, 20)
    top4 = {f"{p[0]}{p[1]}": [round(float(w[l, aa.index(p[0]), aa.index(p[1])]), 4) for l in range(LG)]
            for p in [("R", "R"), ("R", "P"), ("P", "R"), ("A", "R")]}
    ours4 = {f"{p[0]}{p[1]}": [round(float(w[l, aa.index(p[0]), aa.index(p[1])]), 4) for l in range(LG)]
             for p in top[:4]}
    res = {"pair_weights": np.round(P, 4).tolist(), "top_pairs": top,
           "paper_top4_by_lg": top4, "our_top4_by_lg": ours4, "n_support": int(len(clf.model_.support_))}
    (out / "weights.json").write_text(json.dumps(res, indent=1) + "\n")
    print(top[:8], flush=True)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("benchmark", "lg"):
        p = sub.add_parser(name); p.add_argument("pssms"); p.add_argument("outdir"); p.add_argument("--jobs", type=int, default=4)
    p = sub.add_parser("independent"); p.add_argument("pssms"); p.add_argument("filter"); p.add_argument("bench"); p.add_argument("outdir")
    p = sub.add_parser("weights"); p.add_argument("pssms"); p.add_argument("bench"); p.add_argument("outdir")
    a = ap.parse_args()
    {"benchmark": cmd_benchmark, "lg": cmd_lg, "independent": cmd_independent, "weights": cmd_weights}[a.cmd](a)


if __name__ == "__main__":
    main()

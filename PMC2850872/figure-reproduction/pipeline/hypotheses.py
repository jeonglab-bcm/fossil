"""Tests of the hypotheses behind the Table 2 gaps, on splits 0 to N-1. Not part of the pipeline.

Usage: hypotheses.py ANALYTIC.csv GRID.csv OUT.json [--splits 3] [--jobs 4]

H1  The polynomial kernel ran with LIBSVM's default gamma (1 / number of features), only C searched.
H2  Features were scaled to [-1, 1] by svm-scale (min-max over the training sample), not divided by
    fixed numbers: RBF and polynomial kernels, full grid search.
H3  The polynomial kernel had degree 2 instead of LIBSVM's default 3 (C and gamma searched).

Each gives the test AUC per split next to ours (GRID.csv's C and gamma, the pipeline's coding).
The record is committed as output/hypotheses.json and cited by the causes in results_notes.json.
"""

import argparse
import json

import numpy as np
import pandas as pd
from sklearn.svm import SVC

import diabclass as dc
from diabclass import core


def fit_auc(Xtr, ytr, Xte, yte, **kw):
    m = SVC(tol=1e-3, max_iter=10_000_000, **kw).fit(Xtr, ytr)
    return dc.auc(yte, m.decision_function(Xte))


def search(Xb, yb, kernel, log2c, log2g, degree, n_jobs, seed):
    from joblib import Parallel, delayed
    from sklearn.model_selection import StratifiedKFold

    def acc(c, g):
        skf = StratifiedKFold(5, shuffle=True, random_state=seed)
        ok = 0
        for tr, te in skf.split(Xb, yb):
            m = SVC(kernel=kernel, C=2.0**c, gamma=g, degree=degree, coef0=0.0,
                    max_iter=core.GRID_MAX_ITER).fit(Xb[tr], yb[tr])
            ok += int((m.predict(Xb[te]) == yb[te]).sum())
        return ok / len(yb)

    pts = [(c, g) for c in log2c for g in log2g]
    accs = Parallel(n_jobs=n_jobs)(delayed(acc)(c, g) for c, g in pts)
    best = max(zip(pts, accs), key=lambda t: (round(t[1], 12), -t[0][0], t[0][1]))
    return best[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("analytic")
    ap.add_argument("grid")
    ap.add_argument("out")
    ap.add_argument("--splits", type=int, default=3)
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    d = pd.read_csv(a.analytic)
    grid = pd.read_csv(a.grid)
    G = [2.0**g for g in dc.GRID_LOG2G]
    rows = []
    for scheme in ["I", "II"]:
        col = f"scheme_{scheme}_case"
        s = d[d[col].notna()].reset_index(drop=True)
        X = dc.encode(s.to_dict("records"), scheme)
        y = np.where(s[col] == 1, 1, -1)
        for rep in range(a.splits):
            tr, te = dc.split_train_test(y, s.category, 0.2, seed=rep)
            bal = tr[dc.undersample(y[tr], seed=rep)]
            Xb, yb, Xt, yt = X[bal], y[bal], X[te], y[te]
            g = grid[(grid.scheme == scheme) & (grid.rep == rep)].set_index("kernel")
            ours = {k: fit_auc(Xb, yb, Xt, yt, kernel=k, C=g.C[k], gamma=g.gamma[k]) for k in ["poly", "rbf"]}
            # H1: default gamma, C searched.
            g0 = 1.0 / X.shape[1]
            c1, _ = search(Xb, yb, "poly", dc.GRID_LOG2C, [g0], 3, a.jobs, rep)
            h1 = fit_auc(Xb, yb, Xt, yt, kernel="poly", C=2.0**c1, gamma=g0)
            # H2: svm-scale to [-1, 1] on the training sample.
            lo, hi = Xb.min(0), Xb.max(0)
            span = np.where(hi > lo, hi - lo, 1.0)
            sc = lambda Z: -1 + 2 * (Z - lo) / span  # noqa: E731
            h2 = {}
            for k in ["rbf", "poly"]:
                c2, g2 = search(sc(Xb), yb, k, dc.GRID_LOG2C, G, 3, a.jobs, rep)
                h2[k] = fit_auc(sc(Xb), yb, sc(Xt), yt, kernel=k, C=2.0**c2, gamma=g2)
            # H3: polynomial of degree 2.
            c3, g3 = search(Xb, yb, "poly", dc.GRID_LOG2C, G, 2, a.jobs, rep)
            h3 = fit_auc(Xb, yb, Xt, yt, kernel="poly", C=2.0**c3, gamma=g3, degree=2)
            rows.append({"scheme": scheme, "rep": rep, "ours_poly": ours["poly"], "ours_rbf": ours["rbf"],
                         "h1_poly_default_gamma": h1, "h2_minmax_rbf": h2["rbf"], "h2_minmax_poly": h2["poly"],
                         "h3_poly_degree2": h3})
            print(json.dumps(rows[-1]), flush=True)
    df = pd.DataFrame(rows)
    summary = {sch: {c: round(float(df[df.scheme == sch][c].mean()), 4) for c in df.columns if c not in ("scheme", "rep")}
               for sch in ["I", "II"]}
    json.dump({"about": "Hypothesis tests for the Table 2 gaps (hypotheses.py); mean test AUC over splits",
               "splits": a.splits, "mean": summary, "per_split": rows},
              open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()

"""Hypothesis tests behind the causes in results.json: each variant of an unstated setting, rerun on the
paper's data, with the micro-averaged metrics it gives.

Usage: hypotheses.py DATA_DIR SCORES_DIR OUT.json [--jobs N]

SCORES_DIR is the main run (run_models.py). Slow (about 20 minutes on 4 cores): the pipeline runs it with
--full and otherwise uses the committed output/hypotheses.json.

  svm_decision       SVM decision values instead of probability estimates (chem)
  knn_weka_prior     KNN with WEKA IBk's 1/n correction per class
  knn_exact_k        KNN with exactly k neighbours (ties broken by drug order)
  lr_bias            LR with a bias term (LIBLINEAR -B 1)
  lr_dual            LR solved in the dual (LIBLINEAR -s 7), epsilon 1
  lr_tight           LR with epsilon 1e-4 instead of 1
  lr_l1              L1-regularized LR (LIBLINEAR -s 6)
  lr_single_one      our LR, with every test drug of a fold whose training drugs hold no positive scored 1
  lr_first_label     our LR, with the scores of folds whose first training drug is positive inverted (a
                     probability column read by position: LIBLINEAR orders labels by first appearance)
  nb_multinomial     multinomial naive Bayes
  nb_alpha_0.1       Bernoulli naive Bayes with smoothing 0.1
  nb_single_one, nb_first_label   as for LR
"""
import argparse
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

import adrfusion as A
from adrfusion import core

from run_models import load

FULL = "chem+bio+pheno"
_D = {}


def init(data):
    _D["data"] = data
    _D["X"] = {}


def model(name):
    from sklearn.linear_model import LogisticRegression
    from sklearn.naive_bayes import BernoulliNB, MultinomialNB

    return {
        "lr_bias": lambda: LogisticRegression(solver="liblinear", C=10, tol=1),
        "lr_dual": lambda: LogisticRegression(solver="liblinear", C=10, tol=1, dual=True, fit_intercept=False),
        "lr_tight": lambda: LogisticRegression(solver="liblinear", C=10, tol=1e-4, fit_intercept=False),
        "lr_l1": lambda: LogisticRegression(solver="liblinear", penalty="l1", C=10, tol=1, fit_intercept=False),
        "nb_multinomial": lambda: MultinomialNB(alpha=1.0),
        "nb_alpha_0.1": lambda: BernoulliNB(alpha=0.1),
    }[name]()


def one(args):
    name, j = args
    data = _D["data"]
    y = data.Y[:, j].astype(np.int8)
    fold = data.folds[:, j]
    out = np.zeros(data.n_drugs)
    if name.startswith("knn"):
        D = core.distance_for(data, _D["dist"], FULL, j)
        for k in np.unique(fold):
            te, tr = np.flatnonzero(fold == k), np.flatnonzero(fold != k)
            Dt = D[np.ix_(te, tr)]
            if name == "knn_weka_prior":
                out[te] = core._knn_scores(Dt, y[tr], 55, prior=True)
            else:
                for a, row in enumerate(Dt):
                    out[te[a]] = y[tr][np.argsort(row, kind="stable")[:55]].mean()
        return out
    X = core.features_for(data, FULL, j)
    for k in np.unique(fold):
        te, tr = fold == k, fold != k
        if y[tr].min() == y[tr].max():
            out[te] = float(y[tr][0])
            continue
        m = model(name).fit(X[tr], y[tr])
        out[te] = m.predict_proba(X[te])[:, list(m.classes_).index(1)]
    return out


def metrics(Y, S, sub):
    a = A.micro_metrics(Y, S).as_dict()
    b = A.micro_metrics(Y[:, sub], S[:, sub]).as_dict()
    keys = ("auc", "acc", "precision", "recall")
    return {"all": {k: round(a[k], 10) for k in keys}, "50+": {k: round(b[k], 10) for k in keys}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("scores")
    ap.add_argument("out")
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 1)
    a = ap.parse_args()
    data = load(a.data)
    Y, F = data.Y, data.folds
    sub = Y.sum(0) > 50
    res = {}
    S = A.cross_validated_scores(data, "chem", "svm", scores="decision", n_jobs=a.jobs)
    res["svm_decision"] = metrics(Y, S, sub)
    dist = A.block_distances(data)
    for name in ("knn_weka_prior", "knn_exact_k", "lr_bias", "lr_dual", "lr_tight", "lr_l1", "nb_multinomial", "nb_alpha_0.1"):
        tasks = [(name, j) for j in range(data.n_adrs)]
        if name.startswith("knn"):
            init(data)
            _D["dist"] = dist
            cols = [one(t) for t in tasks]
        else:
            with ProcessPoolExecutor(a.jobs, initializer=init, initargs=(data,)) as ex:
                cols = list(ex.map(one, tasks, chunksize=20))
        res[name] = metrics(Y, np.column_stack(cols), sub)
        print(name, res[name]["all"]["auc"], res[name]["50+"]["auc"], file=sys.stderr, flush=True)
    single = np.zeros(Y.shape, bool)
    first = np.zeros(Y.shape, bool)
    for j in range(Y.shape[1]):
        for k in np.unique(F[:, j]):
            tr = np.flatnonzero(F[:, j] != k)
            te = F[:, j] == k
            single[te, j] = Y[tr, j].sum() == 0
            first[te, j] = Y[tr[0], j] == 1
    for alg in ("lr", "nb"):
        base = np.load(Path(a.scores) / f"{alg}:{FULL}.npy")
        s1 = base.copy()
        s1[single] = 1.0
        res[f"{alg}_single_one"] = metrics(Y, s1, sub)
        res[f"{alg}_first_label"] = metrics(Y, np.where(first, 1 - base, base), sub)
    res["_counts"] = {"pairs_in_single_class_folds": int(single.sum()), "pairs_in_first_label_positive_folds": int(first.sum()),
                      "adrs_with_one_drug": int((Y.sum(0) == 1).sum()), "adrs_with_no_drug": int((Y.sum(0) == 0).sum())}
    Path(a.out).write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main()

"""Classification experiments of Figs 3, S2 and S3 and the marker frequencies of Tables 1 and S2.

Usage:
  cv.py DATA OUTDIR within DATASET FIRST LAST      repeats FIRST..LAST-1 of 5-fold CV in one dataset
  cv.py DATA OUTDIR cross SOURCE TARGET FIRST LAST markers from SOURCE, classifiers on TARGET

Writes one JSON file per repeat (OUTDIR/<experiment>/rep<NNN>.json) with, for each of the five
folds, the test AUC of every method and classifier and the markers each PAC classifier used.

The procedure follows the paper's Methods; the choices it leaves open are ours and listed in
results_notes.json:
  * Expression is z-scored per gene over all samples of a dataset (the paper's definition of z).
  * Folds are stratified by class; each repeat r uses seed (DATASET, r) so any repeat can be rerun.
  * The training four fifths are split, stratified, into three equal parts: two for marker
    selection (pathway ranking, CORG search, gene ranking), one for validation.
  * Pathways are pre-selected by Tian et al.'s statistic |sum of member t| / sqrt(members), top 52.
  * Markers are ranked by the p-value of their t statistic in the marker-selection samples and
    added one at a time to a logistic regression (ridge 1e-8) fitted on those samples; the count
    with the best validation AUC is kept, and that model is scored on the test fifth.
  * Gene: as many top genes as the distinct CORGs pooled over the 52 pathways.
  * PAC_random: random gene sets with the sizes of the 52 pathways (measured members), CORG search
    inside each, two draws per partition (1000 random marker sets over the 500 partitions).
  * Mean, Median, PCA: the summary of all measured members of the same 52 pathways.
  * Other classifiers (Fig. S2): k-nearest neighbours (k = 3, 5; accuracy), Gaussian naive Bayes
    and linear discriminant analysis (AUC), with the same sequential selection.
  * Forward selection (Fig. S3): from the empty set, add the marker that most improves the
    validation AUC, and stop when none does.
"""

from __future__ import annotations

import json
import math
import sys
import zlib
from pathlib import Path

import numpy as np
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.model_selection import StratifiedKFold
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier

from common import Dataset, top_count
from pacorg import (activity, auc, find_corgs, fit_logistic, mean_activity, median_activity, pca_activity,
                    predict_logistic, t_scores, tian_scores, zscore)

import os

# Variants for testing hypotheses about unstated settings (default: none).
#   random_nocorg  PAC_random uses all genes of each random set (no CORG search)
#   cross_all      cross-dataset markers from all pathways, without Tian's pre-selection
#   lr_only        logistic regression only (faster)
#   seq_stop       sequential selection stops at the first marker that does not raise the
#                  validation score (instead of keeping the best count over all markers)
VARIANT = set(filter(None, os.environ.get("PAC_VARIANT", "").split(",")))
N_FOLDS = 5
N_TOP = top_count(0.10)  # 52
RANDOM_DRAWS = 2


def seed_for(*parts) -> int:
    return zlib.crc32("/".join(map(str, parts)).encode())


def tian(t, set_rows):
    """|Tian score| of each set (pacorg.tian_scores); empty sets rank last."""
    return np.nan_to_num(np.abs(tian_scores(t, set_rows)), nan=-1.0)


def split_train(y_train, rng):
    """Stratified split of training samples into marker-selection (2/3) and validation (1/3) indices."""
    skf = StratifiedKFold(3, shuffle=True, random_state=int(rng.integers(2**31)))
    parts = [v for _, v in skf.split(np.zeros(len(y_train)), y_train)]
    return np.sort(np.concatenate(parts[:2])), np.sort(parts[2])


# ----------------------------------------------------------------------------- classifiers

def _lr_scores(Ftr, ytr, Fev):
    w = fit_logistic(Ftr, ytr)
    return predict_logistic(w, Fev)


def _sk_scores(model, Ftr, ytr, Fev):
    model.fit(Ftr, ytr)
    if hasattr(model, "predict_proba"):
        return model.predict_proba(Fev)[:, 1]
    return model.decision_function(Fev)


def evaluate(F, y, sel, val, test, order, kind):
    """Sequential selection over the ranked markers; returns (test score, markers used)."""
    best = (-1.0, 0)
    Fs, ys = F[sel], y[sel]
    for k in range(1, len(order) + 1):
        cols = order[:k]
        if kind == "lr":
            s = _lr_scores(Fs[:, cols], ys, F[val][:, cols])
            m = auc(s, y[val])
        elif kind in ("knn3", "knn5"):
            nn = KNeighborsClassifier(n_neighbors=int(kind[-1]))
            nn.fit(Fs[:, cols], ys)
            m = float(np.mean(nn.predict(F[val][:, cols]) == y[val]))
        elif kind == "nb":
            m = auc(_sk_scores(GaussianNB(), Fs[:, cols], ys, F[val][:, cols]), y[val])
        elif kind == "lda":
            m = auc(_sk_scores(LinearDiscriminantAnalysis(), Fs[:, cols], ys, F[val][:, cols]), y[val])
        if m > best[0]:
            best = (m, k)
        elif "seq_stop" in VARIANT:
            break
    cols = order[: best[1]]
    if kind == "lr":
        score = auc(_lr_scores(Fs[:, cols], ys, F[test][:, cols]), y[test])
    elif kind in ("knn3", "knn5"):
        nn = KNeighborsClassifier(n_neighbors=int(kind[-1])).fit(Fs[:, cols], ys)
        score = float(np.mean(nn.predict(F[test][:, cols]) == y[test]))
    elif kind == "nb":
        score = auc(_sk_scores(GaussianNB(), Fs[:, cols], ys, F[test][:, cols]), y[test])
    else:
        score = auc(_sk_scores(LinearDiscriminantAnalysis(), Fs[:, cols], ys, F[test][:, cols]), y[test])
    return score, list(cols)


def forward(F, y, sel, val, test, candidates):
    """Forward selection with logistic regression and validation AUC."""
    chosen, best = [], -1.0
    remaining = list(candidates)
    while remaining:
        trial = []
        for c in remaining:
            cols = chosen + [c]
            trial.append(auc(_lr_scores(F[sel][:, cols], y[sel], F[val][:, cols]), y[val]))
        i = int(np.argmax(trial))
        if trial[i] <= best:
            break
        best = trial[i]
        chosen.append(remaining.pop(i))
    return auc(_lr_scores(F[sel][:, chosen], y[sel], F[test][:, chosen]), y[test])


def rank(F, y, sel):
    """Marker order by increasing p-value (decreasing |t|) in the marker-selection samples."""
    t = np.abs(t_scores(F[sel].T, y[sel]))
    t = np.nan_to_num(t, nan=0.0)
    return list(np.argsort(-t, kind="stable"))


CLASSIFIERS = ["lr", "knn3", "knn5", "nb", "lda"]


# ----------------------------------------------------------------------------- within a dataset

def within(D: Dataset, rep: int, extra: bool = True):
    Z = zscore(D.X)
    y = D.y
    rng = np.random.default_rng(seed_for(D.name, rep))
    skf = StratifiedKFold(N_FOLDS, shuffle=True, random_state=int(rng.integers(2**31)))
    folds = []
    measured = [r for r in D.set_rows]
    for fold, (train, test) in enumerate(skf.split(np.zeros(len(y)), y)):
        msel, mval = split_train(y[train], rng)
        sel, val = train[msel], train[mval]
        Zs = Z[:, sel]
        t = t_scores(Zs, y[sel])
        top = list(np.argsort(-tian(t, measured), kind="stable")[:N_TOP])
        corgs = [find_corgs(Zs, y[sel], measured[p], t) for p in top]
        pooled = sorted({r for c in corgs for r in c})
        n_genes = len(pooled)
        feats = {
            "PAC": np.column_stack([activity(Z, c) for c in corgs]),
            "Gene": Z[np.argsort(-np.abs(t), kind="stable")[:n_genes]].T,
            "Mean": np.column_stack([mean_activity(Z, measured[p]) for p in top]),
            "Median": np.column_stack([median_activity(Z, measured[p]) for p in top]),
            "PCA": np.column_stack([pca_activity(Z, measured[p], fit_columns=sel) for p in top]),
        }
        res = {"fold": fold, "n_test": int(len(test)), "pathways": [D.set_names[p] for p in top],
               "n_corgs": [len(c) for c in corgs], "n_genes": n_genes, "scores": {}}
        for m, F in feats.items():
            order = rank(F, y, sel)
            kinds = CLASSIFIERS if extra else ["lr"]
            for kind in kinds:
                score, used = evaluate(F, y, sel, val, test, order, kind)
                res["scores"][f"{m}/{kind}"] = score
                if m == "PAC" and kind == "lr":
                    res["pac_used"] = [D.set_names[top[i]] for i in used]
            if extra and m in ("PAC", "Gene"):
                res["scores"][f"{m}/fwd"] = forward(F, y, sel, val, test, order)
        # PAC_random: random gene sets of the same sizes, CORG search inside each.
        all_rows = np.arange(len(D.genes))
        rnd = []
        for _ in range(RANDOM_DRAWS):
            rc = []
            for p in top:
                rows = list(rng.choice(all_rows, size=len(measured[p]), replace=False))
                rc.append(rows if "random_nocorg" in VARIANT else find_corgs(Zs, y[sel], rows, t))
            F = np.column_stack([activity(Z, c) for c in rc])
            rnd.append(evaluate(F, y, sel, val, test, rank(F, y, sel), "lr")[0])
        res["scores"]["PAC_random/lr"] = float(np.mean(rnd))
        res["scores"]["PAC_random/draws"] = rnd
        folds.append(res)
    return folds


# ----------------------------------------------------------------------------- across datasets

def cross_markers(S: Dataset, T: Dataset):
    """Markers from the whole source dataset: Tian top 52 pathways with their CORGs, and top genes."""
    Z = zscore(S.X)
    t = t_scores(Z, S.y)
    if "cross_all" in VARIANT:
        top = [i for i, r in enumerate(S.set_rows) if r]
    else:
        top = list(np.argsort(-tian(t, S.set_rows), kind="stable")[:N_TOP])
    corgs = {S.set_names[p]: find_corgs(Z, S.y, S.set_rows[p], t) for p in top}
    pooled = sorted({r for c in corgs.values() for r in c})
    genes = list(np.argsort(-np.abs(t), kind="stable")[: len(pooled)])
    return {
        "pathways": [S.set_names[p] for p in top],
        "corgs": {k: [S.genes[r] for r in v] for k, v in corgs.items()},
        "corg_symbols": {k: [S.symbols[r] for r in v] for k, v in corgs.items()},
        "genes": [S.genes[r] for r in genes],
        "n_genes": len(genes),
    }


def cross(S: Dataset, T: Dataset, rep: int, markers: dict, extra: bool = True):
    Z = zscore(T.X)
    y = T.y
    pw = [p for p in markers["pathways"] if any(g in T.index for g in markers["corgs"][p])]
    feats = {
        "PAC": np.column_stack([activity(Z, [T.index[g] for g in markers["corgs"][p] if g in T.index]) for p in pw]),
        "Gene": Z[[T.index[g] for g in markers["genes"] if g in T.index]].T,
    }
    rng = np.random.default_rng(seed_for(S.name, T.name, rep))
    skf = StratifiedKFold(N_FOLDS, shuffle=True, random_state=int(rng.integers(2**31)))
    folds = []
    for fold, (train, test) in enumerate(skf.split(np.zeros(len(y)), y)):
        msel, mval = split_train(y[train], rng)
        sel, val = train[msel], train[mval]
        res = {"fold": fold, "n_test": int(len(test)), "scores": {}}
        for m, F in feats.items():
            order = rank(F, y, sel)
            for kind in (CLASSIFIERS if extra else ["lr"]):
                score, used = evaluate(F, y, sel, val, test, order, kind)
                res["scores"][f"{m}/{kind}"] = score
                if m == "PAC" and kind == "lr":
                    res["pac_used"] = [pw[i] for i in used]
        folds.append(res)
    return folds


def main(argv):
    data, outdir, mode = Path(argv[0]), Path(argv[1]), argv[2]
    if mode == "within":
        name, first, last = argv[3], int(argv[4]), int(argv[5])
        D = Dataset(data, name)
        out = outdir / "within" / name
        out.mkdir(parents=True, exist_ok=True)
        for r in range(first, last):
            (out / f"rep{r:03d}.json").write_text(json.dumps({"repeat": r, "folds": within(D, r, "lr_only" not in VARIANT)}))
            print(name, r, flush=True)
    elif mode == "cross":
        s, t, first, last = argv[3], argv[4], int(argv[5]), int(argv[6])
        S, T = Dataset(data, s), Dataset(data, t)
        out = outdir / "cross" / f"{s}__{t}"
        out.mkdir(parents=True, exist_ok=True)
        mk = out / "markers.json"
        markers = cross_markers(S, T)
        mk.write_text(json.dumps(markers, indent=1))
        for r in range(first, last):
            (out / f"rep{r:03d}.json").write_text(json.dumps({"repeat": r, "folds": cross(S, T, r, markers, "lr_only" not in VARIANT)}))
            print(s, t, r, flush=True)
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])

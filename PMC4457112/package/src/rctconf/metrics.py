"""The measures of Cohen et al. (2015), Tables 1-3: AUC with the Hanley-McNeil 95% interval,
average precision, F1, accuracy and the mean squared error of a confidence."""

from __future__ import annotations

import math

import numpy as np


def _arrays(labels, scores):
    y = np.asarray(labels).astype(bool)
    s = np.asarray(scores, dtype=float)
    if y.shape != s.shape:
        raise ValueError("labels and scores differ in length")
    if y.all() or not y.any():
        raise ValueError("need both positive and negative labels")
    return y, s


def auc(labels, scores) -> float:
    """Area under the ROC curve (Mann-Whitney U, ties counted one half)."""
    y, s = _arrays(labels, scores)
    order = np.argsort(s, kind="mergesort")
    ss = s[order]
    ranks = np.empty(len(s))
    # average ranks over ties
    _, start, counts = np.unique(ss, return_index=True, return_counts=True)
    avg = start + (counts + 1) / 2.0
    ranks[order] = np.repeat(avg, counts)
    n1 = y.sum()
    n0 = len(y) - n1
    return float((ranks[y].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def hanley_mcneil_se(a: float, n_pos: int, n_neg: int) -> float:
    """Standard error of an AUC by Hanley and McNeil (1982)."""
    q1 = a / (2 - a)
    q2 = 2 * a * a / (1 + a)
    var = (a * (1 - a) + (n_pos - 1) * (q1 - a * a) + (n_neg - 1) * (q2 - a * a)) / (n_pos * n_neg)
    return math.sqrt(var)


def auc_ci(labels, scores, z: float = 1.959964) -> tuple[float, float, float]:
    """AUC and its Hanley-McNeil 95% interval."""
    y, _ = _arrays(labels, scores)
    a = auc(labels, scores)
    se = hanley_mcneil_se(a, int(y.sum()), int((~y).sum()))
    return a, a - z * se, a + z * se


def average_precision(labels, scores) -> float:
    """Mean of the precision at the rank of each positive (ties broken as one block)."""
    y, s = _arrays(labels, scores)
    order = np.argsort(-s, kind="mergesort")
    ys, ss = y[order], s[order]
    # thresholds at distinct scores
    last = np.r_[np.nonzero(np.diff(ss))[0], len(ss) - 1]
    tp = np.cumsum(ys)[last]
    fp = (last + 1) - tp
    precision = tp / (tp + fp)
    recall = tp / y.sum()
    return float(np.sum(np.diff(np.r_[0.0, recall]) * precision))


def binary_measures(labels, predicted) -> dict:
    y = np.asarray(labels).astype(bool)
    p = np.asarray(predicted).astype(bool)
    tp = int((y & p).sum())
    fp = int((~y & p).sum())
    fn = int((y & ~p).sum())
    tn = int((~y & ~p).sum())
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": prec, "recall": rec, "f1": f1,
            "accuracy": (tp + tn) / len(y)}


def mse(labels, confidence) -> float:
    """Mean squared error of a confidence against the 0/1 label (the Brier score)."""
    y = np.asarray(labels).astype(float)
    c = np.asarray(confidence, dtype=float)
    return float(np.mean((c - y) ** 2))


def evaluate(labels, margins, confidence=None, baseline=None) -> dict:
    """All measures of Tables 1-3 for SVM margins (predicted RCT when the margin is above 0)."""
    a, lo, hi = auc_ci(labels, margins)
    out = {"n": int(len(labels)), "n_pos": int(np.sum(labels)), "auc": a, "auc_ci_low": lo, "auc_ci_high": hi,
           "average_precision": average_precision(labels, margins)}
    b = binary_measures(labels, np.asarray(margins) > 0)
    out.update({"f1": b["f1"], "accuracy": b["accuracy"], "precision": b["precision"], "recall": b["recall"]})
    if confidence is not None:
        out["mse"] = mse(labels, confidence)
    if baseline is not None:
        out["mse_sigmoid"] = mse(labels, baseline)
    return out

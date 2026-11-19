"""Scoring a predicted network against a gold standard: AUPR, AUROC and F-beta (Eq. 3).

All scores are on undirected gene pairs (i < j), without self-pairs: GeCON and the mutual-information
methods it is compared with give symmetric scores, so a directed gold-standard edge in either direction
counts as one true pair.
"""

from __future__ import annotations

import numpy as np


def pairs(n: int) -> tuple[np.ndarray, np.ndarray]:
    return np.triu_indices(n, 1)


def undirected_truth(gold: np.ndarray) -> np.ndarray:
    """Upper-triangle labels (1 = an edge in either direction) of a square gold-standard matrix."""
    g = np.asarray(gold) != 0
    g = g | g.T
    i, j = pairs(g.shape[0])
    return g[i, j].astype(int)


def upper(scores: np.ndarray) -> np.ndarray:
    """Upper-triangle scores of a square matrix, symmetrised by the maximum of the two directions."""
    s = np.asarray(scores, dtype=float)
    s = np.maximum(s, s.T)
    i, j = pairs(s.shape[0])
    return s[i, j]


def _curve(y: np.ndarray, s: np.ndarray):
    """Cumulative true and false positives at each distinct score, highest first."""
    order = np.argsort(-s, kind="mergesort")
    s, y = s[order], y[order]
    distinct = np.r_[np.nonzero(np.diff(s))[0], len(s) - 1]
    tp = np.cumsum(y)[distinct]
    fp = np.cumsum(1 - y)[distinct]
    return tp.astype(float), fp.astype(float)


def auroc(y: np.ndarray, s: np.ndarray) -> float:
    """Area under the ROC curve (trapezoidal, ties as one step)."""
    y = np.asarray(y)
    P, N = y.sum(), len(y) - y.sum()
    tp, fp = _curve(y, np.asarray(s, dtype=float))
    tpr = np.r_[0, tp / P]
    fpr = np.r_[0, fp / N]
    return float(np.trapezoid(tpr, fpr))


def aupr(y: np.ndarray, s: np.ndarray) -> float:
    """Area under the precision-recall curve (trapezoidal in recall, starting at the first threshold's
    precision; ties as one step)."""
    y = np.asarray(y)
    P = y.sum()
    tp, fp = _curve(y, np.asarray(s, dtype=float))
    rec = tp / P
    prec = tp / (tp + fp)
    rec = np.r_[0, rec]
    prec = np.r_[prec[0], prec]
    return float(np.trapezoid(prec, rec))


def fbeta(y: np.ndarray, pred: np.ndarray, beta: float = 0.5) -> float:
    """F-beta (Eq. 3) of a binary prediction."""
    y = np.asarray(y).astype(bool)
    p = np.asarray(pred).astype(bool)
    tp = float((y & p).sum())
    if tp == 0:
        return 0.0
    precision = tp / p.sum()
    recall = tp / y.sum()
    b2 = beta * beta
    return float((1 + b2) * precision * recall / (b2 * precision + recall))


def max_fbeta(y: np.ndarray, s: np.ndarray, beta: float = 0.5) -> float:
    """Largest F-beta over all thresholds of a score (the maximum F score of the PR curve)."""
    y = np.asarray(y)
    P = y.sum()
    tp, fp = _curve(y, np.asarray(s, dtype=float))
    prec = tp / (tp + fp)
    rec = tp / P
    b2 = beta * beta
    with np.errstate(invalid="ignore", divide="ignore"):
        f = (1 + b2) * prec * rec / (b2 * prec + rec)
    f = np.nan_to_num(f)
    return float(f.max()) if len(f) else 0.0


def score_network(gold: np.ndarray, scores: np.ndarray, beta: float = 0.5, binary: np.ndarray | None = None) -> dict:
    """AUPR, AUROC and the maximum F-beta of a score matrix; F-beta of ``binary`` too when given."""
    y = undirected_truth(gold)
    s = upper(scores)
    out = {"aupr": aupr(y, s), "auroc": auroc(y, s), "f_max": max_fbeta(y, s, beta), "n_true": int(y.sum()), "n_pairs": int(len(y))}
    if binary is not None:
        out["f_binary"] = fbeta(y, upper(np.abs(binary)) > 0, beta)
    return out

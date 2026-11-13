"""Graph-based semi-supervised classifier: learning with local and global consistency.

Zhou D, Bousquet O, Lal TN, Weston J, Schoelkopf B (2004), as used by You et al. (2010):

    W_ij = exp(-||x_i - x_j||^2 / (2 sigma^2)) for i != j, W_ii = 0      (eq. 11)
    S = D^(-1/2) W D^(-1/2)
    F* = (I - alpha S)^(-1) Y                                            (eq. 12)
"""

from __future__ import annotations

import numpy as np
from scipy.linalg import solve
from scipy.spatial.distance import pdist, squareform

ALPHA_DEFAULT = 0.99


def affinity(X: np.ndarray, sigma: float) -> np.ndarray:
    """Gaussian affinity of eq. 11 with a zero diagonal."""
    D2 = squareform(pdist(np.asarray(X, dtype=float), "sqeuclidean"))
    W = np.exp(-D2 / (2.0 * sigma * sigma))
    np.fill_diagonal(W, 0.0)
    return W


def median_sigma(X: np.ndarray) -> float:
    """A default length scale: the median distance between points."""
    d = pdist(np.asarray(X, dtype=float))
    return float(np.median(d)) if d.size else 1.0


def label_spreading(X: np.ndarray, y: np.ndarray, sigma: float | None = None,
                    alpha: float = ALPHA_DEFAULT) -> np.ndarray:
    """Soft labels for every point.

    X: (n, d) features of labelled and unlabelled points together.
    y: (n,) with 1 (positive, here an SGI pair), 0 (negative) or -1 (unlabelled).
    Returns F*[:, 1] / (F*[:, 0] + F*[:, 1]), a soft label in [0, 1] (0.5 where F* is zero).
    """
    X = np.asarray(X, dtype=float)
    y = np.asarray(y)
    if X.shape[0] != y.shape[0]:
        raise ValueError("X and y must have the same number of rows")
    if not np.any(y == 1) or not np.any(y == 0):
        raise ValueError("need at least one labelled point of each class")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must lie between 0 and 1")
    sigma = median_sigma(X) if sigma is None else float(sigma)
    W = affinity(X, sigma)
    d = W.sum(axis=1)
    d[d == 0] = 1.0
    s = 1.0 / np.sqrt(d)
    S = W * s[:, None] * s[None, :]
    Y = np.zeros((len(y), 2))
    Y[y == 0, 0] = 1.0
    Y[y == 1, 1] = 1.0
    A = np.eye(len(y)) - alpha * S
    F = solve(A, Y, assume_a="sym")
    tot = F.sum(axis=1)
    out = np.full(len(y), 0.5)
    ok = tot > 0
    out[ok] = F[ok, 1] / tot[ok]
    return out


SIGMA_FACTORS = (0.05, 0.1, 0.2, 0.5, 1.0)


def select_sigma(X: np.ndarray, y: np.ndarray, factors=SIGMA_FACTORS, alpha: float = ALPHA_DEFAULT,
                 holdout: float = 1.0 / 3.0, seed: int = 0) -> float:
    """Choose sigma among factors x the median distance by hiding a share of the labelled points and
    scoring how well label spreading ranks them (area under the ROC curve). Only labels in y are used."""
    y = np.asarray(y)
    rng = np.random.default_rng(seed)
    labelled = np.where(y >= 0)[0]
    hide = np.zeros(len(y), dtype=bool)
    for c in (0, 1):
        members = labelled[y[labelled] == c]
        k = max(1, int(round(holdout * len(members))))
        hide[rng.choice(members, k, replace=False)] = True
    y_in = y.copy()
    y_in[hide] = -1
    base = median_sigma(X)
    best, best_auc = base, -1.0
    for f in factors:
        s = label_spreading(X, y_in, sigma=base * f, alpha=alpha)[hide]
        t = y[hide]
        # area under the ROC curve via the rank-sum statistic
        order = np.argsort(np.argsort(s, kind="mergesort"), kind="mergesort") + 1.0
        npos, nneg = (t == 1).sum(), (t == 0).sum()
        auc = (order[t == 1].sum() - npos * (npos + 1) / 2.0) / (npos * nneg)
        if auc > best_auc:
            best, best_auc = base * f, auc
    return float(best)

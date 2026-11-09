"""The SVM side of SVM-PSSM-DT: scaling, grid search, jackknife, metrics, discriminant weights.

The paper uses LIBSVM with an RBF kernel, C and gamma from a grid search with 5-fold cross
validation, and jackknife (leave-one-out) tests. scikit-learn's SVC wraps LIBSVM. Features are
scaled to [-1, 1] on the data set as LIBSVM's svm-scale does, and the RBF kernel matrix is computed
once, so a jackknife of a thousand sequences takes seconds.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.svm import SVC

# LIBSVM grid.py defaults
LOG2C = tuple(range(-5, 16, 2))
LOG2G = tuple(range(3, -16, -2))


def scale(X: np.ndarray, lower: float = -1.0, upper: float = 1.0,
          ref: np.ndarray | None = None) -> np.ndarray:
    """Scale each feature linearly to [lower, upper] using the range of ``ref`` (default ``X``),
    as svm-scale does. Features that are constant in ``ref`` become 0 and do not enter the kernel."""
    X = np.asarray(X, dtype=np.float64)
    R = X if ref is None else np.asarray(ref, dtype=np.float64)
    lo, hi = R.min(axis=0), R.max(axis=0)
    span = hi - lo
    out = np.zeros_like(X)
    ok = span > 0
    out[:, ok] = lower + (upper - lower) * (X[:, ok] - lo[ok]) / span[ok]
    return out


def sq_dists(A: np.ndarray, B: np.ndarray | None = None) -> np.ndarray:
    """Squared Euclidean distances between the rows of A and B."""
    B = A if B is None else B
    d = (A * A).sum(1)[:, None] + (B * B).sum(1)[None, :] - 2.0 * A @ B.T
    return np.maximum(d, 0.0)


def rbf(D2: np.ndarray, gamma: float) -> np.ndarray:
    return np.exp(-gamma * D2)


def _svc(C: float) -> SVC:
    return SVC(C=C, kernel="precomputed", cache_size=500, tol=1e-3)


def cv_decision(K: np.ndarray, y: np.ndarray, C: float, folds: int | None = 5,
                seed: int = 0) -> np.ndarray:
    """Out-of-fold decision values from a precomputed kernel. ``folds=None`` is the jackknife."""
    y = np.asarray(y)
    n = len(y)
    dec = np.empty(n)
    if folds is None:
        splits = ((np.delete(np.arange(n), i), np.array([i])) for i in range(n))
    else:
        splits = StratifiedKFold(folds, shuffle=True, random_state=seed).split(np.zeros(n), y)
    for tr, te in splits:
        m = _svc(C).fit(K[np.ix_(tr, tr)], y[tr])
        dec[te] = m.decision_function(K[np.ix_(te, tr)])
    return dec


@dataclass
class GridResult:
    C: float
    gamma: float
    accuracy: float
    table: list  # [(log2C, log2gamma, accuracy)]


def grid_search(X: np.ndarray, y: np.ndarray, log2c=LOG2C, log2g=LOG2G, folds: int = 5,
                seed: int = 0) -> GridResult:
    """C and gamma by 5-fold cross-validated accuracy over a log2 grid (LIBSVM grid.py ranges).
    Ties go to the first in grid order (smaller C, then larger gamma)."""
    y = np.asarray(y)
    D2 = sq_dists(X)
    table = []
    best = None
    for c in log2c:
        for g in log2g:
            dec = cv_decision(rbf(D2, 2.0 ** g), y, 2.0 ** c, folds, seed)
            a = float(np.mean((dec > 0) == (y > 0)))
            table.append((c, g, a))
            if best is None or a > best[2] + 1e-12:
                best = (c, g, a)
    return GridResult(2.0 ** best[0], 2.0 ** best[1], best[2], table)


def jackknife(X: np.ndarray, y: np.ndarray, C: float, gamma: float) -> np.ndarray:
    """Leave-one-out decision values with fixed C and gamma."""
    return cv_decision(rbf(sq_dists(X), gamma), y, C, folds=None)


def cross_validation(X: np.ndarray, y: np.ndarray, C: float, gamma: float, folds: int = 5,
                     seed: int = 0) -> np.ndarray:
    """Out-of-fold decision values of a stratified k-fold cross validation."""
    return cv_decision(rbf(sq_dists(X), gamma), y, C, folds, seed)


def metrics(y: np.ndarray, decision: np.ndarray, threshold: float = 0.0) -> dict:
    """SN, SP, ACC, MCC (Eqs. 8 to 11) at the threshold, and AUC; percentages for SN, SP, ACC, AUC."""
    y = np.asarray(y) > 0
    p = np.asarray(decision) > threshold
    tp = int(np.sum(p & y)); tn = int(np.sum(~p & ~y))
    fp = int(np.sum(p & ~y)); fn = int(np.sum(~p & y))
    den = np.sqrt(float(tp + fn) * (tp + fp) * (tn + fp) * (tn + fn))
    return {
        "TP": tp, "TN": tn, "FP": fp, "FN": fn,
        "SN": 100.0 * tp / (tp + fn), "SP": 100.0 * tn / (tn + fp),
        "ACC": 100.0 * (tp + tn) / len(y),
        "MCC": float((tp * tn - fp * fn) / den) if den else 0.0,
        "AUC": float(100.0 * roc_auc_score(y, decision)),
    }


def roc_curve_points(y: np.ndarray, decision: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """False and true positive rates (%) as the threshold falls through the decision values."""
    from sklearn.metrics import roc_curve
    fpr, tpr, _ = roc_curve(np.asarray(y) > 0, decision)
    return 100 * fpr, 100 * tpr


class PSSMDTClassifier:
    """An RBF SVM on scaled features, trained once; ``decision_function`` scores new sequences."""

    def __init__(self, C: float, gamma: float):
        self.C, self.gamma = C, gamma

    def fit(self, X: np.ndarray, y: np.ndarray) -> "PSSMDTClassifier":
        self.ref_ = np.asarray(X, dtype=np.float64)
        Xs = scale(self.ref_)
        self.model_ = SVC(C=self.C, kernel="rbf", gamma=self.gamma, tol=1e-3).fit(Xs, np.asarray(y))
        self.Xs_ = Xs
        return self

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        return self.model_.decision_function(scale(X, ref=self.ref_))

    def predict(self, X: np.ndarray) -> np.ndarray:
        return (self.decision_function(X) > 0).astype(int)

    def discriminant_weights(self) -> np.ndarray:
        """W = A . M (Eq. 12): A holds alpha_i * y_i of the support vectors, M their scaled features.
        A positive weight points to DNA binding (label 1)."""
        A = self.model_.dual_coef_.ravel()
        M = self.Xs_[self.model_.support_]
        W = A @ M
        # SVC's dual_coef_ is signed for classes_[1]; make positive mean "binds DNA"
        return W if self.model_.classes_[1] == 1 else -W


def pair_weights(W: np.ndarray, lg_max: int) -> np.ndarray:
    """Discriminant weight of each of the 400 amino-acid pairs: the root of the sum of squares of
    its positive descriptor weights over lg (the "quadratic sum" of the paper), as a 20 x 20 array
    (row: first amino acid, column: second)."""
    w = np.asarray(W).reshape(lg_max, 20, 20)
    return np.sqrt(np.sum(np.where(w > 0, w, 0.0) ** 2, axis=0))

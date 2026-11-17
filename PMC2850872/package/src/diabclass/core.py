"""The method of Yu et al. (2010): SVM classifiers of diabetes status from simple variables.

Steps, as the paper describes them:

1. Code each variable into [-1, 1] (race as -1, -0.5, 0, 0.5, 1; continuous values divided by
   a fixed number, for example age / 100).
2. Train on all cases and an equal number of randomly drawn non-cases.
3. Choose C and gamma with LIBSVM's grid.py: 5-fold cross-validated accuracy over
   log2(C) = -5, -3, ..., 15 and log2(gamma) = 3, 1, ..., -15.
4. Score new people by the SVM decision value; cutoff 0 for sensitivity and specificity.
5. Compare with a survey-weighted multiple logistic regression by the DeLong test of the AUCs.

LIBSVM is used through scikit-learn's SVC, which wraps it.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from typing import Iterable, Sequence

import numpy as np
from scipy import stats

# --- Feature coding -------------------------------------------------------------------------

#: Race and ethnicity codes from the paper's Methods ("-1, -0.5, 0, 0.5, 1 represents
#: non-Hispanic white, non-Hispanic black, Mexican American, other, other Hispanic").
RACE_CODES = {
    "nh_white": -1.0,
    "nh_black": -0.5,
    "mexican_american": 0.0,
    "other": 0.5,
    "other_hispanic": 1.0,
}

#: Divisors for the continuous variables. The paper gives age / 100 and says the others were
#: "divided by an appropriate number"; the rest are our choice (see the package README).
DIVISORS = {"age": 100.0, "weight": 200.0, "height": 200.0, "waist": 200.0, "bmi": 100.0}

#: The variables of each classification scheme (Results section of the paper).
SCHEME_FEATURES = {
    "I": ["family_history", "age", "race", "weight", "height", "waist", "bmi", "hypertension"],
    "II": [
        "family_history", "age", "race", "weight", "height", "waist", "bmi", "hypertension",
        "sex", "physical_activity",
    ],
}

BINARY = {"family_history", "hypertension", "physical_activity"}

#: grid.py defaults (LIBSVM 2.8x to 3.x).
GRID_LOG2C = tuple(range(-5, 16, 2))
GRID_LOG2G = tuple(range(3, -16, -2))
KERNELS = ("linear", "poly", "rbf", "sigmoid")
#: Iteration limit for the fits inside the grid search. Corners of the grid (large C with a
#: large gamma, or the polynomial kernel) can take millions of iterations to converge; they are
#: never the best point on the paper's data, and a limit keeps the search to minutes.
GRID_MAX_ITER = 1_000_000


def _yes_no(value) -> float:
    s = str(value).strip().lower()
    if s in {"1", "1.0", "yes", "y", "true"}:
        return 1.0
    if s in {"0", "0.0", "no", "n", "false"}:
        return -1.0
    raise ValueError(f"expected yes/no (1/0), got {value!r}")


def _sex(value) -> float:
    s = str(value).strip().lower()
    if s in {"male", "m", "1"}:
        return 1.0
    if s in {"female", "f", "2"}:
        return -1.0
    raise ValueError(f"expected male/female, got {value!r}")


def encode(records: Iterable[dict], scheme: str = "I") -> np.ndarray:
    """Code records (dicts with the scheme's variables) into the [-1, 1] feature matrix.

    Variables: family_history, hypertension, physical_activity (yes/no or 1/0); age (years);
    race (one of RACE_CODES); weight (kg); height (cm); waist (cm); bmi (kg/m2); sex
    (male/female).
    """
    if scheme not in SCHEME_FEATURES:
        raise ValueError(f"scheme must be 'I' or 'II', got {scheme!r}")
    names = SCHEME_FEATURES[scheme]
    rows = []
    for r in records:
        row = []
        for name in names:
            if name not in r or r[name] is None or str(r[name]).strip() == "":
                raise ValueError(f"missing value for {name!r}")
            v = r[name]
            if name in BINARY:
                row.append(_yes_no(v))
            elif name == "sex":
                row.append(_sex(v))
            elif name == "race":
                key = str(v).strip().lower()
                if key not in RACE_CODES:
                    raise ValueError(f"race must be one of {sorted(RACE_CODES)}, got {v!r}")
                row.append(RACE_CODES[key])
            else:
                row.append(float(v) / DIVISORS[name])
        rows.append(row)
    if not rows:
        raise ValueError("no records")
    return np.asarray(rows, dtype=float)


# --- Sampling -------------------------------------------------------------------------------


def split_train_test(y: Sequence[int], groups: Sequence, test_share: float = 0.2, seed: int = 0):
    """Random split with test_share of each group in the test set. Returns (train, test) indices."""
    y = np.asarray(y)
    groups = np.asarray(groups)
    rng = np.random.default_rng(seed)
    test = []
    for g in np.unique(groups):
        idx = np.flatnonzero(groups == g)
        n = int(round(test_share * len(idx)))
        test.extend(rng.choice(idx, size=n, replace=False))
    test = np.sort(np.asarray(test, dtype=int))
    train = np.setdiff1d(np.arange(len(y)), test)
    return train, test


def undersample(y: Sequence[int], seed: int = 0) -> np.ndarray:
    """Indices of all cases (y = 1) and an equal number of randomly drawn non-cases (y = -1 or 0)."""
    y = np.asarray(y)
    rng = np.random.default_rng(seed)
    pos = np.flatnonzero(y == 1)
    neg = np.flatnonzero(y != 1)
    if len(pos) == 0 or len(neg) < len(pos):
        raise ValueError("need at least one case and as many non-cases as cases")
    return np.sort(np.concatenate([pos, rng.choice(neg, size=len(pos), replace=False)]))


# --- SVM ------------------------------------------------------------------------------------


def _svc(kernel: str, C: float, gamma: float, tol: float = 1e-3, max_iter: int = 10_000_000):
    from sklearn.svm import SVC

    if kernel not in KERNELS:
        raise ValueError(f"kernel must be one of {KERNELS}")
    # LIBSVM defaults: degree 3, coef0 0, tolerance 1e-3, shrinking on. max_iter: LIBSVM 3.x
    # stops at 10 million iterations; LIBSVM 2.89 had no limit.
    return SVC(kernel=kernel, C=C, gamma=gamma, degree=3, coef0=0.0, tol=tol,
               cache_size=200, max_iter=max_iter)


def _cv_accuracy(X, y, kernel, C, gamma, folds, seed, max_iter=GRID_MAX_ITER):
    from sklearn.model_selection import StratifiedKFold

    skf = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)
    correct = 0
    for tr, te in skf.split(X, y):
        m = _svc(kernel, C, gamma, max_iter=max_iter).fit(X[tr], y[tr])
        correct += int((m.predict(X[te]) == y[te]).sum())
    return correct / len(y)


@dataclass
class GridResult:
    kernel: str
    C: float
    gamma: float
    cv_accuracy: float
    table: list = field(default_factory=list)  # (log2c, log2g, accuracy)


def grid_search(X, y, kernel: str = "rbf", log2c: Sequence[int] = GRID_LOG2C,
                log2g: Sequence[int] = GRID_LOG2G, folds: int = 5, seed: int = 0,
                n_jobs: int = 1, max_iter: int = GRID_MAX_ITER) -> GridResult:
    """grid.py: the (C, gamma) with the best `folds`-fold cross-validated accuracy.

    Ties go to the smaller C, then the larger gamma. The linear kernel has no gamma, so only
    C is searched for it. Each fit stops after `max_iter` iterations.
    """
    X = np.asarray(X, dtype=float)
    y = np.where(np.asarray(y) == 1, 1, -1)
    gs = [0] if kernel == "linear" else list(log2g)
    points = [(c, g) for c in log2c for g in gs]
    if n_jobs == 1:
        accs = [_cv_accuracy(X, y, kernel, 2.0**c, 2.0**g, folds, seed, max_iter) for c, g in points]
    else:
        from joblib import Parallel, delayed

        accs = Parallel(n_jobs=n_jobs)(
            delayed(_cv_accuracy)(X, y, kernel, 2.0**c, 2.0**g, folds, seed, max_iter)
            for c, g in points)
    table = [(c, g, a) for (c, g), a in zip(points, accs)]
    best = max(table, key=lambda t: (round(t[2], 12), -t[0], t[1]))
    return GridResult(kernel, 2.0 ** best[0], 2.0 ** best[1], best[2], table)


class SVMClassifier:
    """An SVM trained on a balanced sample, scored by its decision value (cutoff 0)."""

    def __init__(self, kernel: str = "rbf", C: float | None = None, gamma: float | None = None,
                 seed: int = 0, n_jobs: int = 1, tol: float = 1e-3):
        self.kernel, self.C, self.gamma, self.seed, self.n_jobs = kernel, C, gamma, seed, n_jobs
        self.tol = tol  # LIBSVM's stopping tolerance (-e), 1e-3 by default
        self.grid_ = None

    def fit(self, X, y, balance: bool = True):
        X = np.asarray(X, dtype=float)
        y = np.where(np.asarray(y) == 1, 1, -1)
        idx = undersample(y, self.seed) if balance else np.arange(len(y))
        self.train_index_ = idx
        Xb, yb = X[idx], y[idx]
        if self.C is None or (self.gamma is None and self.kernel != "linear"):
            self.grid_ = grid_search(Xb, yb, self.kernel, seed=self.seed, n_jobs=self.n_jobs)
            self.C, self.gamma = self.grid_.C, self.grid_.gamma
        self.model_ = _svc(self.kernel, self.C, self.gamma if self.gamma is not None else 1.0, self.tol)
        self.model_.fit(Xb, yb)
        return self

    def decision_function(self, X) -> np.ndarray:
        """Decision value of each row; positive means case. Sign follows LIBSVM's label +1."""
        return self.model_.decision_function(np.asarray(X, dtype=float))

    def predict(self, X, cutoff: float = 0.0) -> np.ndarray:
        return np.where(self.decision_function(X) > cutoff, 1, -1)


# --- Logistic regression --------------------------------------------------------------------


def weighted_logistic(X, y, weights=None, max_iter: int = 100, tol: float = 1e-10) -> np.ndarray:
    """Weighted maximum-likelihood logistic regression (Newton-Raphson).

    With survey weights this gives the point estimates of a design-based (SUDAAN, R survey)
    logistic regression. Returns beta with the intercept first.
    """
    X = np.asarray(X, dtype=float)
    y = (np.asarray(y) == 1).astype(float)
    w = np.ones(len(y)) if weights is None else np.asarray(weights, dtype=float)
    w = w / w.mean()
    A = np.column_stack([np.ones(len(y)), X])
    beta = np.zeros(A.shape[1])
    for _ in range(max_iter):
        eta = A @ beta
        p = 1.0 / (1.0 + np.exp(-eta))
        grad = A.T @ (w * (y - p))
        H = (A * (w * p * (1 - p))[:, None]).T @ A
        step = np.linalg.solve(H, grad)
        beta = beta + step
        if np.max(np.abs(step)) < tol:
            break
    return beta


def logistic_probability(X, beta) -> np.ndarray:
    A = np.column_stack([np.ones(len(X)), np.asarray(X, dtype=float)])
    return 1.0 / (1.0 + np.exp(-(A @ beta)))


# --- Evaluation -----------------------------------------------------------------------------


def roc_curve(y, score):
    """False-positive and true-positive rates at every threshold (highest score first)."""
    y = np.asarray(y) == 1
    s = np.asarray(score, dtype=float)
    order = np.argsort(-s, kind="mergesort")
    s, y = s[order], y[order]
    distinct = np.r_[np.flatnonzero(np.diff(s)), len(s) - 1]
    tp = np.cumsum(y)[distinct]
    fp = np.cumsum(~y)[distinct]
    return np.r_[0.0, fp / max(fp[-1], 1)], np.r_[0.0, tp / max(tp[-1], 1)]


def auc(y, score) -> float:
    """Area under the ROC curve (Mann-Whitney, ties counted one half)."""
    y = np.asarray(y) == 1
    r = stats.rankdata(np.asarray(score, dtype=float))
    n1, n0 = y.sum(), (~y).sum()
    if n1 == 0 or n0 == 0:
        raise ValueError("need both cases and non-cases")
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def _placements(pos, neg):
    # Structural components of DeLong et al. (1988), by midranks (Sun and Xu 2014).
    m, n = len(pos), len(neg)
    allr = stats.rankdata(np.r_[pos, neg])
    v10 = (allr[:m] - stats.rankdata(pos)) / n
    v01 = 1.0 - (allr[m:] - stats.rankdata(neg)) / m
    return v10, v01


def delong_test(y, score1, score2) -> dict:
    """DeLong test of two correlated AUCs on the same people (two-sided)."""
    y = np.asarray(y) == 1
    s1, s2 = np.asarray(score1, float), np.asarray(score2, float)
    a10, a01 = _placements(s1[y], s1[~y])
    b10, b01 = _placements(s2[y], s2[~y])
    auc1, auc2 = a10.mean(), b10.mean()
    s10 = np.cov(np.vstack([a10, b10]))
    s01 = np.cov(np.vstack([a01, b01]))
    S = s10 / len(a10) + s01 / len(a01)
    var = S[0, 0] + S[1, 1] - 2 * S[0, 1]
    z = (auc1 - auc2) / np.sqrt(var)
    return {"auc1": float(auc1), "auc2": float(auc2), "z": float(z),
            "p": float(2 * stats.norm.sf(abs(z)))}


def classification_metrics(y, score, cutoff: float = 0.0) -> dict:
    """Sensitivity, specificity, PPV, NPV at `cutoff` (score above it = case), and the AUC."""
    y = np.asarray(y) == 1
    pred = np.asarray(score, dtype=float) > cutoff
    tp, fn = int((pred & y).sum()), int((~pred & y).sum())
    tn, fp = int((~pred & ~y).sum()), int((pred & ~y).sum())

    def ratio(a, b):
        return a / (a + b) if a + b else float("nan")

    return {"sensitivity": ratio(tp, fn), "specificity": ratio(tn, fp), "ppv": ratio(tp, fp),
            "npv": ratio(tn, fn), "auc": auc(y, score), "tp": tp, "fp": fp, "tn": tn, "fn": fn}


# --- Files ----------------------------------------------------------------------------------


def read_records(path) -> list[dict]:
    """Read a CSV with one person per row (columns named as in `encode`)."""
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def labels(records: Iterable[dict], column: str = "case") -> np.ndarray:
    """1 for cases, -1 for non-cases, from a 1/0 column."""
    return np.array([1 if _yes_no(r[column]) > 0 else -1 for r in records])

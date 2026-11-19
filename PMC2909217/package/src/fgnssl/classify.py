"""Feature scaling, the SVM baseline and ROC curves used with the SSL classifier."""

from __future__ import annotations

import numpy as np

SVM_GRID = {"C": [2.0 ** k for k in range(-1, 11, 2)], "gamma": [2.0 ** k for k in range(-9, 3, 2)]}


def scale_features(F: np.ndarray) -> np.ndarray:
    """sign(x) log(1 + |x|) of each feature, then zero mean and unit variance per column.

    The paper does not say how features were scaled; the network properties span six orders of
    magnitude, so without a log transform a few hubs set every distance.
    """
    F = np.asarray(F, dtype=float)
    if not np.all(np.isfinite(F)):
        raise ValueError("features must be finite")
    G = np.sign(F) * np.log1p(np.abs(F))
    sd = G.std(axis=0)
    sd[sd == 0] = 1.0
    return (G - G.mean(axis=0)) / sd


def svm_scores(X_train, y_train, X_test, C: float | None = None, gamma: float | None = None,
               cv: int = 3, seed: int = 0):
    """RBF SVM (LIBSVM through scikit-learn). Without C and gamma, a grid search with cv-fold CV on
    the training set picks them (geometric grid SVM_GRID). Returns (decision values, C, gamma)."""
    from sklearn.model_selection import GridSearchCV, StratifiedKFold
    from sklearn.svm import SVC

    if C is None or gamma is None:
        search = GridSearchCV(SVC(kernel="rbf"), SVM_GRID, scoring="roc_auc",
                              cv=StratifiedKFold(cv, shuffle=True, random_state=seed), n_jobs=1)
        search.fit(X_train, y_train)
        C, gamma = search.best_params_["C"], search.best_params_["gamma"]
    model = SVC(kernel="rbf", C=C, gamma=gamma).fit(X_train, y_train)
    return model.decision_function(X_test), float(C), float(gamma)


def roc_curve(scores: np.ndarray, labels: np.ndarray):
    """False and true positive rates at every distinct threshold, from (0, 0) to (1, 1)."""
    scores = np.asarray(scores, dtype=float)
    labels = np.asarray(labels).astype(bool)
    order = np.argsort(-scores, kind="mergesort")
    s, l = scores[order], labels[order]
    tp = np.cumsum(l)
    fp = np.cumsum(~l)
    last = np.r_[np.where(np.diff(s) != 0)[0], len(s) - 1]
    tpr = np.r_[0.0, tp[last] / max(l.sum(), 1)]
    fpr = np.r_[0.0, fp[last] / max((~l).sum(), 1)]
    return fpr, tpr


def auc(fpr: np.ndarray, tpr: np.ndarray) -> float:
    return float(np.trapezoid(tpr, fpr))


def tpr_at(fpr: np.ndarray, tpr: np.ndarray, x: float) -> float:
    """True positive rate of the ROC step curve at false positive rate x (the highest TPR reached)."""
    return float(np.max(tpr[fpr <= x + 1e-12]))

"""Divide-and-conquer k-nearest neighbours (DC-kNN, Lee et al. 2008) and the possibility degree (Lee et al. 2013).

Dividing: one kNN per feature set (subvector). Choosing: the k = 5 nearest training
proteins in that subvector (Euclidean distance; a protein is never its own neighbour).
Synthesising: for location l, mu_l = [ (1/k) sum_m n_ml phi_m ]^(1/sqrt(M)), where n_ml is
the number of the k neighbours in subvector m that have location l, phi_m the AUC of
subvector m alone, and M the number of selected subvectors. The subvectors for each
location are chosen by forward selection on the AUC.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
from scipy.stats import rankdata

K = 5


def auc(scores: np.ndarray, positive: np.ndarray) -> float:
    """Area under the ROC curve with ties counted half (Mann-Whitney)."""
    s = np.asarray(scores, dtype=float)
    y = np.asarray(positive, dtype=bool)
    npos, nneg = int(y.sum()), int((~y).sum())
    if npos == 0 or nneg == 0:
        return float("nan")
    ranks = rankdata(s)
    return float((ranks[y].sum() - npos * (npos + 1) / 2.0) / (npos * nneg))


def roc_curve(scores: np.ndarray, positive: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """False and true positive rates at every distinct threshold, from (0, 0) to (1, 1)."""
    s = np.asarray(scores, dtype=float)
    y = np.asarray(positive, dtype=bool)
    order = np.argsort(-s, kind="mergesort")
    s, y = s[order], y[order]
    distinct = np.r_[np.flatnonzero(np.diff(s)), len(s) - 1]
    tp = np.cumsum(y)[distinct]
    fp = np.cumsum(~y)[distinct]
    return np.r_[0.0, fp / max(fp[-1], 1)], np.r_[0.0, tp / max(tp[-1], 1)]


def neighbours(query: np.ndarray, train: np.ndarray, k: int = K, self_index: np.ndarray | None = None,
               chunk: int = 1024) -> np.ndarray:
    """Indices into train of the k nearest rows to each query row (Euclidean).

    self_index[i] is the train row of query i (or -1); it is never returned as a neighbour.
    """
    q = np.asarray(query, dtype=np.float64)
    t = np.asarray(train, dtype=np.float64)
    tn = (t * t).sum(axis=1)
    out = np.empty((len(q), k), dtype=np.int64)
    for s in range(0, len(q), chunk):
        qq = q[s:s + chunk]
        d = tn[None, :] - 2.0 * (qq @ t.T)
        if self_index is not None:
            si = self_index[s:s + chunk]
            rows = np.flatnonzero(si >= 0)
            d[rows, si[rows]] = np.inf
        part = np.argpartition(d, k, axis=1)[:, :k]
        dd = np.take_along_axis(d, part, axis=1)
        # stable order by distance, then by train index, so ties are reproducible
        o = np.lexsort((part, dd), axis=1)
        out[s:s + chunk] = np.take_along_axis(part, o, axis=1)
    return out


def label_counts(nbrs: np.ndarray, train_labels: np.ndarray) -> np.ndarray:
    """n_ml for every query: (n_query, L) counts of the k neighbours that carry each location."""
    lab = np.asarray(train_labels, dtype=np.int16)
    return lab[nbrs].sum(axis=1)


def confidence(counts: Mapping[str, np.ndarray], selected: Sequence[str], weights: Mapping[str, float],
               location: int, k: int = K) -> np.ndarray:
    """mu_l for one location from the selected subvectors."""
    tot = sum(counts[m][:, location] * weights[m] for m in selected) / k
    return np.power(tot, 1.0 / np.sqrt(len(selected)))


def forward_select(counts: Mapping[str, np.ndarray], labels: np.ndarray, location: int, rows: np.ndarray,
                   candidates: Sequence[str], k: int = K, tol: float = 1e-6, max_sets: int | None = None
                   ) -> tuple[list[str], dict[str, float], list[float]]:
    """Forward selection of subvectors for one location, scored by AUC on the given rows.

    Returns the selected subvectors, the single-subvector AUCs (phi_m, on the same rows), and the
    AUC after each step. Selection stops when no remaining subvector raises the AUC by more than tol.
    """
    y = np.asarray(labels[rows, location], dtype=bool)
    single = {m: auc(counts[m][rows, location], y) for m in candidates}
    selected: list[str] = []
    path: list[float] = []
    best = -np.inf
    remaining = list(candidates)
    while remaining and (max_sets is None or len(selected) < max_sets):
        trial = []
        for m in remaining:
            c = confidence({x: counts[x][rows] for x in selected + [m]}, selected + [m], single, location, k)
            trial.append((auc(c, y), m))
        score, m = max(trial, key=lambda t: (t[0], -candidates.index(t[1])))
        if score <= best + tol:
            break
        best = score
        selected.append(m)
        remaining.remove(m)
        path.append(score)
    return selected, single, path


def possibility(c: np.ndarray, positive_scores: np.ndarray, negative_scores: np.ndarray) -> np.ndarray:
    """Degree of possibility P_l(c) from the gold-standard confidence distributions (Lee et al. 2013).

    Between the minimum of the positive scores and the maximum of the negative scores,
    P = (share of positives in [min_pos, c] + share of negatives in [min_pos, c]) / 2, both shares taken
    among the gold-standard scores inside [min_pos, max_neg]. P = 0 below min_pos and 1 above max_neg.
    """
    c = np.asarray(c, dtype=float)
    pos = np.sort(np.asarray(positive_scores, dtype=float))
    neg = np.sort(np.asarray(negative_scores, dtype=float))
    lo, hi = pos[0], neg[-1]
    out = np.where(c > hi, 1.0, 0.0)
    if hi <= lo:  # the gold standard is separated: everything above the negatives is possible
        return np.where(c > hi, 1.0, 0.0)
    p_in = pos[(pos >= lo) & (pos <= hi)]
    n_in = neg[(neg >= lo) & (neg <= hi)]
    mid = (c >= lo) & (c <= hi)
    dp = np.searchsorted(p_in, c[mid], side="right") / max(len(p_in), 1)
    dn = np.searchsorted(n_in, c[mid], side="right") / max(len(n_in), 1)
    out[mid] = (dp + dn) / 2.0
    return out


def null_threshold(negative_scores: np.ndarray, alpha: float = 0.005) -> float:
    """Confidence above which a share alpha of the gold-standard negatives lie (the paper's P < 0.005)."""
    return float(np.quantile(np.asarray(negative_scores, dtype=float), 1.0 - alpha, method="higher"))

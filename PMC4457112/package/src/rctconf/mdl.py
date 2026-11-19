"""Fayyad and Irani (1993) minimum-description-length discretization of one numeric attribute.

Cohen et al. (2015) split the author count into ranges by "recursive partitioning ... using a minimum
description length approach" (their ref. 16, Fayyad and Irani) and used each range as a binary feature.
"""

from __future__ import annotations

import math

import numpy as np


def _entropy(counts: np.ndarray) -> float:
    n = counts.sum()
    if n == 0:
        return 0.0
    p = counts[counts > 0] / n
    return float(-(p * np.log2(p)).sum())


def mdl_cut_points(values, labels) -> np.ndarray:
    """Cut points of the Fayyad-Irani MDLP for a numeric attribute and binary (or class) labels.

    Returns sorted cut points c; a value v falls in bin searchsorted(c, v, side="right").
    Candidate cuts lie halfway between adjacent distinct values.
    """
    v = np.asarray(values, dtype=float)
    y = np.asarray(labels)
    if v.shape != y.shape:
        raise ValueError("values and labels differ in length")
    if v.size == 0:
        return np.array([])
    classes, yi = np.unique(y, return_inverse=True)
    k_all = len(classes)
    uniq, vi = np.unique(v, return_inverse=True)
    # class counts per distinct value
    table = np.zeros((len(uniq), k_all), dtype=np.int64)
    np.add.at(table, (vi, yi), 1)
    cuts: list[float] = []

    def split(lo: int, hi: int) -> None:  # distinct-value rows lo..hi-1
        sub = table[lo:hi]
        if hi - lo < 2:
            return
        tot = sub.sum(axis=0)
        n = tot.sum()
        ent = _entropy(tot)
        cum = np.cumsum(sub, axis=0)[:-1]
        best, best_i = math.inf, -1
        for i, left in enumerate(cum):
            right = tot - left
            nl, nr = left.sum(), right.sum()
            e = (nl * _entropy(left) + nr * _entropy(right)) / n
            if e < best:
                best, best_i = e, i
        left = cum[best_i]
        right = tot - left
        gain = ent - best
        k, k1, k2 = (int((c > 0).sum()) for c in (tot, left, right))
        delta = math.log2(3**k - 2) - (k * ent - k1 * _entropy(left) - k2 * _entropy(right))
        if gain <= (math.log2(n - 1) + delta) / n:
            return
        cut = lo + best_i  # cut after distinct value index cut
        cuts.append((uniq[cut] + uniq[cut + 1]) / 2)
        split(lo, cut + 1)
        split(cut + 1, hi)

    split(0, len(uniq))
    return np.array(sorted(cuts))

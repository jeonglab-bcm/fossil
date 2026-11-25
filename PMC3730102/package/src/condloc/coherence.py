"""Expression coherence of interacting proteins (Lee et al. 2013, Methods).

Phi(a, b) = -log2 Psi[ min(med(a), med(b)) / MEDIAN * rho(a, b) ]

rho is the Pearson correlation of the two genes over the samples of one study, med the
gene's median expression, MEDIAN the median of all gene medians, and Psi(x) the P-value of
x against the distribution of the same quantity over all interacting pairs. We take Psi as
the upper-tail share (pairs with a value at least x, the pair itself included), so a pair
that is both highly expressed and strongly co-expressed scores high. A pair that cannot be
scored gets the median score of the scored links of a or b, else the network median.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def quantile_normalize(x: np.ndarray) -> np.ndarray:
    """Quantile normalisation of the columns (samples) of a genes x samples matrix without missing values."""
    order = np.argsort(x, axis=0)
    ranked = np.sort(x, axis=0).mean(axis=1)
    out = np.empty_like(x, dtype=float)
    for j in range(x.shape[1]):
        out[order[:, j], j] = ranked
    return out


def knn_impute(x: np.ndarray, k: int = 10, max_missing: float = 0.3) -> tuple[np.ndarray, np.ndarray]:
    """Impute missing values of genes with less than max_missing missing from the k most similar complete genes.

    Returns the matrix of kept genes and the boolean mask of kept rows (genes with more missing are dropped).
    """
    miss = np.isnan(x)
    frac = miss.mean(axis=1)
    keep = frac < max_missing
    x = x[keep].copy()
    miss = miss[keep]
    complete = ~miss.any(axis=1)
    ref = x[complete]
    for i in np.flatnonzero(~complete):
        obs = ~miss[i]
        d = np.sqrt(np.mean((ref[:, obs] - x[i, obs]) ** 2, axis=1))
        nn = np.argsort(d)[:k]
        x[i, ~obs] = ref[nn][:, ~obs].mean(axis=0)
    return x, keep


def edge_statistic(expr: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """min(med(a), med(b)) / MEDIAN * pearson(a, b) for index arrays a, b into the rows of expr."""
    med = np.median(expr, axis=1)
    big = np.median(med)
    z = expr - expr.mean(axis=1, keepdims=True)
    sd = np.sqrt((z * z).sum(axis=1))
    sd[sd == 0] = np.inf
    z = z / sd[:, None]
    r = np.einsum("ij,ij->i", z[a], z[b])
    return np.minimum(med[a], med[b]) / big * r


def coherence(expr: np.ndarray, genes: Sequence[str], edges: Sequence[tuple[str, str]]) -> np.ndarray:
    """Phi for each edge (NaN where either gene is not measured in this study)."""
    pos = {g: i for i, g in enumerate(genes)}
    a = np.array([pos.get(u, -1) for u, _ in edges])
    b = np.array([pos.get(v, -1) for _, v in edges])
    ok = (a >= 0) & (b >= 0)
    out = np.full(len(edges), np.nan)
    if not ok.any():
        return out
    x = edge_statistic(expr, a[ok], b[ok])
    # Psi(x): share of scored links with a value >= x
    srt = np.sort(x)
    ge = len(x) - np.searchsorted(srt, x, side="left")
    out[ok] = -np.log2(ge / len(x))
    return out


def fill_missing(phi: np.ndarray, edges: Sequence[tuple[str, str]]) -> np.ndarray:
    """Replace NaN scores by the median score of the scored links of either end, else the overall median."""
    phi = np.asarray(phi, dtype=float).copy()
    scored = ~np.isnan(phi)
    if not scored.any():
        return np.zeros_like(phi)
    per: dict[str, list[float]] = {}
    for (u, v), p, s in zip(edges, phi, scored):
        if s:
            per.setdefault(u, []).append(p)
            per.setdefault(v, []).append(p)
    overall = float(np.median(phi[scored]))
    for i in np.flatnonzero(~scored):
        u, v = edges[i]
        vals = per.get(u, []) + per.get(v, [])
        phi[i] = float(np.median(vals)) if vals else overall
    return phi

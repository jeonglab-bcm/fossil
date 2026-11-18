"""Gene and junction expression: upper-quartile gene RPKM, TMM factors, junction fold changes.

Additional file 1: gene RPKM with upper-quartile normalisation over the longest RefSeq model of each
gene symbol; junction reads TMM-normalised (edgeR); junction RPKM normalised to the KO/WT gene RPKM
ratio; fold change = RPKM KO / RPKM WT; >= 2 is up, <= 1/2 ("<= -2" in the paper's signed notation)
is down; junction evidence = more than 2 reads in WT or KO.
"""

from __future__ import annotations

import math

import numpy as np

EVIDENCE_READS = 3  # "more than 2 reads to either WT or KO"; Fig. 2a: "a minimum of three reads"
FOLD = 2.0


def tmm_factors(counts: np.ndarray, ref_column: int | None = None, logratio_trim: float = 0.3,
                sum_trim: float = 0.05, a_cutoff: float = -1e10) -> np.ndarray:
    """TMM normalisation factors of the columns of a count matrix, as edgeR's calcNormFactors.

    Follows edgeR (Robinson and Oshlack 2010): the reference is the column whose upper-quartile
    factor is closest to their mean; M and A values of genes with counts in both libraries are
    trimmed 30% and 5%, weighted by the inverse asymptotic variance, and the factors are scaled to
    a geometric mean of one.
    """
    x = np.asarray(counts, dtype=float)
    lib = x.sum(axis=0)
    if ref_column is None:
        f75 = np.array([np.quantile(x[:, j], 0.75) for j in range(x.shape[1])]) / lib
        ref_column = int(np.argmin(np.abs(f75 - f75.mean())))
    ref = x[:, ref_column]
    nref = lib[ref_column]
    f = np.ones(x.shape[1])
    for j in range(x.shape[1]):
        obs = x[:, j]
        nobs = lib[j]
        ok = (obs > 0) & (ref > 0)
        lo, lr = obs[ok] / nobs, ref[ok] / nref
        m = np.log2(lo / lr)
        a = 0.5 * np.log2(lo * lr)
        v = (nobs - obs[ok]) / nobs / obs[ok] + (nref - ref[ok]) / nref / ref[ok]
        keep = np.isfinite(m) & np.isfinite(a) & (a > a_cutoff)
        m, a, v = m[keep], a[keep], v[keep]
        if m.size == 0 or np.max(np.abs(m)) < 1e-6:
            continue
        n = m.size
        lo_l = math.floor(n * logratio_trim) + 1
        hi_l = n + 1 - lo_l
        lo_s = math.floor(n * sum_trim) + 1
        hi_s = n + 1 - lo_s
        rm = _rank(m)
        ra = _rank(a)
        sel = (rm >= lo_l) & (rm <= hi_l) & (ra >= lo_s) & (ra <= hi_s)
        f[j] = 2 ** (np.sum(m[sel] / v[sel]) / np.sum(1 / v[sel]))
    return f / np.exp(np.mean(np.log(f)))


def _rank(v: np.ndarray) -> np.ndarray:
    """Ranks with ties averaged (R's rank)."""
    order = np.argsort(v, kind="mergesort")
    ranks = np.empty(v.size)
    sv = v[order]
    i = 0
    while i < v.size:
        j = i
        while j + 1 < v.size and sv[j + 1] == sv[i]:
            j += 1
        ranks[order[i : j + 1]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def upper_quartile_rpkm(counts: np.ndarray, lengths: np.ndarray) -> np.ndarray:
    """RPKM with the upper quartile of non-zero counts as the library size (Cufflinks -N)."""
    counts = np.asarray(counts, dtype=float)
    out = np.zeros_like(counts)
    for j in range(counts.shape[1]):
        c = counts[:, j]
        uq = np.quantile(c[c > 0], 0.75)
        out[:, j] = c / (lengths / 1e3) / uq * 1e3
    return out


def regulation(fc: float, fold: float = FOLD) -> str:
    """'up', 'down' or 'unregulated' from a KO/WT fold change."""
    if fc >= fold:
        return "up"
    if fc <= 1 / fold:
        return "down"
    return "unregulated"


def junction_fold_change(wt_reads: float, ko_reads: float, wt_lib: float, ko_lib: float,
                         gene_fc: float | None = None, pseudo: float = 0.0) -> float:
    """KO/WT fold change of a junction from TMM-scaled library sizes, divided by the gene's KO/WT fold
    change when one is given. A junction with no WT reads has an infinite fold change."""
    wt = (wt_reads + pseudo) / wt_lib
    ko = (ko_reads + pseudo) / ko_lib
    if wt == 0:
        fc = math.inf if ko > 0 else 1.0
    else:
        fc = ko / wt
    if gene_fc is not None and gene_fc > 0 and math.isfinite(gene_fc):
        fc = fc / gene_fc
    return fc

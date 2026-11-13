"""Rates of allele frequency change between consecutive samples (Neher and Leitner 2010).

Each site of a codon alignment contributes |dp| / dt for every pair of consecutive samples whose
sizes both exceed ``min_size``. Cases, as in the paper's Methods:

1. biallelic and gap free at t_i (no condition at t_{i+1}): dp is the change of the minor allele's
   frequency; if a third nucleotide appears at t_{i+1}, both t_i alleles are added;
2. one nucleotide at t_i, two at t_{i+1}: dp is the new allele's frequency;
3. one nucleotide at either time, and they differ: dp = 1.

An observation is synonymous when the two nucleotides give the same amino acid in the consensus
codon of the earlier sample.
"""

from __future__ import annotations

import numpy as np

from .align import CODON_TABLE
from .recombination import NUCS, as_array

#: Columns of a rate table (one row per observation).
RATE_KEYS = ("patient", "t0", "t1", "pos", "rate", "dp", "dt", "synonymous", "case", "M0", "M1")


def consensus(block: np.ndarray) -> np.ndarray:
    """Most common byte of each column of an alignment block."""
    out = np.empty(block.shape[1], dtype=np.uint8)
    for j in range(block.shape[1]):
        vals, cnt = np.unique(block[:, j], return_counts=True)
        out[j] = vals[int(np.argmax(cnt))]
    return out


def same_amino_acid(cons: np.ndarray, pos: int, x: int, y: int):
    """Whether nucleotides x and y at column ``pos`` give one amino acid in the consensus codon.

    Returns None when that codon holds a gap or another character.
    """
    start = pos - pos % 3
    codon = bytearray(cons[start : start + 3].tobytes())
    if len(codon) < 3 or any(c not in b"ACGT" for c in codon):
        return None
    k = pos % 3
    codon[k] = x
    first = CODON_TABLE[codon.decode()]
    codon[k] = y
    return first == CODON_TABLE[codon.decode()]


def frequency_changes(aln, times, patient: int = 0, min_size: int = 10) -> dict[str, np.ndarray]:
    """Rates |dp|/dt of one patient. ``times`` are generations; ``aln`` is a codon alignment."""
    X = aln if isinstance(aln, np.ndarray) else as_array(aln)
    times = np.asarray(times, dtype=float)
    rows: dict[str, list] = {k: [] for k in RATE_KEYS}

    def add(t0, t1, pos, dp, syn, case, M0, M1):
        for key, val in zip(RATE_KEYS, (patient, t0, t1, pos, abs(dp) / (t1 - t0), abs(dp),
                                        t1 - t0, syn, case, M0, M1)):
            rows[key].append(val)

    tps = np.unique(times)
    for t0, t1 in zip(tps[:-1], tps[1:]):
        A, B = X[times == t0], X[times == t1]
        M0, M1 = A.shape[0], B.shape[0]
        if M0 <= min_size or M1 <= min_size:
            continue
        cons = consensus(A)
        for j in range(X.shape[1]):
            va, na = np.unique(A[:, j], return_counts=True)
            if not np.isin(va, NUCS).all():
                continue
            col1 = B[:, j]
            if len(va) == 2:
                order = np.argsort(na, kind="stable")
                minor, major = int(va[order[0]]), int(va[order[1]])
                syn = same_amino_acid(cons, j, minor, major)
                if syn is None:
                    continue
                start = {int(v): n / M0 for v, n in zip(va, na)}
                third = np.isin(col1, NUCS) & (col1 != minor) & (col1 != major)
                for v in ((minor, major) if third.any() else (minor,)):
                    add(t0, t1, j, np.count_nonzero(col1 == v) / M1 - start[v], syn, 1, M0, M1)
            elif len(va) == 1:
                vb, _ = np.unique(col1, return_counts=True)
                if not np.isin(vb, NUCS).all():
                    continue
                old = int(va[0])
                if len(vb) == 2 and old in vb:
                    new = int(vb[0] if int(vb[1]) == old else vb[1])
                    syn = same_amino_acid(cons, j, old, new)
                    if syn is not None:
                        add(t0, t1, j, np.count_nonzero(col1 == new) / M1, syn, 2, M0, M1)
                elif len(vb) == 1 and int(vb[0]) != old:
                    syn = same_amino_acid(cons, j, old, int(vb[0]))
                    if syn is not None:
                        add(t0, t1, j, 1.0, syn, 3, M0, M1)
    return {k: np.asarray(v) for k, v in rows.items()}


def concat_rates(tables) -> dict[str, np.ndarray]:
    tables = list(tables)
    return {k: np.concatenate([np.asarray(t[k]) for t in tables]) for k in RATE_KEYS}


def linked_mask(rates, fast: float = 0.002, window: float = 100.0) -> np.ndarray:
    """Synonymous observations closer than ``window`` columns to a non-synonymous one of the same
    patient and interval whose rate exceeds ``fast`` (the paper's hitch-hiking filter)."""
    syn = np.asarray(rates["synonymous"]).astype(bool)
    pos = np.asarray(rates["pos"], dtype=float)
    out = np.zeros(len(syn), bool)
    drivers: dict = {}
    for i in np.where((~syn) & (np.asarray(rates["rate"]) > fast))[0]:
        drivers.setdefault((rates["patient"][i], rates["t0"][i]), []).append(pos[i])
    for i in np.where(syn)[0]:
        near = drivers.get((rates["patient"][i], rates["t0"][i]))
        if near and float(np.min(np.abs(np.asarray(near) - pos[i]))) < window:
            out[i] = True
    return out


def ks(x, y) -> tuple[float, float]:
    """The paper's KS test: statistic D, and the p value from SciPy's two sample test.

    The paper divides D by sqrt(1/m_s + 1/m_n); SciPy's ``ks_2samp`` uses the same scaling inside
    its asymptotic p value, so the p value is taken from it directly.
    """
    from scipy.stats import ks_2samp

    r = ks_2samp(np.asarray(x, float), np.asarray(y, float))
    return float(r.statistic), float(r.pvalue)


def cumulative(rates_subset, grid):
    """Share of observations at or below each point of ``grid`` (the curves of Figure 4)."""
    x = np.sort(np.asarray(rates_subset, float))
    return np.searchsorted(x, np.asarray(grid, float), side="right") / max(len(x), 1)


def share_above(rates_subset, threshold: float) -> float:
    """Share of observations faster than ``threshold`` per generation."""
    x = np.asarray(rates_subset, float)
    return float(np.mean(x > threshold)) if len(x) else float("nan")


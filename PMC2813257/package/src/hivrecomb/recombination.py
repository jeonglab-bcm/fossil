"""Recombination rate from the reappearance of missing haplotypes (Neher and Leitner 2010).

For each pair of consecutive samples (t_i, t_{i+1}) of one patient and each pair of sites that are
biallelic and gapless at t_i, with both alleles seen at least ``min_count`` times, and that show
exactly three of the four possible two-site haplotypes at t_i, we ask whether the fourth (missing)
haplotype is seen at t_{i+1}. Its frequency rises with distance times elapsed time; fitting

    f(d dt) = c0 + c1 (1 - exp(-c2 d dt))

gives the recombination rate rho = c1 c2 / (<M pA pB> - c0)  (Eq. 3 of the paper).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

GAP = ord("-")
NUCS = np.frombuffer(b"ACGT", dtype=np.uint8)

#: Keys of an event table (one row per qualifying pair of sites and pair of consecutive samples).
EVENT_KEYS = ("patient", "t0", "t1", "pos1", "pos2", "d", "dt", "found", "other", "M0", "M1", "pA", "pB", "qA", "qB")


def as_array(seqs) -> np.ndarray:
    """(n, L) uint8 array from equal-length aligned sequences (strings or bytes)."""
    rows = [s.encode("ascii") if isinstance(s, str) else bytes(s) for s in seqs]
    if not rows:
        return np.zeros((0, 0), dtype=np.uint8)
    if len({len(r) for r in rows}) != 1:
        raise ValueError("sequences are not aligned (unequal lengths)")
    return np.frombuffer(b"".join(rows), dtype=np.uint8).reshape(len(rows), -1).copy()


def _biallelic_sites(block: np.ndarray, min_count: int):
    """Columns of ``block`` with exactly two nucleotides, no gap or other character, both seen
    at least ``min_count`` times. Returns positions, allele 1 and allele 2 (allele 1 the commoner)."""
    pos, a1, a2 = [], [], []
    for j in range(block.shape[1]):
        col = block[:, j]
        vals, cnt = np.unique(col, return_counts=True)
        if len(vals) != 2 or not np.isin(vals, NUCS).all():
            continue
        if cnt.min() < min_count:
            continue
        order = np.argsort(-cnt, kind="stable")
        pos.append(j)
        a1.append(vals[order[0]])
        a2.append(vals[order[1]])
    return np.array(pos, dtype=int), np.array(a1, dtype=np.uint8), np.array(a2, dtype=np.uint8)


def pair_events(aln, times, patient: int = 0, min_count: int = 3) -> dict[str, np.ndarray]:
    """Missing-haplotype events of one patient.

    ``aln``: aligned nucleotide sequences ((n, L) uint8 array or a list of strings); ``times``:
    sampling time of each sequence in generations. Returns a table (dict of equal-length arrays)
    with, for each qualifying pair of sites at each pair of consecutive samples: the positions,
    distance ``d`` (alignment columns), ``dt`` (generations), ``found`` (the missing haplotype is
    seen at t_{i+1}), ``other`` (a sequence at t_{i+1} carries, at one of the two sites, a
    nucleotide not seen at t_i), the sample sizes ``M0`` and ``M1`` and the t_i frequencies
    ``pA`` and ``pB`` of the two alleles that form the missing haplotype, and the t_i
    frequencies ``qA`` and ``qB`` of the minor allele at each site.
    """
    X = aln if isinstance(aln, np.ndarray) else as_array(aln)
    times = np.asarray(times, dtype=float)
    if X.shape[0] != times.shape[0]:
        raise ValueError("one time per sequence is needed")
    tps = np.unique(times)
    out = {k: [] for k in EVENT_KEYS}
    for t0, t1 in zip(tps[:-1], tps[1:]):
        A, B = X[times == t0], X[times == t1]
        pos, a1, a2 = _biallelic_sites(A, min_count)
        K = len(pos)
        if K < 2:
            continue
        M0, M1 = A.shape[0], B.shape[0]
        # allele indicators at t_i (allele 1 = column 0, allele 2 = column 1)
        H = [(A[:, pos] == a1).astype(np.int32), (A[:, pos] == a2).astype(np.int32)]
        G = [(B[:, pos] == a1).astype(np.int32), (B[:, pos] == a2).astype(np.int32)]
        freq = [H[0].sum(0) / M0, H[1].sum(0) / M0]
        # site carries a nucleotide at t_{i+1} that was not seen at t_i (gaps not counted)
        newal = (np.isin(B[:, pos], NUCS) & (B[:, pos] != a1) & (B[:, pos] != a2)).any(0)
        n = {(x, y): H[x].T @ H[y] for x in (0, 1) for y in (0, 1)}
        g = {(x, y): (G[x].T @ G[y]) > 0 for x in (0, 1) for y in (0, 1)}
        present = sum((n[k] > 0).astype(int) for k in n)
        iu, ju = np.triu_indices(K, 1)
        sel = present[iu, ju] == 3
        iu, ju = iu[sel], ju[sel]
        if len(iu) == 0:
            continue
        found = np.zeros(len(iu), bool)
        pA = np.zeros(len(iu))
        pB = np.zeros(len(iu))
        for (x, y), cnt in n.items():
            miss = cnt[iu, ju] == 0
            found[miss] = g[(x, y)][iu[miss], ju[miss]]
            pA[miss] = freq[x][iu[miss]]
            pB[miss] = freq[y][ju[miss]]
        m = len(iu)
        out["patient"].append(np.full(m, patient))
        out["t0"].append(np.full(m, t0))
        out["t1"].append(np.full(m, t1))
        out["pos1"].append(pos[iu])
        out["pos2"].append(pos[ju])
        out["d"].append(pos[ju] - pos[iu])
        out["dt"].append(np.full(m, t1 - t0))
        out["found"].append(found)
        out["other"].append(newal[iu] | newal[ju])
        out["M0"].append(np.full(m, M0))
        out["M1"].append(np.full(m, M1))
        out["pA"].append(pA)
        out["pB"].append(pB)
        out["qA"].append(freq[1][iu])
        out["qB"].append(freq[1][ju])
    return {k: (np.concatenate(v) if v else np.zeros(0)) for k, v in out.items()}


def concat_events(tables) -> dict[str, np.ndarray]:
    tables = list(tables)
    return {k: np.concatenate([t[k] for t in tables]) for k in EVENT_KEYS}


@dataclass
class Binned:
    """Probability of the missing haplotype per bin, with the paper's error bars."""

    edges: np.ndarray
    centers: np.ndarray
    pairs: np.ndarray  # pairs in the bin
    counts: np.ndarray  # pairs whose missing (or other) haplotype was found
    p: np.ndarray
    err: np.ndarray  # p * counts**-0.5 (Methods: "the product of the estimated value and 1 +- #counts^-0.5")


def bin_events(x, hit, edges) -> Binned:
    x = np.asarray(x, float)
    hit = np.asarray(hit, bool)
    edges = np.asarray(edges, float)
    idx = np.digitize(x, edges) - 1
    nb = len(edges) - 1
    ok = (idx >= 0) & (idx < nb)
    pairs = np.bincount(idx[ok], minlength=nb)
    counts = np.bincount(idx[ok], weights=hit[ok].astype(float), minlength=nb)
    with np.errstate(invalid="ignore", divide="ignore"):
        p = counts / pairs
        err = p / np.sqrt(counts)
    return Binned(edges, 0.5 * (edges[1:] + edges[:-1]), pairs, counts, p, err)


def saturation(x, c0, c1, c2):
    """Eq. 5: f(d dt) = c0 + c1 (1 - exp(-c2 d dt))."""
    return c0 + c1 * (1.0 - np.exp(-c2 * np.asarray(x, float)))


@dataclass
class Fit:
    c0: float
    c1: float
    c2: float
    MpApB: float
    rho: float
    n_pairs: int
    binned: Binned = field(repr=False)


def fit_saturation(binned: Binned, p0=(0.1, 0.25, 4e-5), weights: str = "error") -> tuple[float, float, float]:
    """Weighted least squares fit of Eq. 5 to the bins that have at least one count.

    ``weights``: ``error`` divides each residual by the bin's error bar p / sqrt(counts);
    ``relative`` divides it by the relative uncertainty 1 / sqrt(counts). f is a probability, so
    c0 and c1 are bounded to [0, 1] and c2 to non-negative values.
    """
    from scipy.optimize import curve_fit

    ok = binned.counts > 0
    sigma = binned.err[ok] if weights == "error" else 1.0 / np.sqrt(binned.counts[ok])
    popt, _ = curve_fit(
        saturation, binned.centers[ok], binned.p[ok], p0=p0, sigma=sigma, maxfev=20000,
        bounds=((0.0, 0.0, 0.0), (1.0, 1.0, np.inf)),
    )
    return tuple(float(v) for v in popt)


def mean_MpApB(events, which: str = "M1", alleles: str = "minor") -> float:
    """<M pA pB> averaged over all contributing pairs.

    ``which``: the sample size used for M (``M1`` at t_{i+1}, ``M0`` at t_i). ``alleles``:
    ``minor`` uses the minor-allele frequencies at t_i (the paper: "A and B being the minor
    alleles"); ``missing`` uses the frequencies of the two alleles that form the missing haplotype.
    """
    a, b = ("qA", "qB") if alleles == "minor" else ("pA", "pB")
    return float(np.mean(events[which] * events[a] * events[b]))


def estimate_rho(events, bin_width: float = 8000.0, max_x: float | None = None, M: str = "M1",
                 alleles: str = "minor", p0=(0.1, 0.25, 4e-5), weights: str = "error") -> Fit:
    """Bin by d*dt, fit Eq. 5 and return rho = c1 c2 / (<M pA pB> - c0) (Eq. 3)."""
    x = events["d"] * events["dt"]
    top = (np.max(x) if max_x is None else max_x) + bin_width
    edges = np.arange(0.0, top, bin_width)
    b = bin_events(x, events["found"], edges)
    c0, c1, c2 = fit_saturation(b, p0=p0, weights=weights)
    m = mean_MpApB(events, M, alleles)
    return Fit(c0, c1, c2, m, c1 * c2 / (m - c0), int(len(x)), b)


def bootstrap_rho(per_patient, n: int = 500, seed: int = 0, with_fit: bool = False, **kw):
    """Resample patients with replacement ``n`` times and re-estimate rho each time.

    ``per_patient``: list of event tables, one per patient. With ``with_fit`` the fit parameters
    of each resample come back too, as an (n, 3) array of c0, c1 and c2: their spread is the
    uncertainty of the fit itself.
    """
    rng = np.random.default_rng(seed)
    k = len(per_patient)
    out = np.empty(n)
    pars = np.full((n, 3), np.nan)
    for i in range(n):
        pick = rng.integers(0, k, size=k)
        ev = concat_events(per_patient[j] for j in pick)
        try:
            fit = estimate_rho(ev, **kw)
        except RuntimeError:  # fit did not converge
            out[i] = np.nan
            continue
        out[i] = fit.rho
        pars[i] = (fit.c0, fit.c1, fit.c2)
    return (out, pars) if with_fit else out

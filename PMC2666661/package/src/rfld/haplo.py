"""Phase-unknown two-SNP haplotypes: EM estimate of the four haplotype frequencies, posterior
probabilities of the two phases of a double heterozygote, and sampled ("predicted") haplotype
pairs, as Meng et al. (2009) obtained them from haplo.stats.

Haplotype indices follow rfld.simulate: 0 = alleles (0, 0), 1 = (1, 1), 2 = (0, 1), 3 = (1, 0),
where the pair is (allele at SNP 1, allele at SNP 2) and allele 1 is the counted allele. Only the
double heterozygote (1, 1) is ambiguous: phase 0/1 (haplotypes 0 and 1) or phase 2/3.
"""

from __future__ import annotations

import numpy as np

__all__ = ["haplotype_em", "phase_posterior", "sample_haplotype_pairs"]

# haplotype index -> (allele at SNP 1, allele at SNP 2)
_A1 = np.array([0, 1, 0, 1])
_A2 = np.array([0, 1, 1, 0])


def _known_pairs(g1, g2):
    """For genotypes other than the double heterozygote, the haplotype pair is fixed."""
    table = {}
    for a in range(4):
        for b in range(a, 4):
            key = (_A1[a] + _A1[b], _A2[a] + _A2[b])
            table.setdefault(key, []).append((a, b))
    pairs = np.full((len(g1), 2), -1, np.int64)
    for key, opts in table.items():
        if len(opts) == 1:
            sel = (g1 == key[0]) & (g2 == key[1])
            pairs[sel] = opts[0]
    return pairs


def haplotype_em(g1, g2, tol=1e-10, max_iter=10000):
    """Maximum-likelihood haplotype frequencies (index order 0-3) from the genotypes (0, 1, 2) of
    two SNPs, by EM from equal starting frequencies. Returns (freqs, iterations)."""
    g1 = np.asarray(g1, dtype=np.int64)
    g2 = np.asarray(g2, dtype=np.int64)
    if g1.shape != g2.shape or g1.ndim != 1:
        raise ValueError("g1 and g2 must be 1-d arrays of the same length")
    if not (np.isin(g1, (0, 1, 2)).all() and np.isin(g2, (0, 1, 2)).all()):
        raise ValueError("genotypes must be 0, 1 or 2")
    known = _known_pairs(g1, g2)
    fixed = np.zeros(4)
    for a, b in known[known[:, 0] >= 0]:
        fixed[a] += 1
        fixed[b] += 1
    ndh = int(((g1 == 1) & (g2 == 1)).sum())
    n = len(g1)
    f = np.full(4, 0.25)
    for it in range(1, max_iter + 1):
        w01 = f[0] * f[1]
        w23 = f[2] * f[3]
        tot = w01 + w23
        p01 = w01 / tot if tot > 0 else 0.5
        counts = fixed.copy()
        counts[[0, 1]] += ndh * p01
        counts[[2, 3]] += ndh * (1 - p01)
        new = counts / (2 * n)
        if np.max(np.abs(new - f)) < tol:
            return new, it
        f = new
    return f, max_iter


def phase_posterior(freqs):
    """Posterior probability that a double heterozygote carries haplotypes 0 and 1 (else 2 and 3)."""
    w01 = freqs[0] * freqs[1]
    w23 = freqs[2] * freqs[3]
    return w01 / (w01 + w23) if (w01 + w23) > 0 else 0.5


def sample_haplotype_pairs(rng, g1, g2, freqs=None, n_samples=1):
    """Draw n_samples haplotype pairs per individual from the posterior given the genotypes.

    Returns an array (n_samples, n, 2) of haplotype indices. Individuals whose genotype fixes the
    pair get it in every sample; each double heterozygote's phase is drawn independently."""
    g1 = np.asarray(g1, dtype=np.int64)
    g2 = np.asarray(g2, dtype=np.int64)
    if freqs is None:
        freqs, _ = haplotype_em(g1, g2)
    p01 = phase_posterior(freqs)
    known = _known_pairs(g1, g2)
    dh = (g1 == 1) & (g2 == 1)
    out = np.repeat(known[None], n_samples, axis=0)
    draw = rng.random((n_samples, int(dh.sum()))) < p01
    pair01 = np.array([0, 1])
    pair23 = np.array([2, 3])
    out[:, dh, :] = np.where(draw[..., None], pair01, pair23)
    return out

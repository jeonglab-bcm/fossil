"""Case-control data under Risch's heterogeneity-multiplicative models (Lunetta et al. 2004;
Meng et al. 2009).

Model HhMm: h independent systems of m loci. With g_hm the number of risk alleles at locus m of
system h and (q0, q1, q2) the penetrance factors of every locus, the penetrance is
w(G) = 1 - prod_h [1 - prod_m q_{g_hm}].

Individuals are drawn from the population in Hardy-Weinberg and linkage equilibrium, affected with
probability w(G), and the first ``ncases`` affected and ``ncontrols`` unaffected individuals are kept.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

__all__ = [
    "GeneticModel", "MODELS", "DESIGNS", "LD_MODELS", "sample_case_control", "snp_dataset",
    "haplotype_frequencies", "haplotype_dataset", "table1_statistics",
]


@dataclass(frozen=True)
class GeneticModel:
    name: str
    h: int
    m: int
    p: float          # risk allele (or risk haplotype) frequency
    q: tuple          # penetrance factors for 0, 1, 2 risk alleles

    @property
    def nloci(self):
        return self.h * self.m


# Table 1 of Meng et al. (2009)
MODELS = {
    "H1M1": GeneticModel("H1M1", 1, 1, 0.03, (0.0, 0.9, 0.9)),
    "H2M3": GeneticModel("H2M3", 2, 3, 0.125, (0.0, 0.9, 0.9)),
    "H3M3": GeneticModel("H3M3", 3, 3, 0.106, (0.0, 0.9, 0.9)),
    "H3M4": GeneticModel("H3M4", 3, 4, 0.176, (0.0, 0.9, 0.9)),
    "H9M2": GeneticModel("H9M2", 9, 2, 0.031, (0.0, 0.9, 0.9)),
    "H4M4": GeneticModel("H4M4", 4, 4, 0.282, (1.20e-8, 0.79, 1.0)),
    "H8M4": GeneticModel("H8M4", 8, 4, 0.214, (2.80e-3, 0.86, 1.0)),
}

# Table 1, column "# Kept": the analysis design (k rSNPs genotyped, s per system) of each model
DESIGNS = {"H1M1": (1, 1), "H2M3": (3, 3), "H3M3": (3, 3), "H3M4": (4, 4), "H9M2": (2, 2),
           "H4M4": (4, 4), "H8M4": (4, 4)}

# Table 5: (LD.rSNPs per rSNP, LD.nSNPs per SNP 97-100)
LD_MODELS = {
    "n0": (0, 0), "n1": (0, 1), "n2": (0, 2), "n3": (0, 3), "n4": (0, 4),
    "r1": (1, 0), "r2": (2, 0), "r3": (3, 0), "r4": (4, 0),
    "r1n1": (1, 1), "r2n2": (2, 2), "r3n3": (3, 3), "r4n4": (4, 4),
}


def table1_statistics(model: GeneticModel):
    """Prevalence K, marginal genotype relative risks (het, hom) and sibling recurrence risk ratio
    lambda_s of a model, computed exactly (Hardy-Weinberg, linkage equilibrium, sib IBD 1/4, 1/2, 1/4)."""
    p, q, H, M = model.p, model.q, model.h, model.m
    g = ((1 - p) ** 2, 2 * p * (1 - p), p * p)
    mean_q = sum(a * b for a, b in zip(g, q))
    K = 1 - (1 - mean_q ** M) ** H

    def risk(gi):
        return 1 - (1 - q[gi] * mean_q ** (M - 1)) * (1 - mean_q ** M) ** (H - 1)

    het = risk(1) / risk(0) if risk(0) > 0 else math.inf
    hom = risk(2) / risk(0) if risk(0) > 0 else math.inf
    alleles = ((0, 1 - p), (1, p))
    s = 0.25 * mean_q ** 2 + 0.25 * sum(a * b * b for a, b in zip(g, q))
    for a, pa in alleles:            # sibs share one allele identical by descent
        for b1, p1 in alleles:
            for b2, p2 in alleles:
                s += 0.5 * pa * p1 * p2 * q[a + b1] * q[a + b2]
    both = 1 - 2 * (1 - mean_q ** M) ** H + (1 - 2 * mean_q ** M + s ** M) ** H
    return {"K": K, "grr_het": het, "grr_hom": hom, "lambda_s": both / K ** 2}


def _penetrance(counts, model):
    """counts: (N, h, m) risk allele counts."""
    q = np.asarray(model.q)
    return 1.0 - np.prod(1.0 - np.prod(q[counts], axis=2), axis=1)


def sample_case_control(rng, model, draw_counts, ncases=250, ncontrols=250, batch=4000):
    """Draw individuals until ncases affected and ncontrols unaffected are kept.

    draw_counts(rng, size) -> (counts (size, h, m), extra) gives the risk counts used by the
    penetrance and any per-individual data to keep (extra is an array indexed by individual).
    Returns (extra for the kept individuals, y) with cases first."""
    cases, controls = [], []
    nc = nu = 0
    while nc < ncases or nu < ncontrols:
        counts, extra = draw_counts(rng, batch)
        aff = rng.random(batch) < _penetrance(counts, model)
        a = extra[aff][: max(ncases - nc, 0)]
        u = extra[~aff][: max(ncontrols - nu, 0)]
        if len(a):
            cases.append(a)
            nc += len(a)
        if len(u):
            controls.append(u)
            nu += len(u)
    kept = np.concatenate(cases + controls)
    y = np.r_[np.ones(ncases, np.int64), np.zeros(ncontrols, np.int64)]
    return kept, y


def noise_frequencies(k):
    """k allele frequencies spread evenly over 0.01-0.99."""
    return np.linspace(0.01, 0.99, k)


def snp_dataset(rng, model, ld_model="n0", design=(4, 4), ncases=250, ncontrols=250):
    """One replicate of the SNP simulation (Meng et al. 2009, Table 5).

    design (k, s): k rSNPs genotyped, s from each system (K4S4: the 4 loci of system 1).
    Columns: rSNPs 1..k, 96 - k nSNPs (frequencies 0.01-0.99), 4 nSNPs (0.3, 0.4, 0.5, 0.6), then for
    each rSNP its LD.rSNPs, then for each of SNPs 97-100 its LD.nSNPs. An SNP in LD is a perfect
    proxy (r^2 = 1): a copy of the genotypes of its partner.

    Returns X (n, p) risk-allele counts, y, and the column classes: list of (kind, partner) with
    kind in 'rSNP', 'nSNP', 'LD.rSNP', 'LD.nSNP' and partner the column it copies (or -1)."""
    k, s = design
    n_ld_r, n_ld_n = LD_MODELS[ld_model]
    systems = k // s
    keep = [(h, j) for h in range(systems) for j in range(s)]

    def draw(rng, size):
        counts = rng.binomial(2, model.p, size=(size, model.h, model.m))
        geno = np.stack([counts[:, h, j] for h, j in keep], axis=1)
        return counts, geno

    rgeno, y = sample_case_control(rng, model, draw, ncases, ncontrols)
    n = len(y)
    n_even = 96 - k  # 100 independent SNPs in all: k rSNPs, 96 - k spread nSNPs, 4 more nSNPs
    freqs = np.r_[noise_frequencies(n_even), [0.3, 0.4, 0.5, 0.6]]
    ngeno = rng.binomial(2, freqs, size=(n, len(freqs)))
    cols = [rgeno, ngeno]
    kinds = [("rSNP", -1)] * k + [("nSNP", -1)] * len(freqs)
    for r in range(k):
        for _ in range(n_ld_r):
            cols.append(rgeno[:, [r]])
            kinds.append(("LD.rSNP", r))
    for j in range(n_even, n_even + 4):
        for _ in range(n_ld_n):
            cols.append(ngeno[:, [j]])
            kinds.append(("LD.nSNP", k + j))
    X = np.concatenate(cols, axis=1).astype(np.int64)
    return X, y, kinds


# Haplotypes ------------------------------------------------------------------------------------
# Two SNPs; alleles 1 = G (SNP1), T (SNP2) and 0 = T (SNP1), C (SNP2). Haplotype index:
# 0 = T-C, 1 = G-T (the risk haplotype), 2 = T-T, 3 = G-C. Allele of SNP1 is 1 for G-T and G-C,
# allele of SNP2 is 1 for G-T and T-T.
HAP_SNP1 = np.array([0, 1, 0, 1])
HAP_SNP2 = np.array([0, 1, 1, 0])
EMPIRICAL = {"TC": 0.570, "GT": 0.287, "TT": 0.113, "GC": 0.030}  # rs1503415-rs10790447, CEU


def _r2_of(f):
    tc, gt, tt, gc = f
    p1 = gt + gc
    p2 = gt + tt
    d = gt - p1 * p2
    return d * d / (p1 * (1 - p1) * p2 * (1 - p2))


def haplotype_frequencies(r2, rule="empirical_ratio", f_gt=0.287):
    """Frequencies (T-C, G-T, T-T, G-C) with G-T fixed at f_gt and the given r^2 between the SNPs.

    The paper fixes G-T and adjusts the other three without saying how; one free parameter is left.
    rule = 'empirical_ratio': T-T : G-C kept at the empirical 0.113 : 0.030 (this passes through the
    empirical frequencies at their r^2 = 0.447). rule = 'equal_snp_freq': T-T = G-C, so both SNPs
    have the same allele frequency."""
    if rule == "empirical_ratio":
        a, b = EMPIRICAL["TT"], EMPIRICAL["GC"]
    elif rule == "equal_snp_freq":
        a, b = 1.0, 1.0
    else:
        raise ValueError(f"unknown rule {rule!r}")

    def freqs(scale):
        tt, gc = a * scale, b * scale
        return np.array([1 - f_gt - tt - gc, f_gt, tt, gc])

    if r2 >= 1:
        return freqs(0.0)

    def d_of(scale):
        f = freqs(scale)
        return f[1] - (f[1] + f[3]) * (f[1] + f[2])

    # D falls from positive at scale 0 to 0 at s0; r^2 falls from 1 to 0 on [0, s0].
    lo, hi = 0.0, (1 - f_gt) / (a + b)
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if d_of(mid) > 0:
            lo = mid
        else:
            hi = mid
    s0 = 0.5 * (lo + hi)
    if r2 <= 0:
        return freqs(s0)
    lo, hi = 0.0, s0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if _r2_of(freqs(mid)) > r2:
            lo = mid
        else:
            hi = mid
    return freqs(0.5 * (lo + hi))


def haplotype_dataset(rng, model, freqs, design=(4, 4), n_total=100, ncases=250, ncontrols=250):
    """One replicate of the haplotype simulation (Meng et al. 2009, K4S4N100 and K4S2N100).

    Every locus of the HhMm model is a two-SNP haplotype; its risk count is the number of G-T
    haplotypes carried. Returns a dict with
      haps  (n, k, 2) haplotype indices of the k genotyped risk haplotypes (unordered pair),
      snps  (n, 2k)   allele counts of their SNPs (SNP1, SNP2 of haplotype 1, then haplotype 2, ...),
      noise (n, n_total - 2k) noise SNP genotypes with frequencies 0.01-0.99,
      y."""
    k, s = design
    systems = k // s
    keep = [(h, j) for h in range(systems) for j in range(s)]
    cum = np.cumsum(freqs)

    def draw(rng, size):
        u = rng.random((size, model.h, model.m, 2))
        hap = np.searchsorted(cum, u, side="right").clip(0, 3)
        counts = (hap == 1).sum(axis=3)
        kept = np.stack([hap[:, h, j, :] for h, j in keep], axis=1)
        return counts, kept

    haps, y = sample_case_control(rng, model, draw, ncases, ncontrols)
    n = len(y)
    snps = np.empty((n, 2 * k), np.int64)
    for j in range(k):
        snps[:, 2 * j] = HAP_SNP1[haps[:, j, :]].sum(axis=1)
        snps[:, 2 * j + 1] = HAP_SNP2[haps[:, j, :]].sum(axis=1)
    nn = n_total - 2 * k
    noise = rng.binomial(2, noise_frequencies(nn), size=(n, nn)).astype(np.int64)
    return {"haps": haps, "snps": snps, "noise": noise, "y": y}


def haplo_genotype_code(pairs):
    """Code an unordered pair of haplotype indices (0-3) as one of 10 categories 0..9."""
    a = np.minimum(pairs[..., 0], pairs[..., 1])
    b = np.maximum(pairs[..., 0], pairs[..., 1])
    # (0,0)=0 (0,1)=1 (0,2)=2 (0,3)=3 (1,1)=4 (1,2)=5 (1,3)=6 (2,2)=7 (2,3)=8 (3,3)=9
    return (a * (7 - a)) // 2 + b

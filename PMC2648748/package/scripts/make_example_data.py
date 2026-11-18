"""Make the package's example data and its expected output, independently of the package.

usage: python make_example_data.py OUTDIR

The example is a small case-control data set from the paper's simulation design, written here in
NumPy from the published formulas, not with the R package:

* the threshold model (model 3 of Marchini, Donnelly and Cardon 2005): odds of disease alpha for
  genotypes without a minor allele at either locus, alpha (1 + theta) otherwise; alpha and theta
  solved for prevalence 0.1 and marginal effect lambda = 1 (the paper's value for model 3), lambda
  being the odds ratio of the marginal penetrances of the heterozygote and the wild-type
  homozygote, minus 1;
* both disease loci at minor allele frequency 0.3 and genotyped directly (r^2 = 1);
* 300 cases, 300 controls and 60 SNPs; the 58 null SNPs have minor allele frequencies drawn from
  U(0.05, 0.5).

The expected output is what this script knows by construction or computes with SciPy from the
paper's formulas:

* which two SNPs are the disease loci (epiForest should identify both);
* the B statistic (Zhang and Liu 2007, pseudo-counts 0.5) and its p-value for each disease SNP
  and for the pair, with the shifted chi-squared null distribution described in the package
  (2B - shift ~ chi-squared with 3^k - 1 degrees of freedom);
* the single-locus chi-squared p-value of each disease SNP (scipy.stats.chi2_contingency).
"""
import csv
import sys
from math import lgamma, log, pi
from pathlib import Path

import numpy as np
from scipy import optimize, stats

SEED = 20090130
N_CASES, N_CONTROLS, N_SNPS = 300, 300, 60
MAF, LAMBDA, PREVALENCE = 0.3, 1.0, 0.1
DISEASE = (17, 44)  # 1-based SNP columns of the two disease loci


def threshold_model(maf, lam, prev):
    hw = np.array([(1 - maf) ** 2, 2 * maf * (1 - maf), maf ** 2])
    w = np.outer(hw, hw)
    i, j = np.meshgrid(range(3), range(3), indexing="ij")

    def pen(log_alpha, theta):
        odds = np.exp(log_alpha) * np.where((i == 0) | (j == 0), 1.0, 1.0 + theta)
        return odds / (1 + odds)

    def alpha_for(theta):
        return optimize.brentq(lambda la: (w * pen(la, theta)).sum() - prev, -30, 20, xtol=1e-14)

    def marginal_lambda(theta):
        p = pen(alpha_for(theta), theta) @ hw
        odds = p / (1 - p)
        return odds[1] / odds[0] - 1

    theta = optimize.brentq(lambda t: marginal_lambda(t) - lam, 1e-6, 1e4, xtol=1e-14)
    return pen(alpha_for(theta), theta), hw


def simulate(rng):
    P, hw = threshold_model(MAF, LAMBDA, PREVALENCE)
    w = np.outer(hw, hw).ravel()
    cells = {1: w * P.ravel(), 0: w * (1 - P.ravel())}
    status = np.r_[np.ones(N_CASES, int), np.zeros(N_CONTROLS, int)]
    loci = np.zeros((len(status), 2), int)
    for s, n in ((1, N_CASES), (0, N_CONTROLS)):
        prob = cells[s] / cells[s].sum()
        c = rng.choice(9, size=n, p=prob)
        rows = slice(0, N_CASES) if s == 1 else slice(N_CASES, None)
        loci[rows, 0], loci[rows, 1] = c // 3, c % 3
    geno = np.zeros((len(status), N_SNPS), int)
    mafs = rng.uniform(0.05, 0.5, N_SNPS)
    for j in range(N_SNPS):
        geno[:, j] = rng.binomial(2, mafs[j], len(status))
    geno[:, DISEASE[0] - 1] = loci[:, 0]
    geno[:, DISEASE[1] - 1] = loci[:, 1]
    return geno, status


def dm(counts, a=0.5):
    counts = np.asarray(counts, float)
    J, N = len(counts), counts.sum()
    return lgamma(J * a) - lgamma(N + J * a) + sum(lgamma(c + a) for c in counts) - J * lgamma(a)


def joint_counts(g, cols):
    code = np.zeros(len(g), int)
    for i, c in enumerate(cols):
        code += g[:, c] * 3 ** i
    return np.bincount(code, minlength=3 ** len(cols))


def log_pmix(g, cols):
    lj = dm(joint_counts(g, cols))
    if len(cols) == 1:
        return lj
    li = sum(dm(np.bincount(g[:, c], minlength=3)) for c in cols)
    return np.logaddexp(li, lj) - log(2)


def b_statistic(geno, status, cols):
    d, u = geno[status == 1], geno[status == 0]
    k = len(cols)
    B = dm(joint_counts(d, cols)) + log_pmix(u, cols) - log_pmix(geno, cols)
    nd, nu = len(d), len(u)

    def off(J, N):
        return -(J - 1) / 2 * log(N / (2 * pi)) + lgamma(J / 2) - J / 2 * log(pi)

    mix = -log(2) if k >= 2 else 0.0
    shift = 2 * ((off(3 ** k, nd) + k * off(3, nu) + mix) - (k * off(3, nd + nu) + mix))
    df = 3 ** k - 1
    p = stats.chi2.sf(max(2 * B - shift, 0.0), df)
    return B, df, shift, p


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    geno, status = simulate(rng)
    names = [f"snp{j + 1}" for j in range(N_SNPS)]
    with open(out / "example_genotypes.csv", "w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["status"] + names)
        for s, row in zip(status, geno):
            wr.writerow([s] + list(row))
    rows = []
    for cols in ([DISEASE[0] - 1], [DISEASE[1] - 1], [DISEASE[0] - 1, DISEASE[1] - 1]):
        B, df, shift, p = b_statistic(geno, status, cols)
        rows.append({"test": "B", "snps": ";".join(names[c] for c in cols), "statistic": f"{float(B):.17g}",
                     "df": df, "shift": f"{float(shift):.17g}", "p": f"{float(p):.17g}"})
    for c in DISEASE:
        tab = np.array([np.bincount(geno[status == s, c - 1], minlength=3) for s in (1, 0)])
        tab = tab[:, tab.sum(axis=0) > 0]
        chi2, p, df, _ = stats.chi2_contingency(tab, correction=False)
        rows.append({"test": "chisq", "snps": names[c - 1], "statistic": f"{float(chi2):.17g}", "df": int(df),
                     "shift": "", "p": f"{float(p):.17g}"})
    rows.append({"test": "disease_snps", "snps": ";".join(names[c - 1] for c in DISEASE),
                 "statistic": "", "df": "", "shift": "", "p": ""})
    with open(out / "example_expected.csv", "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=["test", "snps", "statistic", "df", "shift", "p"])
        wr.writeheader()
        wr.writerows(rows)


if __name__ == "__main__":
    main()

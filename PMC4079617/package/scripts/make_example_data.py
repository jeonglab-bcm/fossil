"""Write the bundled example: one simulated cohort of the study's design, contaminated, and its expected fits.

Usage: python scripts/make_example_data.py   (from the package folder; needs numpy, scipy, statsmodels)

Input (src/robustrr/data/cohort.csv): 500 subjects of the scenario RR 2.0, outcome 10%, quadratic confounder,
strong association (Additional file 1), drawn with seed 4079617, the outcome then reversed for the subjects whose
true p_y is beyond the population's 2.5% and 97.5% quantiles (5% contamination). Columns: id, y, x, z.

Expected output (src/robustrr/data/cohort_expected.csv), computed without robustrr's fitting code:
  robust Poisson: statsmodels' Poisson GLM with HC0 (sandwich) standard errors
  log-binomial:   the likelihood maximized by scipy (Nelder-Mead, then Powell). The plain maximum is on the
                  boundary for this cohort (a fitted probability reaches 1), so the COPY likelihood is maximized:
                  weights 1,000,000 on the data and 1 on the data with y reversed. Its SE is the inverse expected
                  information sum mu/(1 - mu) x x' at that maximum.
Model: y on x, z and z^2.
"""
import csv
import math
from pathlib import Path

import numpy as np
import statsmodels.api as sm
from scipy.optimize import minimize

import robustrr as rr

HERE = Path(__file__).resolve().parent.parent / "src" / "robustrr" / "data"
C = 1_000_000
Z975 = 1.959963984540054
TERMS = ["x", "z", "z^2"]


def main():
    s = rr.scenario(2.0, 10, "nonlinear", "strong")
    z, x, y, p = rr.generate(s, 500, 1, np.random.default_rng(4079617))
    yc = rr.contaminate(y, p, 0.05, cutoffs=rr.population_cutoffs(s, 0.05))[0]
    z, x = z[0], x[0]
    with open(HERE / "cohort.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["id", "y", "x", "z"])
        for i in range(500):
            w.writerow([i + 1, int(yc[i]), int(x[i]), f"{z[i]:.6f}"])
    zz = np.array([float(f"{v:.6f}") for v in z])            # as written
    X = np.column_stack([np.ones(500), x, zz, zz * zz])
    rows = []
    m = sm.GLM(yc, X, family=sm.families.Poisson()).fit(cov_type="HC0", tol=1e-13)
    for j, t in enumerate(TERMS, 1):
        b, se = m.params[j], m.bse[j]
        rows.append(["robust_poisson", t, b, se, math.exp(b), math.exp(b - Z975 * se), math.exp(b + Z975 * se), "", ""])

    def nll(b, a, w_):
        eta = X @ b
        if (eta >= 0).any():
            return 1e300
        return -float((a * eta + w_ * np.log(-np.expm1(eta))).sum())
    st = np.array([math.log(yc.mean()), 0, 0, 0])
    plain = minimize(nll, st, args=(yc, 1 - yc), method="Nelder-Mead", options={"xatol": 1e-12, "fatol": 1e-14, "maxiter": 400000, "maxfev": 400000})
    a, w_ = yc + (1 - yc) / C, (1 - yc) + yc / C
    res = minimize(nll, plain.x - np.array([1e-3, 0, 0, 0]), args=(a, w_), method="Nelder-Mead",
                   options={"xatol": 1e-12, "fatol": 1e-14, "maxiter": 400000, "maxfev": 400000})
    res = minimize(nll, res.x, args=(a, w_), method="Powell", options={"xtol": 1e-13, "ftol": 1e-16, "maxiter": 400000})
    mu = np.exp(X @ res.x)
    print(f"plain maximum: largest fitted probability {np.exp((X @ plain.x).max()):.6f}; COPY: {mu.max():.6f}")
    cov = np.linalg.inv((X * (mu / (1 - mu))[:, None]).T @ X)
    for j, t in enumerate(TERMS, 1):
        b, se = res.x[j], math.sqrt(cov[j, j])
        rows.append(["log_binomial", t, b, se, math.exp(b), math.exp(b - Z975 * se), math.exp(b + Z975 * se), "copy", mu.max()])
    with open(HERE / "cohort_expected.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["model", "term", "log_rr", "se", "rr", "ci_low", "ci_high", "method", "max_fitted"])
        for r in rows:
            w.writerow([r[0], r[1]] + [f"{v:.10g}" for v in r[2:7]] + [r[7], f"{r[8]:.10g}" if r[8] != "" else ""])
    print("wrote", HERE / "cohort.csv", HERE / "cohort_expected.csv")


if __name__ == "__main__":
    main()

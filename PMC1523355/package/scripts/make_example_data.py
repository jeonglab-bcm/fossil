"""Write the package's example data: a synthetic trial and its expected analysis.

Usage: python make_example_data.py   (needs numpy and statsmodels; not the package)

trial.csv: one trial of the paper's base case (N = 8,800, 4,400 per arm; six independent RFs of
prevalence 25% and odds ratio 2; 5-year CER 0.75% with no RF; EER = CER x .5 + .003 x 5), seed 2006.
trial_expected.csv: the interaction tests of that trial, fitted with statsmodels' Logit (an
independent implementation, not this package): RF 1 alone (conventional analysis) and the RF count
(risk-stratified analysis).
"""
import csv
from pathlib import Path

import numpy as np
import statsmodels
import statsmodels.api as sm

OUT = Path(__file__).resolve().parent.parent / "src" / "stratpower" / "data"
rng = np.random.default_rng(2006)
n = 4400
rf = (rng.random((2 * n, 6)) < 0.25).astype(int)
arm = np.repeat([0, 1], n)
odds = 0.0075 / (1 - 0.0075) * 2.0 ** rf.sum(1)
cer = odds / (1 + odds)
risk = np.where(arm == 1, cer * 0.5 + 0.003 * 5, cer)
outcome = (rng.random(2 * n) < risk).astype(int)

with open(OUT / "trial.csv", "w", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["arm", "outcome"] + [f"rf{i}" for i in range(1, 7)])
    for i in range(2 * n):
        w.writerow([arm[i], outcome[i], *rf[i]])

rows = []
for label, z in (("rf1", rf[:, 0].astype(float)), ("score", rf.sum(1).astype(float))):
    X = sm.add_constant(np.column_stack([z, arm, z * arm]))
    fit = sm.Logit(outcome, X).fit(disp=0, tol=1e-12, maxiter=100)
    for term, b, s in zip(("intercept", "z", "arm", "z_x_arm"), fit.params, fit.bse):
        rows.append([label, term, repr(float(b)), repr(float(s))])
    rows.append([label, "p_interaction", repr(float(fit.pvalues[3])), ""])
with open(OUT / "trial_expected.csv", "w", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["subgroup", "term", "coef", "se"])
    w.writerows(rows)
print(f"wrote trial.csv ({2 * n} rows, {outcome.sum()} events) and trial_expected.csv (statsmodels {statsmodels.__version__})")

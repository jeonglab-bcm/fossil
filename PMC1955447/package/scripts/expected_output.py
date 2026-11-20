"""Write the expected output of the bundled example, computed without mlagq: the maximum likelihood estimate of
the paper's model (fixed effects 1, z, x, x:z; correlated random intercept and slope on x) found by maximizing
the log-likelihood integrated on a dense grid (241 x 241 points over +-7 SD in whitened coordinates) with SciPy's
BFGS on a log-Cholesky parameterization, and standard errors from a finite-difference Hessian of that
log-likelihood in the variance parameterization (var0, cov01, var1) that mlagq reports.

Usage: python scripts/expected_output.py   (needs numpy and scipy; writes src/mlagq/data/clustered_binary_expected.csv)
"""
import csv
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

data = Path(__file__).resolve().parents[1] / "src" / "mlagq" / "data"
rows = list(csv.DictReader(open(data / "clustered_binary.csv")))
groups = sorted(set(r["group"] for r in rows))
G = [[r for r in rows if r["group"] == g] for g in groups]
X = [np.array([[1.0, float(r["z"]), float(r["x"]), float(r["x"]) * float(r["z"])] for r in g]) for g in G]
XS = [np.array([float(r["x"]) for r in g]) for g in G]
Y = [np.array([float(r["y"]) for r in g]) for g in G]
T = np.linspace(-7, 7, 241)
B0, B1 = np.meshgrid(T, T, indexing="ij")
PHI = np.exp(-0.5 * (B0 ** 2 + B1 ** 2)) / (2 * np.pi) * (T[1] - T[0]) ** 2


def ll_var(beta, v0, c01, v1):
    D = np.array([[v0, c01], [c01, v1]])
    L = np.linalg.cholesky(D)
    u0, u1 = L[0, 0] * B0, L[1, 0] * B0 + L[1, 1] * B1
    tot = 0.0
    for Xj, xj, yj in zip(X, XS, Y):
        lin = (Xj @ beta)[:, None, None] + u0[None] + u1[None] * xj[:, None, None]
        l = (yj[:, None, None] * lin - np.logaddexp(0, lin)).sum(0)
        m = l.max()
        tot += m + np.log((np.exp(l - m) * PHI).sum())
    return tot


def negll(p):
    l11, l21, l22 = np.exp(p[4]), p[5], np.exp(p[6])
    return -ll_var(p[:4], l11 ** 2, l11 * l21, l21 ** 2 + l22 ** 2)


res = minimize(negll, np.array([-1, .3, .3, .3, np.log(np.sqrt(.67)), 0, 0]), method="BFGS", options={"gtol": 1e-7})
l11, l21, l22 = np.exp(res.x[4]), res.x[5], np.exp(res.x[6])
theta = np.concatenate([res.x[:4], [l11 ** 2, l11 * l21, l21 ** 2 + l22 ** 2]])


def f(t):
    return ll_var(t[:4], t[4], t[5], t[6])


h = 1e-4
H = np.zeros((7, 7))
for i in range(7):
    for j in range(i, 7):
        e_i, e_j = np.eye(7)[i] * h, np.eye(7)[j] * h
        H[i, j] = H[j, i] = (f(theta + e_i + e_j) - f(theta + e_i - e_j) - f(theta - e_i + e_j) + f(theta - e_i - e_j)) / (4 * h * h)
se = np.sqrt(np.diag(np.linalg.inv(-H)))
names = ["1", "z", "x", "x:z", "var(1)", "cov(1;x)", "var(x)"]
with open(data / "clustered_binary_expected.csv", "w") as fh:
    fh.write("parameter,estimate,se\n")
    for nm, e, s in zip(names, theta, se):
        fh.write(f"{nm},{e:.6f},{s:.6f}\n")
print(res.message, -res.fun)
print(open(data / "clustered_binary_expected.csv").read())

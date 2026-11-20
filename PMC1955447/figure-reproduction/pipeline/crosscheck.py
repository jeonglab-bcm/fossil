"""Check mlagq's likelihood and its maximum against direct numerical integration (an independent computation).

Usage: crosscheck.py OUT.json

For 12 data sets (two from each ICC of 30 groups x 5 and 30 groups x 30, drawn as in the main run), at mlagq's estimate:
1. the adaptive quadrature log-likelihood with the points NLMIXED's rule picks, against the integral computed on
   a dense 2-D grid (301 x 301 points over +-7 SD of each random effect, in the random effects' whitened
   coordinates), group by group; and
2. for the fits that converged at an interior maximum: no step of 1e-4 along any parameter (either sign) raises
   the dense-grid log-likelihood by more than 1e-5 (the quadrature itself, with the points NLMIXED's rule picks,
   is accurate to about 1e-5 relative), so the estimate is the maximum of the exact likelihood too.
"""
import json
import sys

import numpy as np

from mlagq import simulation as sim
from mlagq.core import build_D, loglik

GRID = np.linspace(-7, 7, 301)
DX = GRID[1] - GRID[0]


def dense_loglik(theta, d):
    beta, D = theta[:4], build_D(theta[4:], 2, True)
    L = np.linalg.cholesky(D)
    B0, B1 = np.meshgrid(GRID, GRID, indexing="ij")
    phi = np.exp(-0.5 * (B0 ** 2 + B1 ** 2)) / (2 * np.pi)
    u0 = L[0, 0] * B0
    u1 = L[1, 0] * B0 + L[1, 1] * B1
    tot = 0.0
    for j in range(d.y.shape[0]):
        eta = d.X[j] @ beta
        lin = eta[:, None, None] + u0[None] + u1[None] * d.Z[j, :, 1][:, None, None]
        ll = (d.y[j][:, None, None] * lin - np.logaddexp(0, lin)).sum(0)
        m = ll.max()
        tot += m + np.log((np.exp(ll - m) * phi).sum() * DX * DX)
    return float(tot)


def main():
    out = sys.argv[1]
    cells = [c for c in sim.cells("main") if c["groups"] == 30 and c["size"] in (5, 30)]
    rows, worst_ll, worst_gain = [], 0.0, 0.0
    for c in cells:
        for rep in (0, 1):
            rec, d = sim.run_replicate("main", c, rep, 19554471)
            theta = np.array([rec[k] for k in ("g00", "g01", "g10", "g11", "var0", "cov01", "var1")])
            D = build_D(theta[4:], 2, True)
            if np.linalg.eigvalsh(D).min() <= 1e-8:
                rows.append({"cell": c["id"], "rep": rep, "status": rec["status"], "skipped": "estimate on the boundary"})
                continue
            agq = loglik(theta, d, cov=True, Q=int(rec["qpoints"]))
            exact = dense_loglik(theta, d)
            r = {"cell": c["id"], "rep": rep, "status": rec["status"], "qpoints": int(rec["qpoints"]),
                 "agq": round(agq, 8), "dense": round(exact, 8), "relative_difference": abs(agq - exact) / abs(exact)}
            worst_ll = max(worst_ll, r["relative_difference"])
            if rec["status"] in ("gconv", "absgconv"):
                gain = 0.0
                for i in range(7):
                    for s in (1e-4, -1e-4):
                        t = theta.copy()
                        t[i] += s
                        if np.linalg.eigvalsh(build_D(t[4:], 2, True)).min() > 0:
                            gain = max(gain, dense_loglik(t, d) - exact)
                r["best_gain_of_a_step"] = gain
                worst_gain = max(worst_gain, gain)
            rows.append(r)
    compared = [r for r in rows if "agq" in r]
    maxima = [r for r in rows if "best_gain_of_a_step" in r]
    passed = worst_ll < 1e-4 and worst_gain < 1e-5 and len(compared) >= 8
    doc = {"passed": passed,
           "detail": (f"mlagq's adaptive quadrature log-likelihood against a dense-grid integral on {len(compared)} "
                      f"data sets of 30 groups x 5 and x 30 (all ICCs): every relative difference "
                      f"{'below' if worst_ll < 1e-4 else 'NOT below'} 1e-4; at {len(maxima)} interior maxima no step of "
                      f"1e-4 in any parameter raises the dense-grid log-likelihood by 1e-5 or more"
                      + ("" if worst_gain < 1e-5 else " FAILED")),
           "largest_relative_difference": worst_ll, "largest_gain_of_a_step": worst_gain,
           "rows": rows}
    with open(out, "w") as f:
        json.dump(doc, f, indent=1)
        f.write("\n")
    print(doc["detail"], file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()

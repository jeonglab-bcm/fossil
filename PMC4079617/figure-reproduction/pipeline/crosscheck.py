"""Check robustrr's batched fits against independent implementations.

Usage: crosscheck.py OUT_JSON

On contaminated data sets of five scenarios (n = 500, 12 each, the non-linear ones with many COPY fits):
  robust Poisson   coefficients against statsmodels' Poisson GLM, and the sandwich SE against its HC0 SE
  log-binomial     the plain or COPY fit against an independent maximizer of the same likelihood
                   (scipy Nelder-Mead then Powell, started from log(mean y)): same coefficients, and ours at
                   least as high a likelihood; and the score of ours at zero
statsmodels' own log-binomial GLM is not used as the reference: on these data its IRLS stops at lower
likelihoods than ours (see the README).
"""
import json
import math
import sys
import warnings

import numpy as np
import statsmodels.api as sm
from scipy.optimize import minimize

import robustrr as rr
from robustrr.simulation import design_matrix

warnings.filterwarnings("ignore")
SCEN = [((1.5, 10, "nonlinear", "moderate"), 0.02), ((2.0, 10, "nonlinear", "strong"), 0.05),
        ((1.5, 40, "nonlinear", "strong"), 0.0), ((1.5, 25, "linear", "strong"), 0.05), ((2.0, 40, "linear", "moderate"), 0.02)]
REPS, N = 12, 500


def neg_ll(b, X, a, w):
    eta = X @ b
    if (eta[w > 0] >= 0).any() or (eta > 0).any():
        return 1e300
    with np.errstate(divide="ignore"):
        return -float((a * eta + np.where(w > 0, w * np.log(-np.expm1(np.minimum(eta, -1e-300))), 0)).sum())


def main():
    out = sys.argv[1]
    rows = []
    for i, (k, rate) in enumerate(SCEN):
        s = rr.scenario(*k)
        rng = np.random.default_rng([7, i])
        z, x, y, p = rr.generate(s, N, REPS, rng)
        cut = rr.population_cutoffs(s, rate) if rate else None
        yc = rr.contaminate(y, p, rate, cutoffs=cut)
        X = design_matrix(x, z, k[2] == "nonlinear")
        brp, _ = rr.poisson_coef(X, yc)
        blb, info = rr.log_binomial_coef(X, yc)
        for r in range(REPS):
            m = sm.GLM(yc[r], X[r], family=sm.families.Poisson()).fit(cov_type="HC0", tol=1e-13)
            rp = rr.robust_poisson(X[r], yc[r])
            if info["method"][r] == "mle":
                a, w = yc[r], 1 - yc[r]
            else:
                C = rr.DEFAULT_COPIES
                a, w = yc[r] + (1 - yc[r]) / C, (1 - yc[r]) + yc[r] / C
            st = np.zeros(X.shape[2])
            st[0] = math.log(yc[r].mean())
            res = minimize(neg_ll, st, args=(X[r], a, w), method="Nelder-Mead",
                           options={"xatol": 1e-11, "fatol": 1e-13, "maxiter": 200000, "maxfev": 200000})
            res = minimize(neg_ll, res.x, args=(X[r], a, w), method="Powell", options={"xtol": 1e-12, "ftol": 1e-15, "maxiter": 200000})
            eta = X[r] @ blb[r]
            with np.errstate(divide="ignore", invalid="ignore"):
                score = X[r].T @ (a - np.where(w > 0, w * np.exp(eta) / -np.expm1(eta), 0))
            rows.append({"scenario": f"RR {k[0]}, {k[1]}%, {k[2]} {k[3]}, {int(100 * rate)}%", "replicate": r,
                         "lb_method": str(info["method"][r]),
                         "rp_coef_diff": float(np.abs(m.params - brp[r]).max()),
                         "rp_se_rel_diff": float(np.abs(m.bse / np.sqrt(np.diag(rp["cov"])) - 1).max()),
                         "lb_coef_diff": float(np.abs(res.x - blb[r]).max()),
                         "lb_loglik_ours_minus_scipy": float(res.fun - neg_ll(blb[r], X[r], a, w)),
                         "lb_score_max": float(np.abs(score).max())})
    agg = {"fits": len(rows), "copy_fits": sum(r["lb_method"] == "copy" for r in rows),
           "rp_coef_max_diff": max(r["rp_coef_diff"] for r in rows),
           "rp_se_max_rel_diff": max(r["rp_se_rel_diff"] for r in rows),
           "lb_coef_max_diff": max(r["lb_coef_diff"] for r in rows),
           "lb_loglik_min_gain": min(r["lb_loglik_ours_minus_scipy"] for r in rows),
           "lb_score_max": max(r["lb_score_max"] for r in rows)}
    passed = (agg["rp_coef_max_diff"] < 1e-8 and agg["rp_se_max_rel_diff"] < 1e-6 and agg["lb_coef_max_diff"] < 1e-5
              and agg["lb_loglik_min_gain"] > -1e-8 and agg["lb_score_max"] < 1e-4)
    detail = (f"{agg['fits']} contaminated data sets ({agg['copy_fits']} COPY fits): robust Poisson coefficients equal "
              f"statsmodels' to {agg['rp_coef_max_diff']:.0e} and the sandwich SE its HC0 SE to a relative {agg['rp_se_max_rel_diff']:.0e}; "
              f"log-binomial coefficients equal an independent maximizer's to {agg['lb_coef_max_diff']:.0e}, with a likelihood "
              f"at least as high (to {abs(agg['lb_loglik_min_gain']):.0e}) and a score of at most {agg['lb_score_max']:.0e}")
    json.dump({"passed": passed, "detail": detail, **agg, "fits_detail": rows}, open(out, "w"), indent=1)
    open(out, "a").write("\n")
    print(("passed: " if passed else "FAILED: ") + detail, file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()

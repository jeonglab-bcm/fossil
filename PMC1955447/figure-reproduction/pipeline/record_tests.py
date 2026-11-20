"""The text's statements that need the per-replicate records: the non-converged data sets of 30 groups of 5, the
normality of the estimates, and the tests of the non-normal models against model 1 (Discussion).

Usage: record_tests.py RECORDS_DIR OUT.json [--jobs N]

1. Results, Convergence: "we examined 168 non-convergent simulated data sets with 30 groups and group size of 5.
   We first fitted a logistic model with random intercept only and then a logistic model with random slope only
   ... classified as significant if the corresponding p-value was less than 0.05 ... Both ... significant in
   only a small proportion of these data sets (2.4%)." We redraw every non-converged 30 x 5 data set of our main
   run from its seed, fit both one-random-effect models (fixed effects as in the full model, started at the
   true values), and test each variance with NLMIXED's t test (estimate / SE, df = groups - 1). A likelihood-ratio
   test against the ordinary logistic regression (p from the 50:50 mixture of chi-square 0 and 1) is kept as a
   hypothesis.
2. Results, Distribution of parameter estimates: Shapiro-Wilk test of the fixed-effect estimates of the
   converged fits of each cell, at 0.05.
3. Discussion, Table 5: models 2-8 against model 1, at p < 0.01. Convergence: a logistic regression of the
   converged indicator on the model (2 levels), pooled over the numbers of groups, per group size (LR test).
   Estimates: Welch t tests, pooled over the nine cells, between the converged fits' estimates (fixed effects) or
   relative errors (variances, whose true values differ between models); "underestimated" when the model's
   relative error is lower than model 1's. Coverage: Fisher's exact test of the
   non-coverage counts, pooled over the nine cells (random components) or per cell (fixed effects).
"""
import json
import multiprocessing as mp
import sys
from pathlib import Path

import numpy as np
from scipy import stats

from mlagq import simulation as sim
from mlagq.core import GroupedData, fit

sys.path.insert(0, str(Path(__file__).resolve().parent))
from summarize import read  # noqa: E402

BASE = 19554471


def glm_loglik(d):
    """Log-likelihood of the ordinary logistic regression on the same fixed effects (IRLS)."""
    X = d.X.reshape(-1, d.p)
    y = d.y.ravel()
    b = np.zeros(d.p)
    for _ in range(100):
        eta = X @ b
        pr = 1 / (1 + np.exp(-eta))
        W = pr * (1 - pr)
        step = np.linalg.solve(X.T @ (X * W[:, None]) + 1e-12 * np.eye(d.p), X.T @ (y - pr))
        b += step
        if np.max(np.abs(step)) < 1e-10:
            break
    eta = X @ b
    return float(np.sum(y * eta - np.logaddexp(0, eta)))


def one_effect_fits(args):
    cell, rep = args
    rng = np.random.default_rng(sim.seed_for(BASE, "main", cell["index"], rep))
    d = sim.generate(rng, cell["groups"], cell["size"], cell["gamma"], cell["var0"], cell["var1"])
    out = {"cell": cell["id"], "rep": rep}
    ll0 = glm_loglik(d)
    for name, col, var in (("intercept", 0, cell["var0"]), ("slope", 1, cell["var1"])):
        dd = GroupedData(d.y, d.X, d.Z[:, :, col:col + 1], d.mask, d.fixed_names, [d.random_names[col]])
        f = fit(dd, list(cell["gamma"]) + [var], absxconv=1e-8)
        est, se = f.estimate[-1], f.se[-1]
        df = cell["groups"] - 1
        p = float(2 * stats.t.sf(abs(est / se), df)) if np.isfinite(se) and se > 0 else None
        lrt = max(2 * (f.loglik - ll0), 0.0)
        p_lrt = float(0.5 * stats.chi2.sf(lrt, 1)) if lrt > 0 else 1.0   # boundary: 50:50 mixture of chi2(0), chi2(1)
        out[name] = {"variance": float(est), "se": None if not np.isfinite(se) else float(se), "p": p,
                     "converged": bool(f.converged), "significant": bool(p is not None and p < 0.05),
                     "p_lrt": p_lrt, "significant_lrt": bool(p_lrt < 0.05)}
    return out


def lr_two_groups(k1, n1, k2, n2):
    """LR test that two binomial proportions are equal (logistic regression on a 2-level factor)."""
    def ll(k, n):
        p = k / n
        return (k * np.log(p) if k else 0.0) + ((n - k) * np.log(1 - p) if k < n else 0.0)
    stat = 2 * (ll(k1, n1) + ll(k2, n2) - ll(k1 + k2, n1 + n2))
    return float(stats.chi2.sf(max(stat, 0.0), 1))


def robustness_tests(rows):
    cells = {c["id"]: c for c in sim.cells("robustness")}
    by = {}
    for r in rows:
        by.setdefault(r["cell"], []).append(r)
    out = {"convergence": {}, "fixed_t_tests": {}, "random_vs_model1": {}, "coverage": {}}
    for size in (5, 30, 50):
        out["convergence"][str(size)] = {}
        base = [r for J in (30, 50, 100) for r in by[f"m1_J{J}_n{size}"]]
        k1, n1 = sum(r["converged"] for r in base), len(base)
        for m in range(2, 9):
            rr = [r for J in (30, 50, 100) for r in by[f"m{m}_J{J}_n{size}"]]
            k2, n2 = sum(r["converged"] for r in rr), len(rr)
            p = lr_two_groups(k1, n1, k2, n2)
            out["convergence"][str(size)][str(m)] = {"model1_pct": 100 * k1 / n1, "pct": 100 * k2 / n2, "p": p,
                                                     "call": "no difference" if p >= 0.01 else ("more likely" if k2 / n2 > k1 / n1 else "less likely")}
    sig = []
    for m in range(2, 9):
        for p in sim.FIXED:
            a = [r[p] for J in (30, 50, 100) for n in (5, 30, 50) for r in by[f"m1_J{J}_n{n}"] if r["converged"]]
            b = [r[p] for J in (30, 50, 100) for n in (5, 30, 50) for r in by[f"m{m}_J{J}_n{n}"] if r["converged"]]
            t = stats.ttest_ind(b, a, equal_var=False)
            if t.pvalue < 0.01:
                sig.append({"model": m, "parameter": p, "p": float(t.pvalue)})
    out["fixed_t_tests"] = {"tests": 7 * 4, "significant_at_0.01": sig}

    def rel_errors(m, var):
        vals = []
        for J in (30, 50, 100):
            for n in (5, 30, 50):
                c = cells[f"m{m}_J{J}_n{n}"]
                vals += [(r[var] - c[var]) / c[var] for r in by[c["id"]] if r["converged"]]
        return np.array(vals)

    for m in range(2, 9):
        out["random_vs_model1"][str(m)] = {}
        for var in ("var0", "var1"):
            a, b = rel_errors(1, var), rel_errors(m, var)
            t = stats.ttest_ind(b, a, equal_var=False)
            out["random_vs_model1"][str(m)][var] = {"model1_bias_pct": 100 * a.mean(), "bias_pct": 100 * b.mean(),
                                                    "p": float(t.pvalue),
                                                    "underestimated": bool(t.pvalue < 0.01 and b.mean() < a.mean())}

    def miss_counts(m, key, sel):
        k = n = 0
        for J in (30, 50, 100):
            for nn in (5, 30, 50):
                if not sel(J, nn):
                    continue
                c = cells[f"m{m}_J{J}_n{nn}"]
                t = c[key] if key in ("var0", "var1") else dict(zip(sim.FIXED, c["gamma"]))[key]
                for r in by[c["id"]]:
                    if r["converged"] and np.isfinite(r[key + "_se"]):
                        n += 1
                        k += abs(r[key] - t) > 1.959963984540054 * r[key + "_se"]
        return k, n

    for m in range(2, 9):
        out["coverage"][str(m)] = {}
        for var in ("var0", "var1"):
            k1, n1 = miss_counts(1, var, lambda J, n: True)
            k2, n2 = miss_counts(m, var, lambda J, n: True)
            p = float(stats.fisher_exact([[k2, n2 - k2], [k1, n1 - k1]])[1])
            out["coverage"][str(m)][var] = {"model1_noncoverage": k1 / n1, "noncoverage": k2 / n2, "p": p,
                                            "lower_coverage": bool(p < 0.01 and k2 / n2 > k1 / n1)}
        fixed_sig = []
        for J in (50, 100):
            for n in (30, 50):
                for p in sim.FIXED:
                    k1, n1 = miss_counts(1, p, lambda a, b, J=J, n=n: (a, b) == (J, n))
                    k2, n2 = miss_counts(m, p, lambda a, b, J=J, n=n: (a, b) == (J, n))
                    pv = float(stats.fisher_exact([[k2, n2 - k2], [k1, n1 - k1]])[1])
                    if pv < 0.01:
                        fixed_sig.append({"groups": J, "size": n, "parameter": p, "p": pv})
        out["coverage"][str(m)]["fixed_significant_groups50plus_size30plus"] = fixed_sig
    return out


def main():
    rec_dir, out = Path(sys.argv[1]), sys.argv[2]
    jobs = int(sys.argv[sys.argv.index("--jobs") + 1]) if "--jobs" in sys.argv else 1
    rows = read(rec_dir / "main.csv.gz")
    cells = {c["id"]: c for c in sim.cells("main")}
    targets = [(cells[r["cell"]], int(r["rep"])) for r in rows
               if not r["converged"] and cells[r["cell"]]["groups"] == 30 and cells[r["cell"]]["size"] == 5]
    if jobs > 1:
        with mp.Pool(jobs) as pool:
            fits = pool.map(one_effect_fits, targets, chunksize=4)
    else:
        fits = [one_effect_fits(t) for t in targets]
    both = [f for f in fits if f["intercept"]["significant"] and f["slope"]["significant"]]
    both_lrt = [f for f in fits if f["intercept"]["significant_lrt"] and f["slope"]["significant_lrt"]]
    by_icc = {}
    for f in fits:
        b = by_icc.setdefault(f["cell"], [0, 0])
        b[0] += f["intercept"]["significant"] and f["slope"]["significant"]
        b[1] += 1
    # in the data sets where both are significant: the ratio of each estimate to its true variance
    ratios = [{"cell": f["cell"], "rep": f["rep"],
               "intercept_over_true": f["intercept"]["variance"] / cells[f["cell"]]["var0"],
               "slope_over_true": f["slope"]["variance"] / cells[f["cell"]]["var1"]} for f in both]
    doc = {"nonconverged": {"datasets": len(fits), "both_significant": len(both),
                            "both_significant_pct": 100.0 * len(both) / len(fits) if fits else None,
                            "intercept_significant_pct": 100.0 * sum(f["intercept"]["significant"] for f in fits) / len(fits),
                            "slope_significant_pct": 100.0 * sum(f["slope"]["significant"] for f in fits) / len(fits),
                            "lrt": {"both_significant_pct": 100.0 * len(both_lrt) / len(fits),
                                    "intercept_significant_pct": 100.0 * sum(f["intercept"]["significant_lrt"] for f in fits) / len(fits),
                                    "slope_significant_pct": 100.0 * sum(f["slope"]["significant_lrt"] for f in fits) / len(fits)},
                            "by_cell": {k: {"both": v[0], "datasets": v[1]} for k, v in by_icc.items()},
                            "both_significant_ratios": ratios}}
    # normality of the fixed-effect estimates, per cell
    norm = {}
    for cid, c in cells.items():
        ok = [r for r in rows if r["cell"] == cid and r["converged"]]
        norm[cid] = {}
        for p in sim.FIXED:
            v = np.array([r[p] for r in ok])
            w, pv = stats.shapiro(v)
            norm[cid][p] = {"W": round(float(w), 6), "p": float(f"{pv:.6g}"), "normal": bool(pv >= 0.05)}
    doc["normality"] = norm
    doc["robustness_tests"] = robustness_tests(read(rec_dir / "robustness.csv.gz"))
    Path(out).write_text(json.dumps(doc, indent=1) + "\n")


if __name__ == "__main__":
    main()

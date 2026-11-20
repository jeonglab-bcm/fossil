"""Summarize the per-replicate records into every quantity the paper prints.

Usage: summarize.py RECORDS_DIR OUT.json [--extra EXTRA.json]

RECORDS_DIR holds main.csv.gz (Tables 1-3), prevalence.csv.gz (Table 4) and robustness.csv.gz (Table 5), the
records the repository keeps. A full run (--full) also writes main_run2.csv.gz (a second run with other seeds) and
the hypothesis variants var_*.csv.gz (replicates 0-199 of the main grid, refitted another way); their summaries
are then written to EXTRA.json. Without those records, their summaries are read from EXTRA.json (the committed
output/records/extra.json).

Per cell: % converged, and over converged fits the % relative bias (variance scale for sigma0 and sigma1, as
fitted; the SD scale is kept as a hypothesis) and the non-coverage of the 95% Wald interval. Pooled over a
factor level (Table 2), all converged fits of the level are pooled; the p-value is a likelihood-ratio test of
the factor (3 levels) in a logistic regression of the non-coverage indicator.
"""
import csv
import gzip
import json
import math
import sys
from pathlib import Path

import numpy as np

from mlagq import simulation as sim

PARAMS = ["g00", "g01", "g10", "g11", "sigma0", "sigma1"]
VAR = {"sigma0": "var0", "sigma1": "var1"}
Z = 1.959963984540054
INTERIOR = {"gconv", "absgconv"}


def read(path):
    with gzip.open(path, "rt") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k, v in r.items():
            if k in ("study", "cell", "status"):
                continue
            r[k] = float(v)
        r["converged"] = r["converged"] == 1.0
        r["hessian_pd"] = r["hessian_pd"] == 1.0
    return rows


def by_cell(rows):
    out = {}
    for r in rows:
        out.setdefault(r["cell"], []).append(r)
    return out


def indicators(rows, cell, scale="variance", rule="paper"):
    """Per converged fit: estimates on the bias scale and non-coverage indicators (nan without an SE)."""
    ok = [r for r in rows if converged(r, rule)]
    true = dict(zip(sim.FIXED, cell["gamma"]))
    true.update(var0=cell["var0"], var1=cell["var1"])
    out = {"n": len(rows), "ok": ok}
    for p in PARAMS:
        k = VAR.get(p, p)
        est = np.array([r[k] for r in ok])
        se = np.array([r[k + "_se"] for r in ok])
        t = true[k]
        miss = np.where(np.isfinite(se), (np.abs(est - t) > Z * se).astype(float), np.nan)
        if p in VAR and scale == "sd":
            est, t = np.sqrt(np.clip(est, 0, None)), math.sqrt(t)
        out[p] = (est, t, miss)
    return out


def converged(r, rule):
    if rule == "paper":          # the optimizer's own criteria, ABSXCONV 1e-8 included
        return r["converged"]
    if rule == "interior":       # only fits that met a gradient criterion (no ABSXCONV)
        return r["status"] in INTERIOR
    if rule == "hessian":        # and a positive definite Hessian
        return r["converged"] and r["hessian_pd"]
    raise ValueError(rule)


def summary(rows, cell, scale="variance", rule="paper"):
    ind = indicators(rows, cell, scale, rule)
    n_ok = len(ind["ok"])
    s = {"n": ind["n"], "n_converged": n_ok, "converged_pct": 100.0 * n_ok / ind["n"],
         "converged_mcse": 100.0 * math.sqrt(max(n_ok / ind["n"] * (1 - n_ok / ind["n"]), 0) / ind["n"])}
    for p in PARAMS:
        est, t, miss = ind[p]
        n = est.size
        m = miss[np.isfinite(miss)]
        s[p] = {"bias_pct": 100.0 * (est.mean() - t) / t if n else None,
                "bias_mcse": 100.0 * est.std(ddof=1) / math.sqrt(n) / abs(t) if n > 1 else None,
                "noncoverage": float(m.mean()) if m.size else None,
                "n_ci": int(m.size)}
    s["with_se_pct"] = 100.0 * sum(math.isfinite(r["var0_se"]) for r in ind["ok"]) / ind["n"]
    return s


def r6(x):
    if isinstance(x, float):
        return round(x, 6)
    if isinstance(x, dict):
        return {k: r6(v) for k, v in x.items()}
    if isinstance(x, list):
        return [r6(v) for v in x]
    return x


def logistic_lrt(y, levels):
    """LR test of a 3-level factor in a logistic regression of y (0/1), p-value (chi-square, 2 df). With one
    categorical factor the fitted probabilities are the levels' proportions, so the fit is in closed form."""
    y = np.asarray(y, float)
    levels = np.asarray(levels)

    def ll(k, n):
        p = k / n
        return (k * math.log(p) if k > 0 else 0.0) + ((n - k) * math.log(1 - p) if k < n else 0.0)

    full = sum(ll(y[levels == l].sum(), (levels == l).sum()) for l in np.unique(levels))
    stat = 2 * (full - ll(y.sum(), y.size))
    return math.exp(-max(stat, 0.0) / 2)   # chi-square survival function with 2 df


def logistic_trend(y, levels):
    """LR test of the factor entered as a number (1 df) in a logistic regression of y; p-value."""
    y = np.asarray(y, float)
    rank = {l: i for i, l in enumerate(sorted(set(levels)))}
    X = np.column_stack([np.ones(y.size), [rank[l] for l in levels]])
    b = np.array([math.log(max(y.mean(), 1e-9) / max(1 - y.mean(), 1e-9)), 0.0])
    for _ in range(100):
        eta = X @ b
        pr = 1 / (1 + np.exp(-eta))
        step = np.linalg.solve(X.T @ (X * (pr * (1 - pr))[:, None]), X.T @ (y - pr))
        b += step
        if np.max(np.abs(step)) < 1e-12:
            break
    eta = X @ b
    ll1 = float(np.sum(y * eta - np.logaddexp(0, eta)))
    k, n = y.sum(), y.size
    ll0 = k * math.log(k / n) + (n - k) * math.log(1 - k / n)
    return math.erfc(math.sqrt(max(2 * (ll1 - ll0), 0.0) / 2))   # chi-square 1 df survival


def marginals(rows, cells):
    """Table 2: non-coverage pooled over each level of each factor, with the LR p-value of the factor."""
    cmap = {c["id"]: c for c in cells}
    per_fit = []   # (groups, size, icc, {param: miss})
    for cid, rr in by_cell(rows).items():
        c = cmap[cid]
        ind = indicators(rr, c)
        for i in range(len(ind["ok"])):
            per_fit.append((c["groups"], c["size"], c["icc"], {p: ind[p][2][i] for p in PARAMS}))
    out = {}
    for p in PARAMS:
        out[p] = {}
        for fi, fac in enumerate(("groups", "size", "icc")):
            sel = [(f[fi], f[3][p]) for f in per_fit if np.isfinite(f[3][p])]
            lv = sorted(set(l for l, _ in sel))
            out[p][fac] = {f"{l:g}" if fac != "icc" else f"{l:.2f}": float(np.mean([m for k, m in sel if k == l])) for l in lv}
            out[p][fac]["p"] = logistic_lrt([m for _, m in sel], [l for l, _ in sel])
            out[p][fac]["p_trend"] = logistic_trend([m for _, m in sel], [l for l, _ in sel])
            out[p][fac]["n"] = len(sel)
    # convergence and bias by factor (the text): pooled over all fits / converged fits of the level
    conv = {}
    for fi, fac in enumerate(("groups", "size", "icc")):
        conv[fac] = {}
        for c in cells:
            key = f"{c[fac]:g}" if fac != "icc" else f"{c[fac]:.2f}"
            rr = [r for r in rows if r["cell"] == c["id"]]
            a = conv[fac].setdefault(key, [0, 0])
            a[0] += sum(r["converged"] for r in rr)
            a[1] += len(rr)
        conv[fac] = {k: 100.0 * v[0] / v[1] for k, v in conv[fac].items()}
    return out, conv


def pooled_bias(rows, cells, select=lambda c: True, mcse=False):
    """% relative bias over all converged fits of the selected cells (each fit against its cell's truth);
    with mcse, also the Monte Carlo SE of that mean."""
    cmap = {c["id"]: c for c in cells}
    acc = {p: [] for p in PARAMS}
    for cid, rr in by_cell(rows).items():
        c = cmap[cid]
        if not select(c):
            continue
        ind = indicators(rr, c)
        for p in PARAMS:
            est, t, _ = ind[p]
            acc[p].extend(list(100.0 * (est - t) / t))
    if mcse:
        return {p: (float(np.mean(v)), float(np.std(v, ddof=1) / math.sqrt(len(v)))) for p, v in acc.items()}
    return {p: float(np.mean(v)) for p, v in acc.items()}


def ci_variants(rows, cell):
    """Non-coverage of sigma0 and sigma1 under other readings of the interval (hypotheses for Table 3)."""
    ok = [r for r in rows if r["converged"]]
    out = {}
    for p, var in VAR.items():
        t = cell[var]
        v = np.array([r[var] for r in ok])
        se = np.array([r[var + "_se"] for r in ok])
        has = np.isfinite(se)
        vv, ss = v[has], se[has]
        sd = np.sqrt(np.clip(vv, 1e-300, None))
        out[p] = {"sd_scale": float(np.mean(np.abs(sd - math.sqrt(t)) > Z * ss / (2 * sd))),
                  "log_scale": float(np.mean(np.abs(np.log(np.clip(vv, 1e-300, None)) - math.log(t)) > Z * ss / np.clip(vv, 1e-300, None))),
                  "boundary_as_miss": float((np.sum(np.abs(vv - t) > Z * ss) + np.sum(~has)) / len(v)),
                  "n": int(len(v))}
    return out


def run_summary(rows, main_cells):
    """Tables 1-3 and the text's numbers from one run of the main grid."""
    bc = by_cell(rows)
    run = {"cells": {c["id"]: summary(bc[c["id"]], c) for c in main_cells}}
    run["sd_scale"] = {c["id"]: {p: summary(bc[c["id"]], c, scale="sd")[p] for p in ("sigma0", "sigma1")} for c in main_cells}
    run["interior"] = {c["id"]: summary(bc[c["id"]], c, rule="interior") for c in main_cells}
    run["hessian"] = {c["id"]: summary(bc[c["id"]], c, rule="hessian") for c in main_cells}
    run["ci_variants"] = {c["id"]: ci_variants(bc[c["id"]], c) for c in main_cells}
    run["marginals"], run["converged_by_factor"] = marginals(rows, main_cells)
    run["pooled_bias"] = pooled_bias(rows, main_cells)
    run["pooled_bias_by_icc"] = {f"{icc:.2f}": pooled_bias(rows, main_cells, lambda c, i=icc: c["icc"] == i)
                                 for icc in sim.ICC_LEVELS}
    run["n_replicates"] = len(rows)
    run["converged_range"] = [min(v["converged_pct"] for v in run["cells"].values()),
                              max(v["converged_pct"] for v in run["cells"].values())]
    ok = [r for r in rows if r["converged"]]
    bad = [r for r in rows if not r["converged"]]
    run["converged_vs_not"] = {
        k: {"converged": float(np.mean([r[k] for r in ok])), "not_converged": float(np.mean([r[k] for r in bad])),
            "converged_se": float(np.std([r[k] for r in ok], ddof=1) / math.sqrt(len(ok))),
            "not_converged_se": float(np.std([r[k] for r in bad], ddof=1) / math.sqrt(len(bad)))}
        for k in ("prevalence", "z_mean", "z_sd", "x_mean", "x_sd")}
    icc04 = [r for r in rows if r["cell"].endswith("icc0.04")]
    run["converged_vs_not_icc0.04"] = {
        "prevalence": {"converged": float(np.mean([r["prevalence"] for r in icc04 if r["converged"]])),
                       "not_converged": float(np.mean([r["prevalence"] for r in icc04 if not r["converged"]]))}}
    run["negative_variances_in_converged"] = int(sum(r["var0"] < 0 or r["var1"] < 0 for r in ok))
    run["status_counts"] = {s: sum(r["status"] == s for r in rows) for s in sorted(set(r["status"] for r in rows))}
    run["qpoints_counts"] = {f"{q:g}": sum(r["qpoints"] == q for r in rows) for q in sorted(set(r["qpoints"] for r in rows))}
    return run


def main():
    rec_dir, out = Path(sys.argv[1]), sys.argv[2]
    extra_path = Path(sys.argv[sys.argv.index("--extra") + 1]) if "--extra" in sys.argv else None
    main_cells = sim.cells("main")
    doc = {"about": "Every summary of the simulation study the comparison uses (summarize.py).", "runs": {}}
    doc["runs"]["main"] = run_summary(read(rec_dir / "main.csv.gz"), main_cells)

    if (rec_dir / "main_run2.csv.gz").exists():
        extra = {"about": "Summaries of the second run and of the hypothesis variants (summarize.py, from a full run's "
                          "records, which the repository does not keep).",
                 "second": run_summary(read(rec_dir / "main_run2.csv.gz"), main_cells), "variants": {}}
        for f in sorted(rec_dir.glob("var_*.csv.gz")):
            bc = by_cell(read(f))
            extra["variants"][f.name[4:-7]] = {c["id"]: summary(bc[c["id"]], c) for c in main_cells if c["id"] in bc}
        extra = r6(extra)
        if extra_path:
            extra_path.write_text(json.dumps(extra, indent=1) + "\n")
    else:
        extra = json.load(open(extra_path))
    doc["runs"]["second"] = extra["second"]
    doc["variants"] = dict(extra["variants"])
    # the main run's first 200 replicates: the variants' baseline
    rows = [r for r in read(rec_dir / "main.csv.gz") if r["rep"] < 200]
    bc = by_cell(rows)
    doc["variants"]["baseline"] = {c["id"]: summary(bc[c["id"]], c) for c in main_cells}

    prev_cells = sim.cells("prevalence")
    rows = read(rec_dir / "prevalence.csv.gz")
    bc = by_cell(rows)
    pc = {c["id"]: summary(bc[c["id"]], c) for c in prev_cells}
    pooled = {}
    for prev in ("0.10", "0.34", "0.45"):
        for name, sel in (("all_cells", lambda c: True), ("size5", lambda c: c["size"] == 5),
                          ("groups30", lambda c: c["groups"] == 30)):
            cs = [c for c in prev_cells if f"{c['prevalence']:.2f}" == prev and sel(c)]
            rr = [r for c in cs for r in bc[c["id"]]]
            pb = pooled_bias(rr, cs, mcse=True)
            s = {"converged_pct": 100.0 * sum(r["converged"] for r in rr) / len(rr), "n": len(rr),
                 "with_se_pct": 100.0 * sum(r["converged"] and math.isfinite(r["var0_se"]) for r in rr) / len(rr),
                 "prevalence_observed": float(np.mean([r["prevalence"] for r in rr]))}
            for p in PARAMS:
                miss = []
                for c in cs:
                    miss.extend([m for m in indicators(bc[c["id"]], c)[p][2] if np.isfinite(m)])
                s[p] = {"bias_pct": pb[p][0], "bias_mcse": pb[p][1], "noncoverage": float(np.mean(miss)), "n_ci": len(miss)}
            pooled.setdefault(name, {})[prev] = s
    doc["prevalence"] = {"cells": pc, "pooled": pooled}

    rob_cells = sim.cells("robustness")
    bc = by_cell(read(rec_dir / "robustness.csv.gz"))
    doc["robustness"] = {"cells": {c["id"]: summary(bc[c["id"]], c) for c in rob_cells},
                         "sd_scale": {c["id"]: {p: summary(bc[c["id"]], c, scale="sd")[p] for p in ("sigma0", "sigma1")}
                                      for c in rob_cells}}
    Path(out).write_text(json.dumps(r6(doc), indent=1) + "\n")


if __name__ == "__main__":
    main()

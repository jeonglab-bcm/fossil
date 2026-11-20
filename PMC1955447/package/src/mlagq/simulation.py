"""The simulation design of Moineddin, Matheson and Glazier (2007), and its summaries.

Data (Methods): J groups of n individuals; x_ij and z_j standard normal; u0j ~ N(0, var0) and u1j ~ N(0, var1)
independent; logit p_ij = g00 + g10 x_ij + g01 z_j + g11 x_ij z_j + u0j + u1j x_ij; y_ij ~ Bernoulli(p_ij).
Main grid: J 30, 50, 100; n 5, 30, 50; var0 0.13, 0.67, 2.0 (ICC 0.04, 0.17, 0.38); var1 1;
gamma = (-1.0, 0.3, 0.3, 0.3). Prevalence study (Table 4): gamma (-3, .3, .3, .3), (-1, .3, .3, .3),
(-.3, -.3, -.3, -.3), var0 = var1 = 1. Robustness study (Table 5): eight models for the distributions of
(z_j, u0j, u1j, x_ij).

Each data set is drawn from its own NumPy PCG64 stream, seeded by (base seed, study, cell, replicate), so a data
set is the same whatever else runs.
"""

from __future__ import annotations

import math

import numpy as np

from .core import GroupedData, fit

FIXED = ("g00", "g01", "g10", "g11")
PARAMS = FIXED + ("sigma0", "sigma1")
GAMMA_MAIN = (-1.0, 0.3, 0.3, 0.3)
VAR0_LEVELS = (0.13, 0.67, 2.0)
ICC_LEVELS = (0.04, 0.17, 0.38)
GROUPS_LEVELS = (30, 50, 100)
SIZE_LEVELS = (5, 30, 50)
PREVALENCE_GAMMAS = {0.10: (-3.0, 0.3, 0.3, 0.3), 0.34: (-1.0, 0.3, 0.3, 0.3), 0.45: (-0.3, -0.3, -0.3, -0.3)}

# Table 5: (z_j, u0j, u1j, x_ij); ("N", var), ("U", a, b), ("t", df)
ROBUSTNESS_MODELS = {
    1: (("N", 1), ("N", 1), ("N", 1), ("N", 1)),
    2: (("N", 1), ("N", 1), ("N", 4), ("N", 4)),
    3: (("N", 4), ("N", 4), ("N", 4), ("N", 4)),
    4: (("U", -0.5, 0.5), ("N", 1), ("N", 1), ("U", -0.5, 0.5)),
    5: (("U", -0.5, 0.5), ("U", -2, 2), ("U", -2, 2), ("U", -0.5, 0.5)),
    6: (("N", 1), ("t", 3), ("t", 3), ("N", 1)),
    7: (("t", 3), ("t", 3), ("t", 3), ("t", 3)),
    8: (("t", 5), ("t", 5), ("t", 5), ("t", 5)),
}
STUDY_CODES = {"main": 1, "prevalence": 2, "robustness": 3}


def dist_variance(spec):
    kind = spec[0]
    if kind == "N":
        return float(spec[1])
    if kind == "U":
        return (spec[2] - spec[1]) ** 2 / 12.0
    if kind == "t":
        return spec[1] / (spec[1] - 2.0)
    raise ValueError(spec)


def draw(rng, spec, size):
    kind = spec[0]
    if kind == "N":
        return rng.standard_normal(size) * math.sqrt(spec[1])
    if kind == "U":
        return rng.uniform(spec[1], spec[2], size)
    if kind == "t":
        return rng.standard_t(spec[1], size)
    raise ValueError(spec)


def seed_for(base, study, cell, rep):
    return np.random.SeedSequence([int(base), STUDY_CODES[study], int(cell), int(rep)])


def generate(rng, n_groups, group_size, gamma=GAMMA_MAIN, var0=1.0, var1=1.0, dists=None):
    """One data set as GroupedData (fixed effects 1, z, x, x z; random intercept and slope on x).

    dists: (z, u0, u1, x) distribution specs; default normal with variances 1, var0, var1, 1.
    """
    if dists is None:
        dists = (("N", 1.0), ("N", var0), ("N", var1), ("N", 1.0))
    J, n = int(n_groups), int(group_size)
    z = draw(rng, dists[0], J)
    u0 = draw(rng, dists[1], J)
    u1 = draw(rng, dists[2], J)
    x = draw(rng, dists[3], (J, n)).reshape(J, n)
    g00, g01, g10, g11 = gamma
    eta = g00 + g01 * z[:, None] + (g10 + g11 * z[:, None]) * x + u0[:, None] + u1[:, None] * x
    p = 1.0 / (1.0 + np.exp(-eta))
    y = (rng.random((J, n)) < p).astype(float)
    ones = np.ones((J, n))
    zz = np.repeat(z[:, None], n, 1)
    X = np.stack([ones, zz, x, x * zz], axis=2)
    Z = np.stack([ones, x], axis=2)
    return GroupedData(y, X, Z, np.ones((J, n)), list(FIXED), ["u0", "u1"])


def fit_replicate(data, gamma, var0, var1, cov=False, absxconv=1e-8, **kw):
    """Fit the model from the true values, as the paper did ("initial values as the true values")."""
    start = list(gamma) + ([var0, 0.0, var1] if cov else [var0, var1])
    return fit(data, start, cov=cov, absxconv=absxconv, **kw)


def replicate_record(f, data):
    """The numbers a replicate contributes to the summaries."""
    est = f.estimate
    se = f.se
    p = data.p
    i1 = p + (2 if f.cov else 1)
    rec = {"converged": bool(f.converged), "status": f.status, "iterations": int(f.iterations),
           "qpoints": int(f.qpoints), "hessian_pd": bool(f.hessian_pd), "loglik": float(f.loglik),
           "prevalence": float(data.y.sum() / data.mask.sum())}
    for i, name in enumerate(FIXED):
        rec[name] = float(est[i])
        rec[name + "_se"] = float(se[i])
    rec["var0"], rec["var0_se"] = float(est[p]), float(se[p])
    rec["var1"], rec["var1_se"] = float(est[i1]), float(se[i1])
    if f.cov:
        rec["cov01"], rec["cov01_se"] = float(est[p + 1]), float(se[p + 1])
    return rec


Z975 = 1.959963984540054


def summarize(records, gamma, var0, var1, scale="sd", ci="variance", require_hessian=False):
    """Convergence (%), % relative bias and non-coverage of the 95% Wald interval, over converged fits.

    scale: the scale of sigma0 and sigma1 for bias, "sd" (sqrt of the variance estimate, against sqrt of the
    true variance) or "variance". ci: the Wald interval for the random effects, on the "variance" (the
    parameter as fitted) or the "sd" scale (delta method).
    """
    ok = [r for r in records if r["converged"] and (r["hessian_pd"] or not require_hessian)]
    out = {"n": len(records), "n_converged": len(ok),
           "converged_pct": 100.0 * len(ok) / len(records) if records else float("nan")}
    true = dict(zip(FIXED, gamma))
    for name in FIXED:
        est = np.array([r[name] for r in ok])
        se = np.array([r[name + "_se"] for r in ok])
        out[name] = _bias_cover(est, se, true[name])
    for name, var_name, tv in (("sigma0", "var0", var0), ("sigma1", "var1", var1)):
        v = np.array([r[var_name] for r in ok])
        vse = np.array([r[var_name + "_se"] for r in ok])
        if scale == "sd":
            est_b, t_b = np.sqrt(np.clip(v, 0, None)), math.sqrt(tv)
        else:
            est_b, t_b = v, tv
        b = _bias_cover(est_b, None, t_b)
        if ci == "variance":
            c = _bias_cover(v, vse, tv)
        else:
            sd = np.sqrt(np.clip(v, 0, None))
            c = _bias_cover(sd, vse / np.where(sd > 0, 2 * sd, np.nan), math.sqrt(tv))
        out[name] = {"bias_pct": b["bias_pct"], "bias_mcse": b["bias_mcse"], "noncoverage": c["noncoverage"],
                     "n_ci": c["n_ci"]}
    return out


def _bias_cover(est, se, true):
    n = est.size
    res = {"bias_pct": float(100.0 * (est.mean() - true) / true) if n else float("nan"),
           "bias_mcse": float(100.0 * est.std(ddof=1) / math.sqrt(n) / abs(true)) if n > 1 else float("nan")}
    if se is not None:
        okse = np.isfinite(se)
        miss = np.abs(est[okse] - true) > Z975 * se[okse]
        res["noncoverage"] = float(miss.mean()) if okse.any() else float("nan")
        res["n_ci"] = int(okse.sum())
    return res


def cells(study):
    """The cells of a study: dicts with id, groups, size, gamma, var0, var1, dists and labels."""
    out = []
    if study == "main":
        for J in GROUPS_LEVELS:
            for n in SIZE_LEVELS:
                for v0, icc in zip(VAR0_LEVELS, ICC_LEVELS):
                    out.append({"id": f"J{J}_n{n}_icc{icc:.2f}", "groups": J, "size": n, "icc": icc,
                                "gamma": GAMMA_MAIN, "var0": v0, "var1": 1.0, "dists": None})
    elif study == "prevalence":
        for prev, gamma in PREVALENCE_GAMMAS.items():
            for J in GROUPS_LEVELS:
                for n in SIZE_LEVELS:
                    out.append({"id": f"p{prev:.2f}_J{J}_n{n}", "groups": J, "size": n, "prevalence": prev,
                                "gamma": gamma, "var0": 1.0, "var1": 1.0, "dists": None})
    elif study == "robustness":
        for model, dists in ROBUSTNESS_MODELS.items():
            for J in GROUPS_LEVELS:
                for n in SIZE_LEVELS:
                    out.append({"id": f"m{model}_J{J}_n{n}", "groups": J, "size": n, "model": model,
                                "gamma": GAMMA_MAIN, "var0": dist_variance(dists[1]),
                                "var1": dist_variance(dists[2]), "dists": dists})
    else:
        raise ValueError(f"unknown study {study!r}")
    for i, c in enumerate(out):
        c["index"] = i
    return out


def run_replicate(study, cell, rep, base_seed, cov=True, **kw):
    """Draw replicate ``rep`` of a cell from its own stream, fit it from the true values, return its record."""
    rng = np.random.default_rng(seed_for(base_seed, study, cell["index"], rep))
    data = generate(rng, cell["groups"], cell["size"], cell["gamma"], cell["var0"], cell["var1"], cell["dists"])
    f = fit_replicate(data, cell["gamma"], cell["var0"], cell["var1"], cov=cov, **kw)
    rec = replicate_record(f, data)
    z = data.X[:, 0, 1]
    x = data.X[:, :, 2].ravel()
    rec.update({"z_mean": float(z.mean()), "z_sd": float(z.std(ddof=1)), "x_mean": float(x.mean()),
                "x_sd": float(x.std(ddof=1))})
    return rec, data

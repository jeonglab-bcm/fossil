"""The simulation study of Chen, Shi, Qian and Azen (2014), as described in its Methods and Additional file 1.

Design: Z ~ Beta(6, 2); X ~ Bernoulli(p_x), logit(p_x) = alpha0 + alpha1 Z; Y ~ Bernoulli(p_y) with
log(p_y) = beta0 + beta1 X + beta2 Z (linear confounder) or beta0 + beta1 X + beta2 Z + 0.5 beta2 Z^2
(quadratic), beta1 = log(RR), alpha1 = beta2 = log(2) (moderate) or log(4) (strong). alpha0 and beta0 of the 24
scenarios are those of Additional file 1.

Contamination: the outcome is reversed (Y -> 1 - Y) for the records whose p_y is in the bottom or the top rate/2
of the distribution of p_y (2%: bottom 1% and top 1%; 5%: bottom 2.5% and top 2.5%). By default the two cut-offs
are the quantiles of p_y in the population of the scenario (cutoffs='population', computed exactly by
population_cutoffs), so the number of records flipped varies from data set to data set, as it does when fixed
cut-offs are applied to each simulated data set. With cutoffs='sample' each data set has exactly
ceil(n x rate / 2) records flipped per tail (n = 1500: 15 and 38; n = 500: 5 and 13), ranked within the data set.
Other readings are options.

Fitted models: Y on X and Z (and Z^2 for the quadratic confounder), by robust Poisson and by log-binomial
regression with the COPY method. Performance over the replicates: relative bias (%) of the log RR, its
empirical standard error and the MSE (squared bias plus variance), all on the log scale.
"""

from __future__ import annotations

import math

import numpy as np

from .core import DEFAULT_COPIES, log_binomial_coef, poisson_coef

ALPHA0 = {"moderate": -0.5188, "strong": -1.0425}
ASSOC = {"moderate": math.log(2), "strong": math.log(4)}
# beta0 of Additional file 1: (RR, outcome %, confounder form, association level)
BETA0 = {
    (1.5, 10, "linear", "moderate"): -3.0518, (1.5, 10, "linear", "strong"): -3.5885,
    (1.5, 10, "nonlinear", "moderate"): -3.2636, (1.5, 10, "nonlinear", "strong"): -4.0302,
    (1.5, 25, "linear", "moderate"): -2.1349, (1.5, 25, "linear", "strong"): -2.6714,
    (1.5, 25, "nonlinear", "moderate"): -2.3473, (1.5, 25, "nonlinear", "strong"): -3.1136,
    (1.5, 40, "linear", "moderate"): -1.6649, (1.5, 40, "linear", "strong"): -2.2016,
    (1.5, 40, "nonlinear", "moderate"): -1.8769, (1.5, 40, "nonlinear", "strong"): -2.6440,
    (2.0, 10, "linear", "moderate"): -3.2346, (2.0, 10, "linear", "strong"): -3.7722,
    (2.0, 10, "nonlinear", "moderate"): -3.4472, (2.0, 10, "nonlinear", "strong"): -4.2161,
    (2.0, 25, "linear", "moderate"): -2.3191, (2.0, 25, "linear", "strong"): -2.8561,
    (2.0, 25, "nonlinear", "moderate"): -2.5300, (2.0, 25, "nonlinear", "strong"): -3.3006,
    (2.0, 40, "linear", "moderate"): -1.8485, (2.0, 40, "linear", "strong"): -2.3863,
    (2.0, 40, "nonlinear", "moderate"): -2.0618, (2.0, 40, "nonlinear", "strong"): -2.8298,
}
SCENARIOS = list(BETA0)
CONTAMINATION = (0.0, 0.02, 0.05)


def scenario(rr, outcome, form, level):
    """Parameters of one of the 24 scenarios (outcome in %, form 'linear' or 'nonlinear', level 'moderate' or
    'strong')."""
    key = (float(rr), int(outcome), form, level)
    if key not in BETA0:
        raise ValueError(f"no scenario {key}; RR is 1.5 or 2.0, outcome 10, 25 or 40, form linear or nonlinear, "
                         "level moderate or strong")
    return {"rr": key[0], "outcome": key[1], "form": form, "level": level, "alpha0": ALPHA0[level],
            "alpha1": ASSOC[level], "beta0": BETA0[key], "beta1": math.log(key[0]), "beta2": ASSOC[level]}


def outcome_probability(s, x, z):
    """True p_y of the scenario s for exposure x and confounder z."""
    lp = s["beta0"] + s["beta1"] * x + s["beta2"] * z
    if s["form"] == "nonlinear":
        lp = lp + 0.5 * s["beta2"] * z * z
    return np.exp(lp)


def generate(s, n, reps, rng):
    """reps data sets of n subjects: (z, x, y, p_y), each of shape (reps, n)."""
    z = rng.beta(6, 2, (reps, n))
    px = 1 / (1 + np.exp(-(s["alpha0"] + s["alpha1"] * z)))
    x = (rng.random((reps, n)) < px).astype(float)
    p = outcome_probability(s, x, z)
    if (p > 1).any():
        raise ValueError("p_y > 1")
    y = (rng.random((reps, n)) < p).astype(float)
    return z, x, y, p


def n_flipped(n, rate, count="ceil"):
    """Records flipped per tail: ceil(n rate / 2) ('ceil'), floor ('floor') or rounded half up ('round')."""
    k = n * rate / 2
    if count == "ceil":
        return int(math.ceil(k - 1e-9))
    if count == "floor":
        return int(math.floor(k + 1e-9))
    if count == "round":
        return int(math.floor(k + 0.5))
    raise ValueError(f"count must be ceil, floor or round, not {count!r}")


def _gauss(m=96):
    x, w = np.polynomial.legendre.leggauss(m)
    return x, w


def population_cdf(s, c):
    """P(p_y <= c) in the population of scenario s, for an array of c > 0 (exact up to quadrature)."""
    c = np.atleast_1d(np.asarray(c, float))
    gx, gw = _gauss()
    out = np.zeros_like(c)
    quad = 0.5 * s["beta2"] if s["form"] == "nonlinear" else 0.0
    for x in (0.0, 1.0):
        # log p_y = beta0 + beta1 x + beta2 z + quad z^2 is increasing in z on [0, 1]: p_y <= c iff z <= zc
        a0 = s["beta0"] + s["beta1"] * x - np.log(c)
        if quad:
            disc = s["beta2"] ** 2 - 4 * quad * a0
            zc = (-s["beta2"] + np.sqrt(np.maximum(disc, 0))) / (2 * quad)
        else:
            zc = -a0 / s["beta2"]
        zc = np.clip(zc, 0.0, 1.0)
        z = 0.5 * zc[:, None] * (gx[None, :] + 1)
        dens = 42 * z**5 * (1 - z)                      # Beta(6, 2)
        px = 1 / (1 + np.exp(-(s["alpha0"] + s["alpha1"] * z)))
        f = dens * (px if x else 1 - px)
        out += 0.5 * zc * (f * gw[None, :]).sum(1)
    return out


def population_cutoffs(s, rate):
    """The rate/2 and 1 - rate/2 quantiles of p_y in the population of scenario s (bisection on log p_y)."""
    lo_all = s["beta0"]
    hi_all = s["beta0"] + s["beta1"] + s["beta2"] + (0.5 * s["beta2"] if s["form"] == "nonlinear" else 0.0)
    out = []
    for q in (rate / 2, 1 - rate / 2):
        a, b = lo_all - 1e-9, hi_all + 1e-9
        for _ in range(200):
            m = 0.5 * (a + b)
            if population_cdf(s, np.exp(m))[0] < q:
                a = m
            else:
                b = m
        out.append(float(np.exp(0.5 * (a + b))))
    return tuple(out)


def contaminate(y, p, rate, tails="both", count="ceil", cutoffs=None):
    """Reverse the outcome of the records with the most extreme p (per data set, along the last axis).

    cutoffs: (low, high) values of p: flip p <= low and p >= high ('both'), p <= the low cut-off of the whole
    rate ('bottom'; pass its value as low) or p >= high ('top'). Without cutoffs, flip a fixed number of
    records per data set, ranked by p: ceil(n rate/2) per tail ('count' floor or round for other counts).
    tails: 'both' (rate/2 at the bottom and rate/2 at the top), 'bottom' or 'top' (the whole rate in one tail).
    """
    y = np.array(y, dtype=float, copy=True)
    if rate == 0:
        return y
    if cutoffs is not None:
        lo, hi = cutoffs
        if tails == "both":
            flip = (p <= lo) | (p >= hi)
        elif tails == "bottom":
            flip = p <= lo
        elif tails == "top":
            flip = p >= hi
        else:
            raise ValueError(f"tails must be both, bottom or top, not {tails!r}")
        return np.where(flip, 1 - y, y)
    n = y.shape[-1]
    k = n_flipped(n, rate, count)
    order = np.argsort(p, axis=-1, kind="stable")
    if tails == "both":
        idx = np.concatenate([order[..., :k], order[..., n - k:]], axis=-1)
    elif tails == "bottom":
        idx = order[..., :2 * k]
    elif tails == "top":
        idx = order[..., n - 2 * k:]
    else:
        raise ValueError(f"tails must be both, bottom or top, not {tails!r}")
    np.put_along_axis(y, idx, 1 - np.take_along_axis(y, idx, axis=-1), axis=-1)
    return y


def design_matrix(x, z, quadratic):
    cols = [np.ones_like(z), x, z] + ([z * z] if quadratic else [])
    return np.stack(cols, axis=-1)


def run_scenario(s, n=1500, reps=1000, seed=0, rates=CONTAMINATION, tails="both", count="ceil",
                 quadratic=None, rank_by="true", cutoffs="population", copies=DEFAULT_COPIES, chunk=250):
    """Simulate one scenario and fit both models at each contamination rate.

    The same reps data sets are contaminated at every rate. quadratic: fit Z^2 too (default: when the
    confounder is quadratic). cutoffs: 'population' flips the records beyond the population quantiles of p_y;
    'sample' a fixed number per data set (count). rank_by (with 'sample'): 'true' ranks records by the true
    p_y; 'fitted' by p_y fitted by the uncontaminated log-binomial model. Returns {rate: {"lb": log RR estimates, "rp": ..., "copy": bool array
    (COPY used), "converged": bool array (log-binomial fit reported converged), "flipped": records flipped}}.
    """
    if quadratic is None:
        quadratic = s["form"] == "nonlinear"
    if cutoffs not in ("population", "sample"):
        raise ValueError("cutoffs must be population or sample")
    cut = {}
    if cutoffs == "population":
        for r in rates:
            if r:
                whole = population_cutoffs(s, 2 * r)          # one tail holding the whole rate
                half = population_cutoffs(s, r)
                cut[r] = {"both": half, "bottom": (whole[0], None), "top": (None, whole[1])}[tails]
    rng = np.random.default_rng(seed)
    out = {r: {"lb": [], "rp": [], "copy": [], "converged": [], "flipped": []} for r in rates}
    for start in range(0, reps, chunk):
        m = min(chunk, reps - start)
        z, x, y, p = generate(s, n, m, rng)
        X = design_matrix(x, z, quadratic)
        rank = p
        if rank_by == "fitted":
            b, _ = log_binomial_coef(X, y, copies=copies)
            rank = np.exp(np.matmul(X, b[..., None])[..., 0])
        elif rank_by != "true":
            raise ValueError("rank_by must be true or fitted")
        if rank_by == "fitted" and cutoffs == "population":
            raise ValueError("rank_by='fitted' needs cutoffs='sample'")
        for r in rates:
            yc = contaminate(y, rank, r, tails, count, cut.get(r))
            out[r]["flipped"].append((yc != y).sum(1))
            brp, _ = poisson_coef(X, yc)
            blb, info = log_binomial_coef(X, yc, copies=copies)
            out[r]["rp"].append(brp[:, 1])
            out[r]["lb"].append(blb[:, 1])
            out[r]["copy"].append(info["method"] == "copy")
            out[r]["converged"].append(info["converged"])
    return {r: {k: np.concatenate(v) for k, v in d.items()} for r, d in out.items()}


def summarize(est, beta1):
    """Relative bias (%), empirical SE and MSE of log RR estimates, with their Monte Carlo standard errors."""
    est = np.asarray(est, float)
    est = est[np.isfinite(est)]
    R = est.size
    mean = est.mean()
    sd = est.std(ddof=1)
    bias = mean - beta1
    sq = (est - beta1) ** 2
    return {"reps": R, "mean": mean, "relbias": 100 * bias / beta1, "se": sd, "mse": bias**2 + sd**2,
            "relbias_mcse": 100 * sd / math.sqrt(R) / abs(beta1), "se_mcse": sd / math.sqrt(2 * (R - 1)),
            "mse_mcse": sq.std(ddof=1) / math.sqrt(R)}

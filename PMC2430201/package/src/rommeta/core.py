"""Effect measures for continuous outcomes and DerSimonian-Laird random-effects pooling.

As in Friedrich, Adhikari and Beyene (2008), Methods and Appendix:

- MD:  mean_e - mean_c, Var = sd_e^2/n_e + sd_c^2/n_c.
- SMD: (mean_e - mean_c)/sd_pool x [1 - 3/(4N - 9)], Var = N/(n_e n_c) + SMD^2/(2(N - 3.94)),
       N = n_e + n_c, sd_pool = sqrt(((n_e - 1) sd_e^2 + (n_c - 1) sd_c^2)/(N - 2)).
- RoM: ln(mean_e/mean_c), Var = sd_e^2/(n_e mean_e^2) + sd_c^2/(n_c mean_c^2) (first-order delta method),
       pooled on the log scale and back-transformed.

Pooling: inverse-variance weights w = 1/Var; Q = sum w (y - y_FE)^2; DerSimonian-Laird
tau^2 = max(0, (Q - (k - 1))/(sum w - sum w^2/sum w)); random-effects weights 1/(1/w + tau^2);
95% CI = estimate +/- z SE with z = 1.96 as printed; I^2 = max(0, (Q - (k - 1))/Q).

Every function works on NumPy arrays and broadcasts; `pool` pools along the last axis, so one call
pools many meta-analyses at once (the simulation pools 10,000 at a time). Studies whose effect is not
finite (a RoM with a non-positive mean) are left out of their meta-analysis.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

MEASURES = ("MD", "SMD", "RoM")
Z95 = 1.96  # the paper's multiplier; scipy.stats.norm.ppf(0.975) = 1.959963984540054


def effect_sizes(mean_e, sd_e, n_e, mean_c, sd_c, n_c, measure: str, sd_pool_literal: bool = False,
                 small_sample_correction: bool = True):
    """Per-study effect size and its variance: (y, v), arrays broadcast from the inputs.

    For RoM, y is ln(mean_e/mean_c); it is NaN when either mean is not positive.
    `sd_pool_literal` uses the pooled SD as printed in the paper's Appendix, with a stray "- 1" under
    the root (kept only to test that reading; the standard pooled SD is the default).
    """
    mean_e, sd_e, mean_c, sd_c = (np.asarray(x, dtype=float) for x in (mean_e, sd_e, mean_c, sd_c))
    n_e, n_c = np.asarray(n_e, dtype=float), np.asarray(n_c, dtype=float)
    if measure == "MD":
        return mean_e - mean_c, sd_e**2 / n_e + sd_c**2 / n_c
    if measure == "SMD":
        N = n_e + n_c
        ss = (n_e - 1) * sd_e**2 + (n_c - 1) * sd_c**2 - (1.0 if sd_pool_literal else 0.0)
        sd_pool = np.sqrt(ss / (N - 2))
        g = (mean_e - mean_c) / sd_pool * ((1 - 3 / (4 * N - 9)) if small_sample_correction else 1.0)
        return g, N / (n_e * n_c) + g**2 / (2 * (N - 3.94))
    if measure == "RoM":
        with np.errstate(invalid="ignore", divide="ignore"):
            ok = (mean_e > 0) & (mean_c > 0)
            y = np.where(ok, np.log(np.where(ok, mean_e / np.where(ok, mean_c, 1.0), 1.0)), np.nan)
            v = sd_e**2 / (n_e * mean_e**2) + sd_c**2 / (n_c * mean_c**2)
        return y, v
    raise ValueError(f"measure must be one of {MEASURES}, not {measure!r}")


def pool(y, v, z: float = Z95):
    """DerSimonian-Laird random-effects pooling along the last axis.

    Returns a dict of arrays (one value per meta-analysis): estimate, se, ci_low, ci_high, z, p,
    q, df, k, tau2, i2 (a fraction, truncated at 0), fixed (the fixed-effect estimate) and fixed_se.
    Studies with a non-finite y or v are left out.
    """
    y, v = np.asarray(y, dtype=float), np.asarray(v, dtype=float)
    ok = np.isfinite(y) & np.isfinite(v) & (v > 0)
    w = np.where(ok, 1.0 / np.where(ok, v, 1.0), 0.0)
    y0 = np.where(ok, y, 0.0)
    k = ok.sum(-1)
    sw = w.sum(-1)
    with np.errstate(invalid="ignore", divide="ignore"):
        fe = (w * y0).sum(-1) / sw
        q = (w * (y0 - fe[..., None]) ** 2).sum(-1)
        df = k - 1
        c = sw - (w**2).sum(-1) / sw
        tau2 = np.where(q > df, (q - df) / c, 0.0)
        ws = 1.0 / (np.where(ok, v, np.inf) + tau2[..., None])  # 0 for a study left out
        sws = ws.sum(-1)
        est = (ws * y0).sum(-1) / sws
        se = np.sqrt(1.0 / sws)
        zstat = est / se
        i2 = np.where(q > 0, np.maximum(0.0, (q - df) / np.where(q > 0, q, 1.0)), 0.0)
    p = _two_sided_p(zstat)
    return {"estimate": est, "se": se, "ci_low": est - z * se, "ci_high": est + z * se, "z": zstat, "p": p,
            "q": q, "df": df, "k": k, "tau2": tau2, "i2": i2, "fixed": fe, "fixed_se": np.sqrt(1.0 / sw)}


def _two_sided_p(zstat):
    zstat = np.abs(np.asarray(zstat, dtype=float))
    erfc = np.vectorize(math.erfc, otypes=[float])
    return erfc(zstat / math.sqrt(2.0))


def two_sided_p(zstat):
    """Two-sided normal p-value of a z statistic (array or number)."""
    return _two_sided_p(zstat)


@dataclass(frozen=True)
class MetaResult:
    """One random-effects meta-analysis, on the reporting scale (RoM back-transformed)."""

    measure: str
    k: int
    estimate: float
    ci_low: float
    ci_high: float
    p: float
    log_estimate: float | None  # RoM only: the pooled ln(RoM)
    se: float  # of the pooled estimate on the analysis scale (ln RoM for RoM)
    q: float
    tau2: float
    i2: float  # percent

    def as_dict(self) -> dict:
        return dict(self.__dict__)


def meta_analysis(mean_e, sd_e, n_e, mean_c, sd_c, n_c, measure: str = "RoM", z: float = Z95) -> MetaResult:
    """Random-effects (DerSimonian-Laird) meta-analysis of one set of studies.

    The inputs are per-study sequences: means, SDs and sizes of the experimental and control arms.
    """
    arrays = [np.asarray(x, dtype=float) for x in (mean_e, sd_e, n_e, mean_c, sd_c, n_c)]
    if len({a.shape for a in arrays}) != 1 or arrays[0].ndim != 1:
        raise ValueError("give one value per study for each of mean_e, sd_e, n_e, mean_c, sd_c, n_c")
    if arrays[0].size < 2:
        raise ValueError("a meta-analysis needs at least two studies")
    if np.any(arrays[2] < 2) or np.any(arrays[5] < 2):
        raise ValueError("each arm needs at least two patients")
    y, v = effect_sizes(*arrays, measure)
    r = pool(y, v, z=z)
    est, lo, hi = float(r["estimate"]), float(r["ci_low"]), float(r["ci_high"])
    log_est = None
    if measure == "RoM":
        log_est, est, lo, hi = est, math.exp(est), math.exp(lo), math.exp(hi)
    return MetaResult(measure=measure, k=int(r["k"]), estimate=est, ci_low=lo, ci_high=hi, p=float(r["p"]),
                      log_estimate=log_est, se=float(r["se"]), q=float(r["q"]), tau2=float(r["tau2"]),
                      i2=100.0 * float(r["i2"]))

"""The simulation study of Friedrich, Adhikari and Beyene (2008): k trials per meta-analysis, each arm's
mean and SD computed from n values, pooled with MD, SMD and RoM, 10,000 replicates per scenario.

Design (Methods, "Design of the Simulation Study"):

- Control arm: values from a distribution with mean 100 (`control_mean`) and SD 10, 40 or 70; the
  experimental arm: mean 100 + effect x SD, the same SD. The true MD is effect x SD, the true SMD the
  effect, the true RoM 1 + effect x SD/100.
- Heterogeneity tau (in SD units): each trial's arm means are shifted by independent normal draws with
  SD tau/sqrt(2) x SD, so their difference has SD tau x SD ("added to experimental and control group means").
- The skewed scenario: values from a mixture of three normals, SD 0.24, centred at 0.84, 1.42, 1.92 and
  weighted 0.77, 0.17, 0.06 (mean about 1, SD about 0.40, skewness about 0.88), times the control mean.

Choices the paper does not state are options, so each can be tested (see the reproduction):
`heterogeneity` (how the shifts enter), `skew_shift` (how the experimental arm of the skewed scenario is
moved), `draw` (normal arms from their sufficient statistics or from individual values; the two are
equal in distribution), and the summaries of bias and I2 returned side by side.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from .core import MEASURES, Z95, effect_sizes, pool

SKEWED_MIXTURE = {"centers": (0.84, 1.42, 1.92), "sd": 0.24, "weights": (0.77, 0.17, 0.06)}


@dataclass(frozen=True)
class Scenario:
    """One scenario of the simulation study."""

    sd: float  # SD of both arms, in units of the control mean / 100 (10, 40 or 70)
    effect: float  # in SD units (the true SMD)
    n_exp: int
    n_contr: int
    k: int  # trials per meta-analysis
    tau: float = 0.0  # heterogeneity, in SD units
    distribution: str = "normal"  # or "skewed"
    control_mean: float = 100.0

    @property
    def true(self) -> dict:
        """The true MD, SMD and RoM (RoM on the ratio scale)."""
        md = self.effect * self.sd
        return {"MD": md, "SMD": self.effect, "RoM": 1.0 + md / self.control_mean}

    def as_dict(self) -> dict:
        return asdict(self)


def mixture_moments(centers=SKEWED_MIXTURE["centers"], sd=SKEWED_MIXTURE["sd"], weights=SKEWED_MIXTURE["weights"]):
    """Mean, SD and skewness (third standardized moment) of a mixture of normals with a common SD."""
    m = np.asarray(centers, float)
    w = np.asarray(weights, float)
    mean = float(w @ m)
    d = m - mean
    var = float(w @ (d**2 + sd**2))
    third = float(w @ (d**3 + 3 * d * sd**2))
    return mean, var**0.5, third / var**1.5


def _shifts(sc: Scenario, reps: int, rng, heterogeneity: str):
    zero = np.zeros((reps, sc.k))
    if not sc.tau:
        return zero, zero
    s = sc.tau * sc.sd
    if heterogeneity == "independent":
        return rng.normal(0, s / np.sqrt(2), (reps, sc.k)), rng.normal(0, s / np.sqrt(2), (reps, sc.k))
    if heterogeneity == "experimental_only":
        return rng.normal(0, s, (reps, sc.k)), zero
    if heterogeneity == "shared":
        u = rng.normal(0, s / np.sqrt(2), (reps, sc.k))
        return u, u
    raise ValueError(f"unknown heterogeneity model {heterogeneity!r}")


def _skewed_values(sc: Scenario, rng, shape, arm: str, skew_shift: str):
    c = np.asarray(SKEWED_MIXTURE["centers"])
    comp = rng.choice(3, size=shape, p=np.asarray(SKEWED_MIXTURE["weights"]))
    x = c[comp] + SKEWED_MIXTURE["sd"] * rng.standard_normal(shape)
    cm = sc.control_mean
    if skew_shift == "standardized":  # rescaled to mean cm and SD sd exactly
        mean, sd, _ = mixture_moments()
        x = cm + sc.sd * (x - mean) / sd
    else:
        x = cm * x
    if arm == "exp":
        if skew_shift == "multiplicative":
            x = x * sc.true["RoM"]
        else:  # additive, standardized
            x = x + sc.effect * sc.sd
    return x


def draw_trials(sc: Scenario, reps: int, seed=None, heterogeneity: str = "independent",
                skew_shift: str = "additive", draw: str = "summary", max_values: int = 4_000_000):
    """Arm means and SDs of `reps` meta-analyses of `sc.k` trials: (mean_e, sd_e, mean_c, sd_c), each (reps, k).

    `seed` feeds two independent streams, one for the heterogeneity shifts and one for the patients, so
    variants of the heterogeneity model see the same sampling noise. `draw="summary"` takes normal arms
    from their sufficient statistics (mean ~ N(mu, sd^2/n), (n - 1) s^2/sd^2 ~ chi^2(n - 1)); `draw="values"`
    draws every patient (always used for the skewed scenario).
    """
    ss_shift, ss_vals = np.random.SeedSequence(seed).spawn(2)
    rs, rv = np.random.default_rng(ss_shift), np.random.default_rng(ss_vals)
    ue, uc = _shifts(sc, reps, rs, heterogeneity)
    mu_c = sc.control_mean
    mu_e = mu_c + sc.effect * sc.sd
    if sc.distribution == "normal" and draw == "summary":
        me = mu_e + sc.sd / np.sqrt(sc.n_exp) * rv.standard_normal((reps, sc.k))
        se = sc.sd * np.sqrt(rv.chisquare(sc.n_exp - 1, (reps, sc.k)) / (sc.n_exp - 1))
        mc = mu_c + sc.sd / np.sqrt(sc.n_contr) * rv.standard_normal((reps, sc.k))
        sd_c = sc.sd * np.sqrt(rv.chisquare(sc.n_contr - 1, (reps, sc.k)) / (sc.n_contr - 1))
        return me + ue, se, mc + uc, sd_c
    if sc.distribution not in ("normal", "skewed"):
        raise ValueError(f"unknown distribution {sc.distribution!r}")
    out = [np.empty((reps, sc.k)) for _ in range(4)]
    step = max(1, max_values // (sc.k * max(sc.n_exp, sc.n_contr)))
    for a in range(0, reps, step):
        b = min(reps, a + step)
        for j, (arm, n, mu) in enumerate((("exp", sc.n_exp, mu_e), ("contr", sc.n_contr, mu_c))):
            shape = (b - a, sc.k, n)
            if sc.distribution == "normal":
                x = mu + sc.sd * rv.standard_normal(shape)
            else:
                x = _skewed_values(sc, rv, shape, arm, skew_shift)
            out[2 * j][a:b] = x.mean(-1)
            out[2 * j + 1][a:b] = x.std(-1, ddof=1)
    me, se, mc, sd_c = out
    return me + ue, se, mc + uc, sd_c


def summarize(sc: Scenario, me, se, mc, sd_c, z: float = Z95, sd_pool_literal: bool = False,
              negative: str = "drop_trial", measures=MEASURES, small_sample_correction: bool = True) -> dict:
    """Performance of each measure over the replicates (rows) of simulated trial summaries.

    Per measure (all percentages):
      bias       100 x (mean pooled estimate - true)/true, on the reporting scale (RoM back-transformed);
                 the paper's definition, as its tables print it
      coverage   share of 95% CIs that contain the true value
      power      share of 95% CIs that exclude 0 (MD, SMD) or 1 (RoM)
      i2         100 x (1 - 1/mean(Q/(k - 1))): I2 of the average Q/(k - 1) over the replicates
      *_se       Monte Carlo standard errors of one run
    and, to test the paper's unstated definitions: i2_mean (mean of each replicate's I2), i2_median,
    q_df (mean Q/(k - 1)); for RoM, bias_ln (on ln RoM) and bias_rm1 (as a share of RoM - 1).
    `negative`: a RoM study with a non-positive mean is left out of its meta-analysis ("drop_trial"),
    or the whole replicate is left out ("drop_replicate").
    """
    reps = me.shape[0]
    out = {}
    for m in measures:
        y, v = effect_sizes(me, se, sc.n_exp, mc, sd_c, sc.n_contr, m, sd_pool_literal=sd_pool_literal,
                            small_sample_correction=small_sample_correction)
        dropped = int((~np.isfinite(y)).sum())
        keep = np.ones(reps, bool)
        if m == "RoM" and negative == "drop_replicate":
            keep = np.isfinite(y).all(-1)
            y, v = y[keep], v[keep]
        r = pool(y, v, z=z)
        true = sc.true[m]
        t = np.log(true) if m == "RoM" else true
        est = r["estimate"]
        lo, hi = r["ci_low"], r["ci_high"]
        rep = np.exp(est) if m == "RoM" else est
        n = len(est)
        qdf = r["q"] / r["df"]
        h = float(qdf.mean())
        cov = float(((lo <= t) & (t <= hi)).mean())
        pw = float(((lo > 0) | (hi < 0)).mean())
        d = {
            "bias": 100 * (float(rep.mean()) - true) / true,
            "bias_se": 100 * float(rep.std(ddof=1)) / np.sqrt(n) / abs(true),
            "coverage": 100 * cov, "coverage_se": 100 * np.sqrt(cov * (1 - cov) / n),
            "power": 100 * pw, "power_se": 100 * np.sqrt(pw * (1 - pw) / n),
            "i2": 100 * (1 - 1 / h), "i2_se": 100 * float(qdf.std(ddof=1)) / np.sqrt(n) / h**2,
            "i2_mean": 100 * float(r["i2"].mean()), "i2_median": 100 * float(np.median(r["i2"])),
            "q_df": h, "replicates": int(n), "studies_left_out": dropped, "replicates_left_out": int(reps - keep.sum()),
        }
        if m == "RoM":
            d["bias_ln"] = 100 * (float(est.mean()) - t) / t
            d["bias_rm1"] = 100 * (float(rep.mean()) - true) / (true - 1)
        out[m] = d
    return out


def run_scenario(sc: Scenario, reps: int = 10_000, seed=None, *, heterogeneity: str = "independent",
                 skew_shift: str = "additive", draw: str = "summary", z: float = Z95,
                 sd_pool_literal: bool = False, negative: str = "drop_trial",
                 small_sample_correction: bool = True) -> dict:
    """Simulate one scenario and return `summarize`'s performance measures for MD, SMD and RoM."""
    arms = draw_trials(sc, reps, seed, heterogeneity=heterogeneity, skew_shift=skew_shift, draw=draw)
    return summarize(sc, *arms, z=z, sd_pool_literal=sd_pool_literal, negative=negative,
                     small_sample_correction=small_sample_correction)

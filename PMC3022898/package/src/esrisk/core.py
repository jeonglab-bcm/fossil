"""Exposure-specific risk (ESR) from two independent samples (Reichmann et al. 2011).

Sample 1 gives the overall risk of disease P1(D) from n1 people. Sample 2 gives the relative risk
RR2 = P2(D|E) / P2(D|not E) and the exposure probability P2(E) from n2 people, n2E of them exposed.

Estimators (equation numbers of the paper):

* simple product-based, eq. 2:   ESR_S = P1(D) * RR2
* revised product-based, eq. 9:  ESR_R = P1(D) / ((RR2 - 1) * P2(E) + 1) * RR2

Interval estimators:

* log-based CI of ESR_S, eqs 5-6: exp(ln ESR_S +/- z sqrt(V)),
  V = (1 - P1(D)) / (n1 P1(D)) + (1 - P2(D|E)) / (P2(D|E) n2E) + (1 - P2(D|~E)) / (P2(D|~E) n2~E)
* log-based CI of ESR_R, eq. 10: the same with P1(D|~E) = P1(D) / ((RR2 - 1) P2(E) + 1) (eq. 8)
  in place of P1(D)
* binomial CI of ESR_R, eqs 11-12: ESR_R +/- z sqrt(ESR_R (1 - ESR_R) / (n1 P2(E)))

Everything is vectorised over NumPy arrays, so one call evaluates a whole simulation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

Z95 = 1.959963984540054  # the paper prints 1.96; the two give the same intervals to 1e-5 relative

#: How a sample with no cases among the exposed (or among the unexposed) of sample 2 is handled
#: in the log-based intervals, which are undefined there (ln 0, or a division by zero). The paper
#: does not say. The point estimates are kept in every rule except "half".
#:   "unbounded" (default): the log interval is (0, infinity): with no cases in a group, the data
#:              bound the risk ratio on one side only. It covers every ESR and has no finite length.
#:              This rule fits the paper's Tables S5 and S6 best (see the reproduction's README).
#:   "missing": the log intervals are missing, and left out of coverage and length.
#:   "not_covered": the log intervals count as not covering.
#:   "half": 0.5 is added to every cell of sample 2 when one is zero (point estimates too).
ZERO_CELL_RULES = ("unbounded", "missing", "not_covered", "half")


def esr_simple(p1_d, rr2):
    """Simple product-based ESR (eq. 2): P1(D) x RR2."""
    return np.asarray(p1_d, dtype=float) * np.asarray(rr2, dtype=float)


def p_unexposed(p1_d, rr2, p2_e):
    """Risk of disease in the unexposed by the law of total probability (eq. 8)."""
    p1_d, rr2, p2_e = (np.asarray(x, dtype=float) for x in (p1_d, rr2, p2_e))
    return p1_d / ((rr2 - 1.0) * p2_e + 1.0)


def esr_revised(p1_d, rr2, p2_e):
    """Revised product-based ESR (eq. 9): P1(D) / ((RR2 - 1) P2(E) + 1) x RR2."""
    return p_unexposed(p1_d, rr2, p2_e) * np.asarray(rr2, dtype=float)


def var_ln_proportion(p, n):
    """Delta-method variance of ln(p) for a binomial proportion p from n trials (eq. 4)."""
    p, n = np.asarray(p, dtype=float), np.asarray(n, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return (1.0 - p) / (n * p)


def var_ln_rr(p_exposed, n_exposed, p_unexposed_, n_unexposed):
    """Variance of ln(RR) for a risk ratio of two independent proportions (eq. 3)."""
    return var_ln_proportion(p_exposed, n_exposed) + var_ln_proportion(p_unexposed_, n_unexposed)


def log_ci(est, var_ln, z=Z95):
    """exp(ln est +/- z sqrt(var_ln)) (eq. 6). NaN where the estimate or variance is undefined."""
    est, var_ln = np.asarray(est, dtype=float), np.asarray(var_ln, dtype=float)
    ok = (est > 0) & np.isfinite(var_ln) & (var_ln >= 0)
    with np.errstate(divide="ignore", invalid="ignore"):
        half = z * np.sqrt(np.where(ok, var_ln, np.nan))
        lo = np.where(ok, np.exp(np.log(np.where(ok, est, 1.0)) - half), np.nan)
        hi = np.where(ok, np.exp(np.log(np.where(ok, est, 1.0)) + half), np.nan)
    return lo, hi


def binomial_ci(esr, n1, p2_e, z=Z95):
    """ESR_R +/- z sqrt(ESR_R (1 - ESR_R) / (n1 P2(E))) (eqs 11-12)."""
    esr, n1, p2_e = (np.asarray(x, dtype=float) for x in (esr, n1, p2_e))
    with np.errstate(divide="ignore", invalid="ignore"):
        half = z * np.sqrt(esr * (1.0 - esr) / (n1 * p2_e))
    return esr - half, esr + half


@dataclass
class Estimates:
    """Point and interval estimates for one or many pairs of samples (arrays of equal shape)."""

    p1_d: np.ndarray
    rr2: np.ndarray
    p2_e: np.ndarray
    esr_s: np.ndarray
    esr_r: np.ndarray
    ci_s_log: tuple
    ci_r_log: tuple
    ci_r_binomial: tuple

    def as_dict(self):
        out = {"p1_d": self.p1_d, "rr2": self.rr2, "p2_e": self.p2_e, "esr_s": self.esr_s, "esr_r": self.esr_r}
        for name in ("ci_s_log", "ci_r_log", "ci_r_binomial"):
            lo, hi = getattr(self, name)
            out[name + "_lower"], out[name + "_upper"] = lo, hi
        return out


def estimate(d1, n1, d2e, n2e, d2u, n2u, zero_cells="unbounded", z=Z95):
    """Both ESRs and their three 95% CIs from case counts.

    d1 cases among the n1 people of sample 1; d2e cases among the n2e exposed and d2u among the n2u
    unexposed of sample 2. Scalars or arrays.
    """
    if zero_cells not in ZERO_CELL_RULES:
        raise ValueError(f"zero_cells must be one of {ZERO_CELL_RULES}")
    d1, n1, d2e, n2e, d2u, n2u = np.broadcast_arrays(*(np.asarray(x, dtype=float) for x in (d1, n1, d2e, n2e, d2u, n2u)))
    if np.any(n1 <= 0) or np.any(n2e <= 0) or np.any(n2u <= 0):
        raise ValueError("sample 1 and both exposure groups of sample 2 need at least one person")
    if np.any((d1 < 0) | (d1 > n1) | (d2e < 0) | (d2e > n2e) | (d2u < 0) | (d2u > n2u)):
        raise ValueError("case counts must lie between 0 and the group size")
    if zero_cells == "half":
        zero = (d2e == 0) | (d2u == 0) | (d2e == n2e) | (d2u == n2u)
        d2e, d2u = np.where(zero, d2e + 0.5, d2e), np.where(zero, d2u + 0.5, d2u)
        n2e, n2u = np.where(zero, n2e + 1.0, n2e), np.where(zero, n2u + 1.0, n2u)
    p1_d = d1 / n1
    p2_de, p2_du = d2e / n2e, d2u / n2u
    p2_e = n2e / (n2e + n2u)
    with np.errstate(divide="ignore", invalid="ignore"):
        rr2 = p2_de / p2_du
    s = esr_simple(p1_d, rr2)
    r = esr_revised(p1_d, rr2, p2_e)
    v_rr = var_ln_rr(p2_de, n2e, p2_du, n2u)
    v_s = var_ln_proportion(p1_d, n1) + v_rr
    v_r = var_ln_proportion(p_unexposed(p1_d, rr2, p2_e), n1) + v_rr
    ci_s, ci_r = log_ci(s, v_s, z), log_ci(r, v_r, z)
    if zero_cells == "unbounded":
        ci_s = (np.where(np.isnan(ci_s[0]), 0.0, ci_s[0]), np.where(np.isnan(ci_s[1]), np.inf, ci_s[1]))
        ci_r = (np.where(np.isnan(ci_r[0]), 0.0, ci_r[0]), np.where(np.isnan(ci_r[1]), np.inf, ci_r[1]))
    if zero_cells == "not_covered":
        # An undefined interval is kept as an empty one at -1, which covers nothing.
        ci_s = tuple(np.where(np.isnan(x), -1.0, x) for x in ci_s)
        ci_r = tuple(np.where(np.isnan(x), -1.0, x) for x in ci_r)
    return Estimates(p1_d, rr2, p2_e, s, r, ci_s, ci_r, binomial_ci(r, n1, p2_e, z))


def esr_from_summaries(p1_d, n1, rr2, rr2_ci, p2_e, z=Z95):
    """Both ESRs and their CIs from published summaries, without the counts of sample 2.

    p1_d: overall risk from sample 1 of size n1; rr2 and rr2_ci = (lower, upper): a relative risk and
    its 95% CI from sample 2; p2_e: the exposure probability in sample 2. The variance of ln(RR2) is
    taken from the CI as ((ln upper - ln lower) / (2 z))^2, which equals eq. 3 when the CI was computed
    the usual way. Returns a dict of plain floats.
    """
    if not (0 < p1_d < 1 and 0 < p2_e < 1 and rr2 > 0 and n1 > 0):
        raise ValueError("need 0 < p1_d < 1, 0 < p2_e < 1, rr2 > 0 and n1 > 0")
    lo, hi = rr2_ci
    if not (0 < lo <= rr2 <= hi):
        raise ValueError("rr2_ci must be (lower, upper) around rr2")
    v_rr = ((math.log(hi) - math.log(lo)) / (2 * z)) ** 2
    s = float(esr_simple(p1_d, rr2))
    r = float(esr_revised(p1_d, rr2, p2_e))
    v_s = float(var_ln_proportion(p1_d, n1)) + v_rr
    v_r = float(var_ln_proportion(p_unexposed(p1_d, rr2, p2_e), n1)) + v_rr
    (sl, sh), (rl, rh) = log_ci(s, v_s, z), log_ci(r, v_r, z)
    bl, bh = binomial_ci(r, n1, p2_e, z)
    return {
        "esr_s": s, "esr_s_log_lower": float(sl), "esr_s_log_upper": float(sh),
        "esr_r": r, "esr_r_log_lower": float(rl), "esr_r_log_upper": float(rh),
        "esr_r_binomial_lower": float(bl), "esr_r_binomial_upper": float(bh),
        "p_unexposed": float(p_unexposed(p1_d, rr2, p2_e)), "var_ln_rr2": v_rr,
    }


# ---------------------------------------------------------------------------------------------
# Simulation (Methods, "Simulation study details")
# ---------------------------------------------------------------------------------------------

def make_population(p_exposed, p_disease_unexposed, rr, size=10_000_000, rng=None, exact=False):
    """Cell counts of a population: (exposed cases, exposed non-cases, unexposed cases, unexposed non-cases).

    exact=False draws exposure and disease for each person (Bernoulli); exact=True gives each cell
    its expected count, rounded.
    """
    p1 = rr * p_disease_unexposed
    if not (0 < p_exposed < 1 and 0 < p_disease_unexposed < 1 and 0 < p1 <= 1):
        raise ValueError("probabilities out of range")
    if exact:
        n_e = round(size * p_exposed)
        n_u = size - n_e
        de, du = round(n_e * p1), round(n_u * p_disease_unexposed)
    else:
        rng = np.random.default_rng(rng)
        n_e = int(rng.binomial(size, p_exposed))
        n_u = size - n_e
        de, du = int(rng.binomial(n_e, p1)), int(rng.binomial(n_u, p_disease_unexposed))
    return np.array([de, n_e - de, du, n_u - du], dtype=np.int64)


def draw_samples(population, n, reps, rng=None):
    """reps samples of n people without replacement: an array (reps, 4) of cell counts."""
    rng = np.random.default_rng(rng)
    return rng.multivariate_hypergeometric(np.asarray(population, dtype=np.int64), n, size=reps)


def simulate(p_exposed, p_disease_unexposed, rr, n1, n2, reps=1000, size=10_000_000, rng=None,
             exact_population=False, zero_cells="unbounded", z=Z95):
    """One setting of the simulation study: a population, then reps pairs of independent samples.

    Returns (estimates, population, sample1, sample2) with one row per pair of samples.
    """
    rng = np.random.default_rng(rng)
    pop = make_population(p_exposed, p_disease_unexposed, rr, size, rng, exact=exact_population)
    s1 = draw_samples(pop, n1, reps, rng)
    s2 = draw_samples(pop, n2, reps, rng)
    d1 = s1[:, 0] + s1[:, 2]
    est = estimate(d1, n1, s2[:, 0], s2[:, 0] + s2[:, 1], s2[:, 2], s2[:, 2] + s2[:, 3], zero_cells=zero_cells, z=z)
    return est, pop, s1, s2


def evaluate(estimates, true_esr):
    """The paper's measures for one setting (Methods, "Evaluation of ESR Estimators" and "... CIs").

    relative bias = (mean estimate - true) / true; absolute bias = mean estimate - true;
    coverage = share of intervals that contain the true ESR (missing intervals left out);
    expected length given coverage = mean upper - lower over the intervals that cover and are finite;
    empirical CI = 2.5th and 97.5th percentiles of the point estimates.
    """
    out = {}
    for name, est in (("esr_s", estimates.esr_s), ("esr_r", estimates.esr_r)):
        est = est[np.isfinite(est)]
        m = float(np.mean(est))
        out[name] = {
            "mean": m, "sd": float(np.std(est, ddof=1)), "n": int(est.size),
            "relative_bias": (m - true_esr) / true_esr, "absolute_bias": m - true_esr,
            "empirical_lower": float(np.percentile(est, 2.5)), "empirical_upper": float(np.percentile(est, 97.5)),
        }
        out[name]["empirical_length"] = out[name]["empirical_upper"] - out[name]["empirical_lower"]
    for name in ("ci_s_log", "ci_r_log", "ci_r_binomial"):
        lo, hi = getattr(estimates, name)
        ok = ~np.isnan(lo) & ~np.isnan(hi)
        cover = ok & (lo <= true_esr) & (true_esr <= hi)
        finite = cover & np.isfinite(hi - lo)
        n_ok = int(ok.sum())
        out[name] = {
            "coverage": float(cover.sum() / n_ok) if n_ok else float("nan"),
            "n_defined": n_ok,
            "n_covering": int(cover.sum()),
            "n_unbounded": int((ok & ~np.isfinite(hi - lo)).sum()),
            "expected_length_given_coverage": float(np.mean((hi - lo)[finite])) if finite.any() else float("nan"),
        }
    return out

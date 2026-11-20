"""Risk-stratified vs conventional subgroup analysis of a clinical trial (Hayward et al. 2006).

The model of the paper:

* Each person carries independent binary risk factors (RFs). Their 5-year risk without treatment (the
  control event rate, CER) is a baseline risk times the effect of each RF present, on the risk scale
  (relative risks) or on the odds scale (odds ratios).
* The treatment removes half of that risk but adds a uniform harm: 3 serious complications per 1,000
  treated per year, over 5 years. Fig. 1A prints the formula: EER = CER x .5 + .003 x 5.
* A subgroup analysis tests treatment-effect heterogeneity with a logistic regression of the outcome on
  the subgroup variable, the arm and their interaction (Brookes et al.); its power is the share of
  simulated trials (N = 8,800, 4,400 per arm) whose interaction p-value is below .05.

Everything here works on the population's RF patterns (2^K of them), so a whole trial is a table of
counts and events per pattern and arm. That makes thousands of trials per second possible, and gives
the same likelihood as a regression on the 8,800 individual rows.
"""

from __future__ import annotations

import csv
import itertools
import math
from dataclasses import dataclass, field
from typing import Iterable, Sequence

import numpy as np

RRR = 0.5  # the treatment's relative reduction of the pre-treatment risk
HARM_PER_YEAR = 0.003  # serious treatment complications per treated person-year (base case)
YEARS = 5
N_PER_ARM = 4400
ALPHA = 0.05


# --------------------------------------------------------------------------------------------------
# The population
# --------------------------------------------------------------------------------------------------


@dataclass
class Population:
    """Every pattern of K independent binary risk factors, with its share and its 5-year CER."""

    prevalence: np.ndarray  # (K,)
    effect: np.ndarray  # (K,) relative risk or odds ratio of each RF
    cer0: float  # 5-year CER with no risk factor
    scale: str  # "rr" or "or"
    patterns: np.ndarray = field(init=False)  # (P, K) 0/1
    share: np.ndarray = field(init=False)  # (P,)
    cer: np.ndarray = field(init=False)  # (P,)

    def __post_init__(self):
        self.prevalence = np.asarray(self.prevalence, float)
        self.effect = np.asarray(self.effect, float)
        if self.prevalence.shape != self.effect.shape or self.prevalence.ndim != 1:
            raise ValueError("prevalence and effect must be sequences of the same length")
        if np.any((self.prevalence < 0) | (self.prevalence > 1)):
            raise ValueError("prevalences must lie in [0, 1]")
        if self.scale not in ("rr", "or"):
            raise ValueError("scale must be 'rr' (relative risks) or 'or' (odds ratios)")
        if not 0 < self.cer0 < 1:
            raise ValueError("cer0 must lie in (0, 1)")
        k = len(self.prevalence)
        self.patterns = np.array(list(itertools.product([0, 1], repeat=k)), dtype=int).reshape(-1, k)
        self.share = np.prod(np.where(self.patterns == 1, self.prevalence, 1 - self.prevalence), axis=1)
        mult = np.prod(np.where(self.patterns == 1, self.effect, 1.0), axis=1)
        if self.scale == "rr":
            cer = self.cer0 * mult
            if np.any(cer > 1):
                raise ValueError("a pattern's risk exceeds 1 on the relative-risk scale")
        else:
            odds = self.cer0 / (1 - self.cer0) * mult
            cer = odds / (1 + odds)
        self.cer = cer

    @property
    def mean_cer(self) -> float:
        return float(self.share @ self.cer)

    def count(self, columns: Sequence[int] | None = None) -> np.ndarray:
        """Number of RFs present in each pattern (of the given columns; default all)."""
        cols = range(self.patterns.shape[1]) if columns is None else columns
        return self.patterns[:, list(cols)].sum(axis=1)

    def score(self, weights: Sequence[float]) -> np.ndarray:
        """A weighted risk index: the sum of the weights of the RFs present."""
        w = np.asarray(weights, float)
        if w.shape != (self.patterns.shape[1],):
            raise ValueError(f"need {self.patterns.shape[1]} weights")
        return self.patterns @ w


def population(n_rf: int = 6, prevalence=0.25, effect=2.0, cer0: float = 0.0075, scale: str = "rr") -> Population:
    """A population of n_rf independent RFs; prevalence and effect may be scalars or sequences."""
    prev = np.broadcast_to(np.asarray(prevalence, float), (n_rf,)).copy()
    eff = np.broadcast_to(np.asarray(effect, float), (n_rf,)).copy()
    return Population(prev, eff, float(cer0), scale)


def cer0_for_mean(mean_cer: float, prevalence, effect, scale: str = "rr", n_rf: int | None = None) -> float:
    """The baseline (no-RF) CER that gives the population the stated average CER (bisection)."""
    prev = np.atleast_1d(np.asarray(prevalence, float))
    eff = np.atleast_1d(np.asarray(effect, float))
    k = n_rf or max(len(prev), len(eff))
    lo, hi = 1e-9, mean_cer
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        m = population(k, prev if len(prev) > 1 else prev[0], eff if len(eff) > 1 else eff[0], mid, scale).mean_cer
        lo, hi = (mid, hi) if m < mean_cer else (lo, mid)
    return 0.5 * (lo + hi)


# --------------------------------------------------------------------------------------------------
# Treatment effect
# --------------------------------------------------------------------------------------------------


def treated_risk(cer, rrr: float = RRR, harm_per_year: float = HARM_PER_YEAR, years: float = YEARS,
                 harm_model: str = "additive"):
    """5-year event rate on treatment (EER).

    additive (the paper's Fig. 1A): EER = CER x (1 - RRR) + harm per year x years.
    independent: the outcome and a treatment complication as independent events,
    EER = 1 - (1 - CER x (1 - RRR)) x (1 - harm per year)^years.
    """
    cer = np.asarray(cer, float)
    if harm_model == "additive":
        eer = cer * (1 - rrr) + harm_per_year * years
    elif harm_model == "independent":
        eer = 1 - (1 - cer * (1 - rrr)) * (1 - harm_per_year) ** years
    else:
        raise ValueError("harm_model must be 'additive' or 'independent'")
    return np.clip(eer, 0.0, 1.0)


def net_rrr(cer, rrr: float = RRR, harm_per_year: float = HARM_PER_YEAR, years: float = YEARS,
            harm_model: str = "additive"):
    """Net relative risk reduction (CER - EER) / CER; negative values are net harm."""
    cer = np.asarray(cer, float)
    return (cer - treated_risk(cer, rrr, harm_per_year, years, harm_model)) / cer


def subgroup_table(pop: Population, groups: dict[str, np.ndarray], **treat) -> list[dict]:
    """Share, CER, net RRR and NNT of subgroups of the population (masks over its patterns).

    These are the 'true' values of Table 1: they follow from the model with no simulation.
    """
    eer = treated_risk(pop.cer, **treat)
    rows = []
    for name, mask in groups.items():
        mask = np.asarray(mask, bool)
        s = pop.share[mask].sum()
        c = float(pop.share[mask] @ pop.cer[mask] / s)
        e = float(pop.share[mask] @ eer[mask] / s)
        arr = c - e
        rows.append({"group": name, "share": float(s), "cer": c, "eer": e, "rrr": arr / c,
                     "nnt": (1 / arr) if arr != 0 else math.inf})
    return rows


# --------------------------------------------------------------------------------------------------
# AUROC of a risk index
# --------------------------------------------------------------------------------------------------


def auroc_weighted(score, w_event, w_none) -> float:
    """AUROC of a score from weighted events and non-events (ties count one half)."""
    score = np.asarray(score, float)
    w_event = np.asarray(w_event, float)
    w_none = np.asarray(w_none, float)
    vals, inv = np.unique(score, return_inverse=True)
    ev = np.bincount(inv, weights=w_event, minlength=len(vals))
    no = np.bincount(inv, weights=w_none, minlength=len(vals))
    below = np.concatenate([[0.0], np.cumsum(no)[:-1]])
    return float((ev * (below + 0.5 * no)).sum() / (ev.sum() * no.sum()))


def population_auroc(pop: Population, score, arms: str = "both", **treat) -> float:
    """AUROC of a risk index for the 5-year outcome in the population.

    arms: 'control' (pre-treatment risk only), 'treated', or 'both' (a 1:1 trial, the default).
    """
    score = np.asarray(score, float)
    eer = treated_risk(pop.cer, **treat)
    if arms == "control":
        p_ev, p_no = pop.share * pop.cer, pop.share * (1 - pop.cer)
    elif arms == "treated":
        p_ev, p_no = pop.share * eer, pop.share * (1 - eer)
    elif arms == "both":
        p_ev, p_no = pop.share * (pop.cer + eer), pop.share * (2 - pop.cer - eer)
    else:
        raise ValueError("arms must be 'control', 'treated' or 'both'")
    return auroc_weighted(score, p_ev, p_no)


# --------------------------------------------------------------------------------------------------
# Logistic regression on grouped data
# --------------------------------------------------------------------------------------------------


def _norm_sf2(z):
    """Two-sided normal p-value of |z|."""
    z = np.abs(np.asarray(z, float))
    return np.vectorize(math.erfc)(z / math.sqrt(2.0))


def fit_logit_grouped(X: np.ndarray, n: np.ndarray, y: np.ndarray, max_iter: int = 50, tol: float = 1e-10):
    """Maximum-likelihood logistic regression for many data sets at once.

    X: (R, p) design of the R covariate patterns; n, y: (B, R) trials and events per pattern for B data
    sets. Returns beta (B, p), se (B, p) and a mask of the fits that converged to finite estimates
    (a fit with an empty event cell, for example, diverges and is marked False).
    """
    X = np.asarray(X, float)
    n = np.atleast_2d(np.asarray(n, float))
    y = np.atleast_2d(np.asarray(y, float))
    B, p = n.shape[0], X.shape[1]
    rate = np.clip(y.sum(1) / np.maximum(n.sum(1), 1), 1e-6, 1 - 1e-6)
    beta = np.zeros((B, p))
    beta[:, 0] = np.log(rate / (1 - rate))
    ok = np.ones(B, bool)
    eye = np.eye(p) * 1e-12
    for _ in range(max_iter):
        eta = beta @ X.T
        mu = 1 / (1 + np.exp(-eta))
        w = n * mu * (1 - mu)
        grad = (y - n * mu) @ X
        H = np.einsum("br,ri,rj->bij", w, X, X) + eye
        step = np.linalg.solve(H, grad[..., None])[..., 0]
        beta = beta + step
        if np.all(np.abs(step) < tol):
            break
    eta = beta @ X.T
    mu = 1 / (1 + np.exp(-eta))
    w = n * mu * (1 - mu)
    H = np.einsum("br,ri,rj->bij", w, X, X) + eye
    cov = np.linalg.inv(H)
    se = np.sqrt(np.clip(np.diagonal(cov, axis1=1, axis2=2), 0, None))
    ok &= np.all(np.isfinite(beta), 1) & np.all(np.isfinite(se), 1) & np.all(np.abs(beta) < 15, 1)
    ok &= np.all(np.abs(step) < 1e-6, 1)
    return beta, se, ok


def loglik_grouped(X, beta, n, y):
    """Binomial log-likelihood (without the constant) of grouped data for each data set."""
    eta = np.asarray(beta) @ np.asarray(X, float).T
    log_mu = -np.logaddexp(0, -eta)
    log_1mu = -np.logaddexp(0, eta)
    return np.sum(y * log_mu + (n - y) * log_1mu, axis=1)


def _chi2_1_sf(x):
    """Upper tail of a chi-squared variable with 1 degree of freedom."""
    x = np.clip(np.asarray(x, float), 0, None)
    return np.vectorize(math.erfc)(np.sqrt(x / 2.0))


def interaction_design(z_values: np.ndarray) -> np.ndarray:
    """Rows (z, arm) for arm 0 then arm 1, columns intercept, z, arm, z x arm."""
    z = np.asarray(z_values, float)
    rows = [[1.0, v, a, v * a] for a in (0.0, 1.0) for v in z]
    return np.array(rows)


def interaction_test(z, arm, outcome) -> dict:
    """Test of a subgroup-by-treatment interaction on individual data (Brookes et al.).

    Logistic regression of outcome (0/1) on z, arm (0/1) and z x arm. Returns the coefficients, their
    standard errors and the Wald p-value of the interaction. z may be a binary subgroup or a risk score.
    """
    z = np.asarray(z, float)
    arm = np.asarray(arm, float)
    y = np.asarray(outcome, float)
    if not (len(z) == len(arm) == len(y)):
        raise ValueError("z, arm and outcome must have the same length")
    if not set(np.unique(arm)) <= {0.0, 1.0} or not set(np.unique(y)) <= {0.0, 1.0}:
        raise ValueError("arm and outcome must be coded 0/1")
    if len(np.unique(arm)) < 2 or len(np.unique(z)) < 2:
        raise ValueError("need both arms and at least two values of z")
    keys, inv = np.unique(np.column_stack([z, arm]), axis=0, return_inverse=True)
    inv = inv.ravel()
    n = np.bincount(inv).astype(float)
    ev = np.bincount(inv, weights=y)
    X = np.column_stack([np.ones(len(keys)), keys[:, 0], keys[:, 1], keys[:, 0] * keys[:, 1]])
    beta, se, ok = fit_logit_grouped(X, n[None], ev[None])
    if not ok[0]:
        raise ValueError("the logistic regression did not converge (an empty cell?)")
    b, s = beta[0], se[0]
    names = ["intercept", "z", "arm", "z_x_arm"]
    return {
        "coef": dict(zip(names, map(float, b))),
        "se": dict(zip(names, map(float, s))),
        "z_interaction": float(b[3] / s[3]),
        "p_interaction": float(_norm_sf2(b[3] / s[3])),
        "n": int(len(y)),
    }


# --------------------------------------------------------------------------------------------------
# Power by simulation
# --------------------------------------------------------------------------------------------------


def _finite_population(pop: Population, eer: np.ndarray, size: int, rng: np.random.Generator):
    """A finite population as a pseudo-population of (pattern, control outcome, treated outcome) cells.

    Returns a Population-like object whose 'patterns' are the cells, and the treated risk of each cell
    (0 or 1): a trial then samples people with replacement from these cells.
    """
    m = rng.multinomial(size, pop.share)
    a = rng.binomial(m, pop.cer)  # events without treatment
    b = rng.binomial(m, eer)  # events with treatment (drawn independently of a)
    # four cells per pattern: (y0, y1) in {0,1}^2, with b split independently of a
    p11 = np.where(m > 0, a * b / np.maximum(m, 1) ** 2, 0)
    p10 = np.where(m > 0, a * (m - b) / np.maximum(m, 1) ** 2, 0)
    p01 = np.where(m > 0, (m - a) * b / np.maximum(m, 1) ** 2, 0)
    p00 = np.where(m > 0, (m - a) * (m - b) / np.maximum(m, 1) ** 2, 0)
    w = m / size
    share = np.concatenate([w * p00, w * p01, w * p10, w * p11])
    y0 = np.concatenate([np.zeros_like(p00), np.zeros_like(p01), np.ones_like(p10), np.ones_like(p11)])
    y1 = np.concatenate([np.zeros_like(p00), np.ones_like(p01), np.zeros_like(p10), np.ones_like(p11)])
    fp = _CellPopulation(np.vstack([pop.patterns] * 4), share / share.sum(), y0)
    return fp, y1


@dataclass
class _CellPopulation:
    patterns: np.ndarray
    share: np.ndarray
    cer: np.ndarray


def _draw_trials(pop: Population, rng: np.random.Generator, iterations: int, n_per_arm: int, eer: np.ndarray):
    """Counts and events per pattern and arm for `iterations` trials drawn with replacement."""
    nc = rng.multinomial(n_per_arm, pop.share, size=iterations)
    nt = rng.multinomial(n_per_arm, pop.share, size=iterations)
    yc = rng.binomial(nc, pop.cer)
    yt = rng.binomial(nt, eer)
    return nc, yc, nt, yt


def simulate_power(
    pop: Population,
    subgroups: dict[str, np.ndarray],
    iterations: int = 2000,
    n_per_arm: int = N_PER_ARM,
    seed: int = 0,
    alpha: float = ALPHA,
    chunk: int = 500,
    rrr: float = RRR,
    harm_per_year: float = HARM_PER_YEAR,
    years: float = YEARS,
    harm_model: str = "additive",
    test: str = "wald",
    population_size: int | None = None,
    auroc_of: Iterable[str] = (),
) -> dict:
    """Power of each subgroup analysis over simulated trials.

    subgroups maps a name to the subgroup variable of each pattern: a 0/1 subgroup (conventional
    analysis, or a dichotomized index) or a score (continuous risk index). Each trial draws n_per_arm
    people per arm with replacement from the population, then events with the pattern's CER (control)
    or EER (treated). The same trials are used for every subgroup variable. The main effect (arm only)
    is tested too, as 'main_effect'.

    test: 'wald' (the z test of the interaction coefficient) or 'lr' (likelihood ratio against the
    model without the interaction).

    population_size: None draws every trial from the infinite population. An integer M first draws one
    finite population of M people, each with an outcome without and with treatment, and then samples
    every trial with replacement from it (one reading of the paper's "randomly drawing observations,
    with replacement, from a population").

    Returns {name: {"power", "se", "failed", "iterations"}} and, for the names in auroc_of, the mean
    AUROC of the variable over the simulated trials (both arms).
    """
    if test not in ("wald", "lr"):
        raise ValueError("test must be 'wald' or 'lr'")
    rng = np.random.default_rng(seed)
    eer = treated_risk(pop.cer, rrr, harm_per_year, years, harm_model)
    if population_size is not None:
        pop, eer = _finite_population(pop, eer, int(population_size), rng)
    specs = {}
    for name, z in subgroups.items():
        z = np.asarray(z, float)
        if len(z) != len(pop.share):  # a finite population repeats each pattern in four cells
            z = np.tile(z, len(pop.share) // len(z))
        vals, inv = np.unique(z, return_inverse=True)
        M = np.zeros((len(z), len(vals)))
        M[np.arange(len(z)), inv] = 1
        specs[name] = (vals, M, interaction_design(vals))
    hits = {k: 0 for k in specs}
    fails = {k: 0 for k in specs}
    auc_sum = {k: 0.0 for k in auroc_of}
    main_hits = 0
    done = 0
    while done < iterations:
        b = min(chunk, iterations - done)
        nc, yc, nt, yt = _draw_trials(pop, rng, b, n_per_arm, eer)
        # main effect: two proportions, logistic regression on arm alone (closed form)
        ec, et = yc.sum(1), yt.sum(1)
        with np.errstate(divide="ignore", invalid="ignore"):
            lor = np.log(et / (n_per_arm - et)) - np.log(ec / (n_per_arm - ec))
            se = np.sqrt(1 / et + 1 / (n_per_arm - et) + 1 / ec + 1 / (n_per_arm - ec))
            pm = _norm_sf2(lor / se)
        main_hits += int(np.sum(np.nan_to_num(pm, nan=1.0) < alpha))
        for name, (vals, M, X) in specs.items():
            n = np.hstack([nc @ M, nt @ M])
            y = np.hstack([yc @ M, yt @ M])
            beta, se, ok = fit_logit_grouped(X, n, y)
            if test == "wald":
                pval = np.where(ok, _norm_sf2(beta[:, 3] / np.where(ok, se[:, 3], 1.0)), 1.0)
            else:
                b0, _, ok0 = fit_logit_grouped(X[:, :3], n, y)
                lr = 2 * (loglik_grouped(X, beta, n, y) - loglik_grouped(X[:, :3], b0, n, y))
                ok = ok & ok0
                pval = np.where(ok, _chi2_1_sf(lr), 1.0)
            hits[name] += int(np.sum(pval < alpha))
            fails[name] += int(np.sum(~ok))
            if name in auc_sum:
                for i in range(b):
                    auc_sum[name] += auroc_weighted(
                        np.concatenate([vals, vals]), y[i], n[i] - y[i])
        done += b
    out = {}
    for name in specs:
        p = hits[name] / iterations
        out[name] = {"power": p, "se": math.sqrt(p * (1 - p) / iterations), "failed": fails[name],
                     "iterations": iterations}
        if name in auc_sum:
            out[name]["auroc"] = auc_sum[name] / iterations
    p = main_hits / iterations
    out["main_effect"] = {"power": p, "se": math.sqrt(p * (1 - p) / iterations), "failed": 0,
                          "iterations": iterations}
    return out


# --------------------------------------------------------------------------------------------------
# Files
# --------------------------------------------------------------------------------------------------


def read_trial(path) -> dict[str, np.ndarray]:
    """Read a trial CSV with columns arm (0/1), outcome (0/1) and any number of numeric covariates."""
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"{path}: no rows")
    cols = rows[0].keys()
    for need in ("arm", "outcome"):
        if need not in cols:
            raise ValueError(f"{path}: missing column {need!r}")
    return {c: np.array([float(r[c]) for r in rows]) for c in cols}


def risk_score(data: dict[str, np.ndarray], weights: dict[str, float]) -> np.ndarray:
    """Weighted sum of covariates: a risk index from an external prediction tool's weights."""
    missing = [k for k in weights if k not in data]
    if missing:
        raise ValueError(f"no column(s) {missing}")
    return sum(float(w) * data[k] for k, w in weights.items())

"""The method of Thorlund et al. (2011), implemented from the paper's text and Appendices S1 and S2.

Three parts:

* ``ois``: the optimal information size of a binary-outcome meta-analysis (the paper's equation,
  with the heterogeneity correction 1 / (1 - I^2)).
* ``simulate``: cumulative meta-analyses of simulated trials (Appendix S2), each pooled after every
  trial with the DerSimonian-Laird random-effects model on the log relative risk (Appendix S1).
* ``overestimation_curve`` and ``required_number``: the proportion of pooled relative risk reductions
  above a threshold per interval of cumulative patients or events, and the number of patients or
  events needed for that proportion to drop below 10%, 5% or 1%.

Settings the paper does not state are arguments, with the choice the reproduction found to fit the
paper as the default (see the package README).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from statistics import NormalDist

import numpy as np

# Table S2, column "Proportions used for simulations": (low, high, probability).
COCHRANE_SIZES = ((20, 200, 0.50), (201, 500, 0.275), (501, 1000, 0.10), (1001, 2000, 0.075), (2001, 5000, 0.05))
# Appendix S2: "an 80% chance that a trial will have a sample size between 20 and 200 patients and a
# 20% chance that a trial will have a sample size between 200 and 500 patients".
COMMON_SIZES = ((20, 200, 0.80), (201, 500, 0.20))
SIZE_DISTRIBUTIONS = {"cochrane": COCHRANE_SIZES, "common": COMMON_SIZES}

# The four control-group risk ranges and the OIS control-group risk assumed for each (their midpoints).
PC_RANGES = {"1-5": (0.01, 0.05), "5-15": (0.05, 0.15), "15-40": (0.15, 0.40), "40-80": (0.40, 0.80)}
PC_MIDPOINTS = {"1-5": 0.03, "5-15": 0.10, "15-40": 0.275, "40-80": 0.60}

ZERO_RULES = ("exclude_double", "correct_all")
BINOMIAL_N = ("arm", "total")
BIN_RULES = ("nearest", "interval", "edge_last", "edge_first")
READ_RULES = ("first", "stays")


# --------------------------------------------------------------------------------------------- OIS


def ois(pc: float, rrr: float, i2: float = 0.0, alpha: float = 0.05, beta: float = 0.20) -> dict:
    """Optimal information size (patients and events), unrounded.

    OIS = 4 (z_{1-alpha/2} + z_{1-beta})^2 P (1 - P) / delta^2 * 1 / (1 - I^2), with
    P = (PC + PE) / 2, PE = PC (1 - RRR) and delta = PC - PE. Events = OIS * P.

    The paper writes z_{1-alpha} with alpha = 5%; its Table 2 is only reproduced with the two-sided
    1.96 (z_{1-alpha/2}), which is what ``alpha`` means here.
    """
    if not 0 < pc < 1:
        raise ValueError("pc must be a proportion between 0 and 1")
    if not 0 < rrr < 1:
        raise ValueError("rrr must be a proportion between 0 and 1")
    if not 0 <= i2 < 1:
        raise ValueError("i2 must be a proportion in [0, 1)")
    z = NormalDist().inv_cdf
    pe = pc * (1 - rrr)
    p = (pc + pe) / 2
    delta = pc - pe
    patients = 4 * (z(1 - alpha / 2) + z(1 - beta)) ** 2 * p * (1 - p) / delta**2 / (1 - i2)
    return {"patients": patients, "events": patients * p, "p": p}


def round_up(x: float, step: int) -> int:
    """Round up to the next multiple of ``step``."""
    return int(math.ceil(x / step - 1e-12) * step)


def round_ois(patients: float, events: float, pc: float) -> dict:
    """Table 2's rounding, as found to reproduce most of its printed cells.

    The footnote says events are rounded up to a multiple of 50 and patients up to a multiple of 1000
    (PC 3% and 10%) or 100 (PC 27.5% and 60%); that rule gives 32 of the 72 printed patient cells and
    46 of the 72 event cells. The printed cells follow this rule more closely (62 and 61 of 72):
    patients to the nearest multiple of 500 above 10,000 and of 100 below; events up to a multiple of 50
    for PC 27.5% and 60%, to the nearest multiple of 50 otherwise.
    """
    step = 500 if patients > 10000 else 100
    ev = round_up(events, 50) if pc > 0.2 else int(50 * round(events / 50))
    return {"patients": int(step * round(patients / step)), "events": ev}


def round_ois_footnote(patients: float, events: float, pc: float) -> dict:
    """Table 2's rounding as its footnote states it (a hypothesis test; see ``round_ois``)."""
    return {"patients": round_up(patients, 1000 if pc < 0.2 else 100), "events": round_up(events, 50)}


def ois_table(rrrs=(0.30, 0.20), pcs=(0.03, 0.10, 0.275, 0.60), i2s=(0.0, 0.25, 0.50), betas=(0.20, 0.10, 0.05),
              alpha: float = 0.05) -> list[dict]:
    """The 72 OIS values of Table 2 (unrounded and rounded)."""
    rows = []
    for pc in pcs:
        for rrr in rrrs:
            for i2 in i2s:
                for beta in betas:
                    o = ois(pc, rrr, i2, alpha, beta)
                    r = round_ois(o["patients"], o["events"], pc)
                    rows.append({"pc": pc, "rrr": rrr, "i2": i2, "beta": beta, "patients_exact": o["patients"],
                                 "events_exact": o["events"], "patients": r["patients"], "events": r["events"]})
    return rows


# ------------------------------------------------------------------------------------- simulation


@dataclass
class Scenario:
    """One simulation scenario (Fig. 1): trial sizes, control-group risk range, tau^2 and true RRR."""

    sizes: str = "cochrane"
    pc: str = "5-15"
    tau2: float = 0.15
    rrr: float = 0.0
    n_meta: int = 20000
    n_trials: int = 100

    @property
    def key(self) -> str:
        return f"{self.sizes}_pc{self.pc}_tau{self.tau2:.2f}_rrr{int(round(self.rrr * 100))}"


@dataclass
class Simulation:
    """Cumulative meta-analyses: arrays of shape (n_meta, n_trials)."""

    scenario: Scenario
    cum_patients: np.ndarray
    cum_events: np.ndarray
    log_rr: np.ndarray  # pooled DerSimonian-Laird log RR after each trial; NaN when no trial is usable yet
    tau2_dl: np.ndarray
    settings: dict = field(default_factory=dict)

    def rrr(self) -> np.ndarray:
        return 1.0 - np.exp(self.log_rr)


def draw_trials(scenario: Scenario, rng: np.random.Generator, binomial_n: str = "arm") -> dict:
    """Draw the trials of every meta-analysis of a scenario (Appendix S2).

    Trial size: a size interval with the Table S2 (or 'common') probabilities, then an integer uniform
    on it. Each arm gets n/2 patients, rounded up. Control risk PC_i ~ U(range); ln RR_i ~ N(ln(1 - RRR),
    tau^2); PE_i = PC_i RR_i (capped at 1). Events ~ Binomial(arm size, risk), or Binomial(n, risk)
    with ``binomial_n='total'`` (Appendix S2 writes bin(n_i, P_i); a hypothesis test only).
    """
    if binomial_n not in BINOMIAL_N:
        raise ValueError(f"binomial_n must be one of {BINOMIAL_N}")
    sizes = SIZE_DISTRIBUTIONS[scenario.sizes]
    shape = (scenario.n_meta, scenario.n_trials)
    probs = np.array([s[2] for s in sizes])
    lo = np.array([s[0] for s in sizes])
    hi = np.array([s[1] for s in sizes])
    cat = rng.choice(len(sizes), size=shape, p=probs / probs.sum())
    n = rng.integers(lo[cat], hi[cat] + 1)
    arm = (n + 1) // 2
    a, b = PC_RANGES[scenario.pc]
    pc = rng.uniform(a, b, size=shape)
    rr = np.exp(rng.normal(math.log(1.0 - scenario.rrr), math.sqrt(scenario.tau2), size=shape))
    pe = np.minimum(pc * rr, 1.0)
    trials_n = arm if binomial_n == "arm" else n
    e_c = rng.binomial(trials_n, pc)
    e_e = rng.binomial(trials_n, pe)
    return {"n_c": trials_n, "n_e": trials_n, "e_c": e_c, "e_e": e_e, "patients": 2 * arm}


def log_rr_and_variance(e_e, n_e, e_c, n_c, zero: str = "exclude_double"):
    """Log relative risk and its variance per trial, with 0.5 added to every cell of a trial with a zero cell.

    ``zero='exclude_double'``: trials with no events in either arm (or only events in both) carry no
    information on the relative risk and are left out (variance = inf). ``zero='correct_all'``: they are
    kept with the 0.5 correction.
    """
    if zero not in ZERO_RULES:
        raise ValueError(f"zero must be one of {ZERO_RULES}")
    e_e = np.asarray(e_e, float)
    e_c = np.asarray(e_c, float)
    n_e = np.asarray(n_e, float)
    n_c = np.asarray(n_c, float)
    zero_cell = (e_e == 0) | (e_c == 0) | (e_e == n_e) | (e_c == n_c)
    cc = np.where(zero_cell, 0.5, 0.0)
    a, b = e_e + cc, n_e - e_e + cc
    c, d = e_c + cc, n_c - e_c + cc
    y = np.log(a / (a + b)) - np.log(c / (c + d))
    v = 1 / a - 1 / (a + b) + 1 / c - 1 / (c + d)
    if zero == "exclude_double":
        double = ((e_e == 0) & (e_c == 0)) | ((e_e == n_e) & (e_c == n_c))
        v = np.where(double, np.inf, v)
        y = np.where(double, 0.0, y)
    return y, v


def cumulative_dl(y: np.ndarray, v: np.ndarray, chunk: int = 250) -> tuple[np.ndarray, np.ndarray]:
    """DerSimonian-Laird random-effects meta-analysis after each trial (Appendix S1).

    ``y`` and ``v`` have shape (n_meta, n_trials); trials with ``v = inf`` are left out. Returns the
    pooled log RR and tau^2_DL after each trial, NaN where no trial is usable yet.
    """
    y = np.atleast_2d(np.asarray(y, float))
    v = np.atleast_2d(np.asarray(v, float))
    m, k = y.shape
    w = np.where(np.isfinite(v), 1.0 / v, 0.0)
    used = np.isfinite(v)
    s1 = np.cumsum(w, axis=1)
    s2 = np.cumsum(w * w, axis=1)
    sy = np.cumsum(w * y, axis=1)
    syy = np.cumsum(w * y * y, axis=1)
    kk = np.cumsum(used, axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        q = syy - sy * sy / s1
        tau2 = np.maximum(0.0, (q - (kk - 1)) / (s1 - s2 / s1))
    tau2 = np.where(kk >= 2, tau2, 0.0)
    pooled = np.full((m, k), np.nan)
    tril = np.tril(np.ones((k, k), dtype=bool))
    vv = np.where(used, v, np.inf)
    for start in range(0, m, chunk):
        sl = slice(start, min(m, start + chunk))
        ws = 1.0 / (vv[sl, None, :] + tau2[sl, :, None])  # (c, k_step, k_trial)
        ws = np.where(tril[None], ws, 0.0)
        den = ws.sum(axis=2)
        num = (ws * y[sl, None, :]).sum(axis=2)
        with np.errstate(invalid="ignore", divide="ignore"):
            pooled[sl] = np.where(den > 0, num / den, np.nan)
    tau2 = np.where(kk >= 1, tau2, np.nan)
    return pooled, tau2


def simulate(scenario: Scenario, seed: int | np.random.SeedSequence = 0, zero: str = "exclude_double",
             binomial_n: str = "arm") -> Simulation:
    """Simulate a scenario's cumulative meta-analyses (Appendix S2) and pool them (Appendix S1)."""
    rng = np.random.default_rng(seed)
    t = draw_trials(scenario, rng, binomial_n=binomial_n)
    y, v = log_rr_and_variance(t["e_e"], t["n_e"], t["e_c"], t["n_c"], zero=zero)
    pooled, tau2 = cumulative_dl(y, v)
    patients = t["n_c"] + t["n_e"] if binomial_n == "arm" else t["patients"]
    return Simulation(scenario, np.cumsum(patients, axis=1), np.cumsum(t["e_c"] + t["e_e"], axis=1), pooled, tau2,
                      {"zero": zero, "binomial_n": binomial_n})


# ------------------------------------------------------------------------------- curves, read-off


def overestimation_curve(cum: np.ndarray, rrr: np.ndarray, threshold: float, width: float, cap: float,
                         rule: str = "nearest", min_count: int = 1) -> dict:
    """Proportion of pooled RRR above ``threshold`` per interval of ``width`` up to ``cap``.

    ``rule='nearest'`` (the default, the rule that reproduces the paper): every pooled estimate counts towards
    the point its cumulative count rounds to (to the nearest multiple of ``width``, halves to even as in R);
    estimates that round to 0 are dropped, as the paper's log axes start at ``width``.
    ``rule='interval'``: every pooled estimate whose cumulative count falls in ((j-1) width, j width] counts
    towards point j width (a meta-analysis can count several times, or not at all).
    ``rule='edge_last'``: each meta-analysis counts once at j width, with its estimate after the last trial
    at or below j width (meta-analyses that never reach j width are left out).
    ``rule='edge_first'``: its estimate after the first trial at or above j width.
    Estimates that are NaN (no usable trial yet) are left out. Points with fewer than ``min_count``
    estimates are NaN.
    """
    if rule not in BIN_RULES:
        raise ValueError(f"rule must be one of {BIN_RULES}")
    cum = np.asarray(cum, float)
    over = np.asarray(rrr) > threshold
    ok = np.isfinite(rrr)
    edges = np.arange(width, cap + width / 2, width)
    nb = len(edges)
    if rule in ("interval", "nearest"):
        if rule == "nearest":
            j = np.rint(cum / width).astype(int) - 1
        else:
            j = np.ceil(cum / width - 1e-9).astype(int) - 1
        sel = ok & (j >= 0) & (j < nb)
        n = np.bincount(j[sel], minlength=nb)
        hits = np.bincount(j[sel], weights=over[sel].astype(float), minlength=nb)
    else:
        m, k = cum.shape
        big = float(cum.max() + 10 * width + 1)
        offs = (np.arange(m) * big)[:, None]
        flat = (cum + offs).ravel()
        q = (edges[None, :] + offs).ravel()
        if rule == "edge_last":
            idx = np.searchsorted(flat, q, side="right") - 1
            row = np.repeat(np.arange(m), nb)
            valid = (idx >= row * k) & (cum[:, -1].repeat(nb) >= np.tile(edges, m))
        else:
            idx = np.searchsorted(flat, q, side="left")
            row = np.repeat(np.arange(m), nb)
            valid = idx < (row + 1) * k
        idx = np.where(valid, idx, 0)
        okf = ok.ravel()[idx] & valid
        overf = over.ravel()[idx] & okf
        n = okf.reshape(m, nb).sum(axis=0)
        hits = overf.reshape(m, nb).sum(axis=0).astype(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        p = np.where(n >= min_count, hits / np.maximum(n, 1), np.nan)
    return {"x": edges, "p": p, "n": n, "hits": np.rint(hits).astype(int)}


def required_number(x: np.ndarray, p: np.ndarray, level: float, rule: str = "first"):
    """The smallest x at which the proportion drops below ``level``.

    ``rule='first'``: the first point below the level. ``rule='stays'``: the first point after which every
    point is below it. Returns None when the curve never gets there (the paper prints '>cap').
    """
    if rule not in READ_RULES:
        raise ValueError(f"rule must be one of {READ_RULES}")
    x = np.asarray(x, float)
    p = np.asarray(p, float)
    keep = np.isfinite(p)
    x, p = x[keep], p[keep]
    below = p < level
    if not below.any():
        return None
    if rule == "first":
        return float(x[np.argmax(below)])
    if not below[-1]:
        return None
    above = np.where(~below)[0]
    return float(x[0] if len(above) == 0 else x[above[-1] + 1])


def required_table(sim: Simulation, thresholds=(0.30, 0.20), levels=(0.10, 0.05, 0.01), patient_width=500,
                   event_width=50, patient_cap=50000, event_cap=5000, bin_rule="nearest", read_rule="first",
                   min_count=1) -> list[dict]:
    """Table 1's rows for one simulation: patients and events required per threshold and level."""
    rrr = sim.rrr()
    rows = []
    for th in thresholds:
        row = {"threshold": th}
        for what, cum, w, cap in (("patients", sim.cum_patients, patient_width, patient_cap),
                                  ("events", sim.cum_events, event_width, event_cap)):
            c = overestimation_curve(cum, rrr, th, w, cap, rule=bin_rule, min_count=min_count)
            for lv in levels:
                row[f"{what}_{int(round(lv * 100))}"] = required_number(c["x"], c["p"], lv, rule=read_rule)
        rows.append(row)
    return rows


def format_required(value, cap) -> str:
    """As the paper prints it: the number, or '>cap' when the level is never reached."""
    return f">{int(cap)}" if value is None else str(int(value))

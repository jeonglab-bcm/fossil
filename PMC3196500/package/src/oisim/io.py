"""Read a meta-analysis's trials from CSV and write its cumulative DerSimonian-Laird analysis."""

from __future__ import annotations

import csv
import math

import numpy as np

from .core import cumulative_dl, log_rr_and_variance

TRIAL_COLUMNS = ("trial", "events_treatment", "n_treatment", "events_control", "n_control")
OUT_COLUMNS = ("trial", "cum_patients", "cum_events", "rr", "rrr", "tau2")


def read_trials(path) -> dict:
    """Trials in their order of publication: columns trial, events_treatment, n_treatment, events_control, n_control."""
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError("no trials in the input")
    missing = [c for c in TRIAL_COLUMNS if c not in rows[0]]
    if missing:
        raise ValueError(f"missing columns: {', '.join(missing)}")
    out = {"trial": [r["trial"] for r in rows]}
    for c in TRIAL_COLUMNS[1:]:
        out[c] = np.array([int(r[c]) for r in rows])
    if np.any(out["events_treatment"] > out["n_treatment"]) or np.any(out["events_control"] > out["n_control"]):
        raise ValueError("more events than patients in an arm")
    return out


def cumulative(trials: dict, zero: str = "exclude_double") -> list[dict]:
    """Cumulative random-effects meta-analysis after each trial: patients, events, pooled RR and RRR, tau^2."""
    y, v = log_rr_and_variance(trials["events_treatment"], trials["n_treatment"], trials["events_control"],
                               trials["n_control"], zero=zero)
    pooled, tau2 = cumulative_dl(y[None, :], v[None, :])
    cp = np.cumsum(trials["n_treatment"] + trials["n_control"])
    ce = np.cumsum(trials["events_treatment"] + trials["events_control"])
    rows = []
    for k, name in enumerate(trials["trial"]):
        mu = pooled[0, k]
        rr = math.exp(mu) if np.isfinite(mu) else None
        rows.append({"trial": name, "cum_patients": int(cp[k]), "cum_events": int(ce[k]), "rr": rr,
                     "rrr": None if rr is None else 1 - rr, "tau2": None if not np.isfinite(tau2[0, k]) else float(tau2[0, k])})
    return rows


def write_cumulative(rows: list[dict], f) -> None:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(OUT_COLUMNS)
    for r in rows:
        w.writerow([r["trial"], r["cum_patients"], r["cum_events"]] +
                   ["" if r[k] is None else f"{r[k]:.10g}" for k in ("rr", "rrr", "tau2")])

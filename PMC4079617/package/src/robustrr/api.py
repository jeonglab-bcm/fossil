"""Fit both models to a table of records and report the relative risk of each covariate."""

from __future__ import annotations

import csv
import math

import numpy as np

from .core import DEFAULT_COPIES, log_binomial, robust_poisson

Z975 = 1.959963984540054


def read_table(path):
    """Read a CSV with a header into {column: list of floats}."""
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"{path}: no records")
    cols = {}
    for c in rows[0]:
        try:
            cols[c] = [float(r[c]) for r in rows]
        except (TypeError, ValueError):
            raise ValueError(f"{path}: column {c!r} is not numeric") from None
    return cols


def fit_relative_risk(data, outcome, covariates, copy=True, copies=DEFAULT_COPIES):
    """Robust Poisson and log-binomial (COPY) fits of outcome on covariates.

    data: a mapping of column name to values (a dict of lists, a pandas DataFrame). covariates: column names,
    exposure first; a name 'a^2' adds the square of column a. Returns a list of rows, one per model and
    covariate: model, term, log_rr, se, rr, ci_low, ci_high, and for the log-binomial model the method
    ('mle' or 'copy') and the largest fitted probability.
    """
    if outcome not in data:
        raise ValueError(f"no outcome column {outcome!r}")
    y = np.asarray(data[outcome], float)
    cols = [np.ones_like(y)]
    for c in covariates:
        base, sq = (c[:-2], True) if c.endswith("^2") else (c, False)
        if base not in data:
            raise ValueError(f"no covariate column {base!r}")
        v = np.asarray(data[base], float)
        cols.append(v * v if sq else v)
    if y.size < len(cols) + 1:
        raise ValueError("too few records for the model")
    X = np.column_stack(cols)
    rows = []
    for model, fit in (("robust_poisson", robust_poisson(X, y)), ("log_binomial", log_binomial(X, y, copy, copies))):
        se = np.sqrt(np.diag(fit["cov"]))
        for j, term in enumerate(covariates, start=1):
            b, s = float(fit["coef"][j]), float(se[j])
            row = {"model": model, "term": term, "log_rr": b, "se": s, "rr": math.exp(b),
                   "ci_low": math.exp(b - Z975 * s), "ci_high": math.exp(b + Z975 * s)}
            if model == "log_binomial":
                row["method"] = fit["method"]
                row["max_fitted"] = float(fit["max_fitted"])
            rows.append(row)
    return rows

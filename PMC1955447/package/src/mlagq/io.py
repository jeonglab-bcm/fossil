"""Read clustered binary data from CSV and fit the model with named columns."""

from __future__ import annotations

import csv

import numpy as np

from .core import fit, group_data


def read_long_csv(path):
    """Read a CSV with a header into a dict of column name -> list of strings."""
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"{path}: no rows")
    return {k: [r[k] for r in rows] for k in rows[0]}


def fit_table(table, outcome, group, fixed, random=("1",), start=None, cov=False, **kw):
    """Fit a multilevel logistic model to a table (dict of columns).

    outcome: 0/1 column; group: group column; fixed: names of the fixed effects, where "1" is the intercept
    and "a:b" the product of columns a and b; random: the random effects in the same notation ("1" a random
    intercept, "x" a random slope on x), one or two of them. start: starting values (fixed effects, then the
    variance parameters); by default 0 for the fixed effects and 1 for each variance (0 for a covariance).
    Returns the Fit.
    """
    n = len(table[outcome])

    def column(term):
        if term == "1":
            return np.ones(n)
        out = np.ones(n)
        for part in term.split(":"):
            if part not in table:
                raise KeyError(f"no column {part!r}")
            out = out * np.asarray(table[part], float)
        return out

    y = np.asarray(table[outcome], float)
    X = np.stack([column(t) for t in fixed], axis=1)
    Z = np.stack([column(t) for t in random], axis=1)
    data = group_data(y, X, Z, table[group], fixed_names=list(fixed), random_names=list(random))
    if start is None:
        nv = 3 if (len(random) == 2 and cov) else len(random)
        start = [0.0] * len(fixed) + ([1.0, 0.0, 1.0] if nv == 3 else [1.0] * nv)
    return fit(data, start, cov=cov, **kw)

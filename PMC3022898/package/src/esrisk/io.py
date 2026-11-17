"""Read a table of two-sample counts and write the estimates (CSV)."""

from __future__ import annotations

import csv
import math

from .core import estimate

COUNT_COLUMNS = ("d1", "n1", "d2_exposed", "n2_exposed", "d2_unexposed", "n2_unexposed")
OUTPUT_COLUMNS = (
    "esr_s", "esr_s_log_lower", "esr_s_log_upper",
    "esr_r", "esr_r_log_lower", "esr_r_log_upper", "esr_r_binomial_lower", "esr_r_binomial_upper",
)


def read_counts(path):
    """Rows of a CSV with a 'label' column and the count columns d1, n1, d2_exposed, n2_exposed,
    d2_unexposed, n2_unexposed (cases and people in sample 1; cases and people among the exposed and
    the unexposed of sample 2)."""
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"{path}: no rows")
    missing = [c for c in ("label",) + COUNT_COLUMNS if c not in rows[0]]
    if missing:
        raise ValueError(f"{path}: missing columns {missing}")
    out = []
    for r in rows:
        try:
            out.append({"label": r["label"], **{c: int(r[c]) for c in COUNT_COLUMNS}})
        except ValueError as e:
            raise ValueError(f"{path}: row {r.get('label')!r}: counts must be whole numbers") from e
    return out


def _fmt(x, digits):
    return "" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{digits}f}"


def estimate_table(rows, zero_cells="unbounded", digits=6):
    """Both ESRs and their three 95% CIs for each row of counts, rounded to `digits` decimals."""
    out = []
    for r in rows:
        e = estimate(r["d1"], r["n1"], r["d2_exposed"], r["n2_exposed"], r["d2_unexposed"], r["n2_unexposed"],
                     zero_cells=zero_cells).as_dict()
        vals = {
            "esr_s": e["esr_s"], "esr_s_log_lower": e["ci_s_log_lower"], "esr_s_log_upper": e["ci_s_log_upper"],
            "esr_r": e["esr_r"], "esr_r_log_lower": e["ci_r_log_lower"], "esr_r_log_upper": e["ci_r_log_upper"],
            "esr_r_binomial_lower": e["ci_r_binomial_lower"], "esr_r_binomial_upper": e["ci_r_binomial_upper"],
        }
        out.append({"label": r["label"], **{k: _fmt(float(v), digits) for k, v in vals.items()}})
    return out


def write_rows(rows, f):
    w = csv.DictWriter(f, fieldnames=("label",) + OUTPUT_COLUMNS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)

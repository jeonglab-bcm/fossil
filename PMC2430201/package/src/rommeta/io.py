"""Reading study tables and writing results as CSV (standard library only)."""

from __future__ import annotations

import csv
import io as _io
from pathlib import Path

COLUMNS = ("mean_exp", "sd_exp", "n_exp", "mean_contr", "sd_contr", "n_contr")
RESULT_COLUMNS = ("measure", "k", "estimate", "ci_low", "ci_high", "p", "log_estimate", "se", "q", "tau2", "i2")


def read_studies(path) -> dict:
    """Read a CSV with one row per study and the columns of COLUMNS (and optionally `study`).

    Returns a dict of lists: `study` (names, or 1..k) and one list of floats per column.
    """
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"{path}: no studies")
    missing = [c for c in COLUMNS if c not in rows[0]]
    if missing:
        raise ValueError(f"{path}: missing column(s) {', '.join(missing)}")
    out = {"study": [r.get("study") or str(i + 1) for i, r in enumerate(rows)]}
    for c in COLUMNS:
        try:
            out[c] = [float(r[c]) for r in rows]
        except ValueError as e:
            raise ValueError(f"{path}: column {c} is not numeric ({e})") from None
    return out


def read_results(path) -> list[dict]:
    """Read a results CSV written by write_results (numbers as floats, empty cells as None)."""
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k, v in r.items():
            if k != "measure":
                r[k] = None if v == "" else float(v)
    return rows


def write_results(results, target) -> None:
    """Write MetaResult objects (or dicts) as CSV to a path or an open text file."""
    rows = [r.as_dict() if hasattr(r, "as_dict") else dict(r) for r in results]
    if isinstance(target, (str, Path)):
        with open(target, "w", newline="", encoding="utf-8") as f:
            _write(rows, f)
    else:
        _write(rows, target)


def _write(rows, f):
    w = csv.DictWriter(f, fieldnames=RESULT_COLUMNS, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if r.get(k) is None else (repr(float(r[k])) if k not in ("measure", "k") else r[k]))
                    for k in RESULT_COLUMNS})


def results_text(results) -> str:
    buf = _io.StringIO()
    write_results(results, buf)
    return buf.getvalue()

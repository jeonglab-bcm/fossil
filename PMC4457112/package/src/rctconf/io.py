"""Read citations from CSV and write scores."""

from __future__ import annotations

import csv
import gzip

FIELDS = ("pmid", "title", "abstract", "journal", "authors", "n_authors", "mesh", "mesh_qual", "chemicals",
          "keywords", "pubtypes", "rct")


def _open(path, mode="rt"):
    path = str(path)
    return gzip.open(path, mode, encoding="utf-8", newline="") if path.endswith(".gz") else open(
        path, mode, encoding="utf-8", newline="")


def read_citations(path) -> list[dict]:
    """Citations from a CSV (optionally gzipped) with a header row.

    Columns (all optional except pmid): pmid, title, abstract, journal, authors ("|"-joined
    "Last Initials"), n_authors, mesh ("|"-joined descriptor UIs, "*" before a major topic),
    mesh_qual ("D.../Q..." pairs), chemicals, keywords, pubtypes, rct (1 or 0, the label).
    """
    with _open(path) as fh:
        rows = list(csv.DictReader(fh))
    if rows and "pmid" not in rows[0]:
        raise ValueError(f"{path}: no pmid column")
    for r in rows:
        if r.get("n_authors") not in (None, ""):
            r["n_authors"] = int(r["n_authors"])
        else:
            r["n_authors"] = None
        if r.get("rct") not in (None, ""):
            r["rct"] = int(r["rct"])
    return rows


def write_scores(rows, fh) -> None:
    """Write dicts with pmid, margin and confidence (and rct when known) as CSV."""
    rows = list(rows)
    cols = [c for c in ("pmid", "rct", "margin", "confidence") if rows and c in rows[0]]
    w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: (f"{r[k]:.6f}" if isinstance(r[k], float) else r[k]) for k in cols})

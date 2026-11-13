"""Read and write the CSV files the command line and the tutorial use."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np


def read_expression(path):
    """CSV with a 'gene' column and one column per condition (blank = missing). Returns (genes, X)."""
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    head = rows[0]
    if head[0] != "gene":
        raise ValueError("the expression file needs a first column named 'gene'")
    genes = [r[0] for r in rows[1:]]
    X = np.array([[float(v) if v.strip() else np.nan for v in r[1:]] for r in rows[1:]], dtype=float)
    return genes, X


def read_edges(path):
    """CSV with columns gene_a, gene_b. Returns a list of (a, b)."""
    with open(path, newline="", encoding="utf-8") as f:
        return [(r["gene_a"], r["gene_b"]) for r in csv.DictReader(f)]


def read_pairs(path):
    """CSV with columns gene_a, gene_b and optionally label (1, 0 or blank for unlabelled)."""
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    pairs = [(r["gene_a"], r["gene_b"]) for r in rows]
    labels = None
    if rows and "label" in rows[0]:
        labels = np.array([int(r["label"]) if r["label"].strip() else -1 for r in rows])
    return pairs, labels


def write_table(path_or_file, header, rows):
    close = False
    f = path_or_file
    if isinstance(path_or_file, (str, Path)):
        f = open(path_or_file, "w", newline="", encoding="utf-8")
        close = True
    w = csv.writer(f, lineterminator="\n")
    w.writerow(header)
    for r in rows:
        w.writerow([f"{v:.10g}" if isinstance(v, float) else v for v in r])
    if close:
        f.close()


def read_table(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

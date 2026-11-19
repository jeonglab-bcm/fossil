"""Command line: gecon INPUT.tsv [-o EDGES.csv] [--theta T] [--tau DEG] [--standardize] [--segments N,N,...]."""

from __future__ import annotations

import argparse
import sys

import numpy as np

from . import DEFAULT_TAU, DEFAULT_THETA, __version__, edge_list, edge_patterns, example_path, gecon, read_matrix, write_edges


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="gecon",
        description="Signed gene co-expression network from local expression patterns (GeCON, Roy et al. 2014).",
    )
    ap.add_argument("input", nargs="?", help="TSV or CSV: header row, then one row per gene (name, then values in condition order)")
    ap.add_argument("-o", "--output", help="output CSV of connected pairs (default: standard output)")
    ap.add_argument("--theta", type=float, default=DEFAULT_THETA, help=f"support threshold, a fraction of the edges (default {DEFAULT_THETA})")
    ap.add_argument("--tau", type=float, default=DEFAULT_TAU, help=f"angle tolerance in degrees (default {DEFAULT_TAU:g})")
    ap.add_argument("--standardize", action="store_true", help="centre and scale each gene before GeCON (mean 0, sd 1)")
    ap.add_argument("--segments", help="lengths of separate time series in the columns, e.g. 21,21,21")
    ap.add_argument("--patterns", action="store_true", help="print each gene's edge angles and regulation instead of the network")
    ap.add_argument("--example-path", metavar="NAME", nargs="?", const="gds3702_mrps26_pfn2.tsv",
                    help="print the path of a bundled example file and exit")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = ap.parse_args(argv)

    if args.example_path:
        print(example_path(args.example_path))
        return 0
    if not args.input:
        ap.error("INPUT is required")
    genes, _, X = read_matrix(args.input)
    if args.patterns:
        r, a = edge_patterns(X)
        print("gene\tedge\tangle\tregulation")
        for g, rr, aa in zip(genes, r, a):
            for k, (x, y) in enumerate(zip(aa, rr), 1):
                print(f"{g}\t{k}\t{x:.4f}\t{int(y)}")
        return 0
    if args.standardize:
        sd = X.std(1, keepdims=True)
        if (sd == 0).any():
            ap.error("a gene has constant values; it cannot be standardised")
        X = (X - X.mean(1, keepdims=True)) / sd
    segments = [int(s) for s in args.segments.split(",")] if args.segments else None
    A, sup = gecon(X, theta=args.theta, tau=args.tau, segments=segments)
    rows = edge_list(A, sup, genes)
    if args.output:
        with open(args.output, "w", newline="", encoding="utf-8") as f:
            write_edges(rows, f)
    else:
        write_edges(rows, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())

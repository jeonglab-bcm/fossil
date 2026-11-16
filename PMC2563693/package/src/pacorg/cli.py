"""Command line: pacorg EXPRESSION.gct LABELS.cls GENESETS.gmt [-o OUT.csv] [--top N]."""

from __future__ import annotations

import argparse
import sys

from . import __version__, example_path, infer_pathways, read_cls, read_gct, read_gmt
from .core import write_results


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="pacorg",
        description="Condition-responsive genes (CORGs) and pathway activity scores for two classes "
        "of samples (Lee et al. 2008).",
    )
    ap.add_argument("expression", nargs="?", help="expression matrix, GCT 1.2 (genes x samples)")
    ap.add_argument("labels", nargs="?", help="class labels, CLS (two classes)")
    ap.add_argument("genesets", nargs="?", help="gene sets, GMT")
    ap.add_argument("-o", "--output", help="output CSV (default: standard output)")
    ap.add_argument("--top", type=int, help="keep the N gene sets with the largest |Tian score| (default: all)")
    ap.add_argument("--example", action="store_true", help="run on the bundled example input")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = ap.parse_args(argv)

    if args.example:
        args.expression = str(example_path("example.gct"))
        args.labels = str(example_path("example.cls"))
        args.genesets = str(example_path("example.gmt"))
    if not (args.expression and args.labels and args.genesets):
        ap.error("EXPRESSION, LABELS and GENESETS are required (or --example)")
    genes, _, X = read_gct(args.expression)
    results = infer_pathways(X, genes, read_cls(args.labels), read_gmt(args.genesets))
    if args.top:
        results = sorted(results, key=lambda r: -abs(r.tian))[: args.top]
    if args.output:
        with open(args.output, "w", newline="", encoding="utf-8") as f:
            write_results(results, f)
    else:
        write_results(results, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())

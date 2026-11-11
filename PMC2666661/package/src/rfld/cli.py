"""Command line: rfld INPUT.csv [-o OUTPUT.csv] [--revised-tree] [--ld-threshold R] [...]."""

from __future__ import annotations

import argparse
import sys

from . import __version__, example_path, importance_table, read_genotypes, write_table


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="rfld",
        description="Random forest importance of SNPs: original (RF0) or revised tree builder (RF1, "
                    "Meng et al. 2009), with the original (IM0) and revised (IM1) importance.")
    ap.add_argument("input", nargs="?", help="CSV with a 0/1 status column and one column per SNP (0, 1, 2)")
    ap.add_argument("-o", "--output", help="output CSV (default: standard output)")
    ap.add_argument("--status", default="status", help="name of the case-control column (default: status)")
    ap.add_argument("--revised-tree", action="store_true", help="RF1: keep SNPs in LD out of the same tree")
    ap.add_argument("--ld-threshold", type=float, default=0.5,
                    help="RF1 drops SNPs with r^2 above this with a SNP the tree already uses (default 0.5)")
    ap.add_argument("--ntree", type=int, default=5000, help="number of trees (default 5000)")
    ap.add_argument("--mtry", type=int, default=35, help="split candidates per node (default 35)")
    ap.add_argument("--seed", type=int, default=1, help="random seed (default 1)")
    ap.add_argument("--example-path", action="store_true", help="print the path of the bundled example and exit")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    a = ap.parse_args(argv)
    if a.example_path:
        print(example_path())
        return 0
    if not a.input:
        ap.error("INPUT is required")
    X, y, names = read_genotypes(a.input, a.status)
    rows = importance_table(X, y, names, ntree=a.ntree, mtry=a.mtry, revised_tree=a.revised_tree,
                            ld_threshold=a.ld_threshold, seed=a.seed)
    if a.output:
        with open(a.output, "w", newline="", encoding="utf-8") as fh:
            write_table(rows, fh)
    else:
        write_table(rows, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())

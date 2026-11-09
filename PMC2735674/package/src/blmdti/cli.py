"""Command line: score every drug-target pair of a network with bipartite local models.

    blmdti NETWORK.txt --chemical CHEM.txt --genomic GEN.txt -o scores.tsv

The three input files are tab separated with a header row and a label column, in the format of the
Yamanishi et al. (2008) benchmark: the network has target proteins as rows and drugs as columns,
the chemical matrix is drug by drug and the genomic matrix is target by target.
"""

from __future__ import annotations

import argparse
import sys

from . import (
    __version__,
    aggregate,
    auc,
    aupr,
    blm_drug_scores,
    blm_target_scores,
    example_path,
    interactions,
    make_psd,
    read_matrix,
    read_network,
    write_matrix,
)
from .core import NO_POSITIVE_RULES

METHODS = ("blmd", "blmt", "max")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="blmdti",
        description=(
            "Score drug-target pairs with bipartite local models (Bleakley and Yamanishi 2009)."
        ),
    )
    ap.add_argument("network", nargs="?", help="adjacency file: targets as rows, drugs as columns")
    ap.add_argument("--chemical", help="drug by drug chemical similarity matrix")
    ap.add_argument("--genomic", help="target by target sequence similarity matrix")
    ap.add_argument(
        "--method",
        default="max",
        choices=METHODS,
        help="blmd (the target's local model over drugs), blmt (the drug's local model over"
        " targets) or max, the paper's m(BLMd,BLMt) (default: max)",
    )
    ap.add_argument(
        "--C", type=float, default=1.0, help="SVM regularization (default: 1, as in the paper)"
    )
    ap.add_argument(
        "--no-positive",
        default="minus_one",
        choices=NO_POSITIVE_RULES,
        help="score for a local model with no positive training example (default: minus_one)",
    )
    ap.add_argument(
        "-o", "--output", help="output matrix, drugs as rows (default: standard output)"
    )
    ap.add_argument(
        "--metrics", action="store_true", help="also print the AUC and AUPR of the scores"
    )
    ap.add_argument(
        "--example-path",
        action="store_true",
        help="print the path of the bundled example network and exit",
    )
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = ap.parse_args(argv)

    if args.example_path:
        print(example_path())
        return 0
    if not args.network:
        ap.error("NETWORK is required")
    needs_chemical = args.method in ("blmd", "max")
    needs_genomic = args.method in ("blmt", "max")
    if needs_chemical and not args.chemical:
        ap.error(f"--chemical is required for --method {args.method}")
    if needs_genomic and not args.genomic:
        ap.error(f"--genomic is required for --method {args.method}")

    drugs, targets, adjacency = read_network(args.network)
    parts = []
    if needs_chemical:
        rows, columns, chemical = read_matrix(args.chemical)
        if rows != drugs or columns != drugs:
            ap.error("--chemical is not in the network's drug order")
        kernel, _ = make_psd(chemical)
        parts.append(blm_drug_scores(adjacency, kernel, C=args.C, no_positive=args.no_positive))
    if needs_genomic:
        rows, columns, genomic = read_matrix(args.genomic)
        if rows != targets or columns != targets:
            ap.error("--genomic is not in the network's target order")
        kernel, _ = make_psd(genomic)
        parts.append(blm_target_scores(adjacency, kernel, C=args.C, no_positive=args.no_positive))
    scores = aggregate(*parts)

    if args.output:
        with open(args.output, "w", newline="", encoding="utf-8") as f:
            write_matrix(drugs, targets, scores, f)
    else:
        write_matrix(drugs, targets, scores, sys.stdout)
    if args.metrics:
        labels = interactions(adjacency)
        print(
            f"# AUC {100 * auc(labels, scores):.1f} AUPR {100 * aupr(labels, scores):.1f}",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())

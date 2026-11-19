"""Command line: fgnssl EXPRESSION.csv INTERACTIONS.csv PAIRS.csv [-o OUT.csv]."""

from __future__ import annotations

import argparse
import sys

from . import FEATURE_NAMES, __version__, build_fgn, pair_features, predict, read_edges, read_expression, read_pairs, write_table
from .fgn import L1_DEFAULT
from .ssl import ALPHA_DEFAULT


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="fgnssl",
        description="Build the weighted functional gene network, compute the 18 features of each gene pair "
                    "and, when PAIRS.csv has a label column, score the unlabelled pairs by label spreading.")
    ap.add_argument("expression", help="CSV: gene, then one column per condition")
    ap.add_argument("interactions", help="CSV: gene_a, gene_b (protein interactions and complex co-members)")
    ap.add_argument("pairs", help="CSV: gene_a, gene_b[, label] with label 1, 0 or blank (unlabelled)")
    ap.add_argument("-o", "--output", help="output CSV (default: standard output)")
    ap.add_argument("--l1", type=float, default=L1_DEFAULT, help=f"eq. 2 trade-off L1 (default {L1_DEFAULT})")
    ap.add_argument("--sigma", type=float, help="SSL length scale (default: the median distance)")
    ap.add_argument("--alpha", type=float, default=ALPHA_DEFAULT, help=f"SSL alpha (default {ALPHA_DEFAULT})")
    ap.add_argument("--binary", action="store_true", help="use the unweighted network")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    a = ap.parse_args(argv)
    genes, X = read_expression(a.expression)
    net = build_fgn(genes, X, read_edges(a.interactions), l1=a.l1)
    pairs, labels = read_pairs(a.pairs)
    F = pair_features(net, pairs, weighted=not a.binary)
    header = ["gene_a", "gene_b", *FEATURE_NAMES]
    score = None
    if labels is not None:
        score = predict(F, labels, sigma=a.sigma, alpha=a.alpha)
        header.append("sgi_score")
    rows = []
    for k, (ga, gb) in enumerate(pairs):
        row = [ga, gb, *[float(v) for v in F[k]]]
        if score is not None:
            row.append(float(score[k]))
        rows.append(row)
    write_table(a.output if a.output else sys.stdout, header, rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())

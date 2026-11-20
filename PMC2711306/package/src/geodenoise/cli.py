"""Command line: geodenoise {distances,scores,predict} NETWORK.tsv [options]."""

from __future__ import annotations

import argparse
import csv
import sys

import numpy as np

from . import (
    DELTA,
    PRIOR_EDGE,
    __version__,
    candidate_false_positives,
    confidence_scores,
    embed,
    example_path,
    largest_component,
    learn_densities,
    pairwise_distances,
    predict,
    read_network,
    write_scores,
)


def _open(path):
    return open(path, "w", newline="", encoding="utf-8") if path else sys.stdout


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="geodenoise",
        description="Geometric de-noising of protein-protein interaction networks "
        "(Kuchaiev et al. 2009): embed the network, then predict missing interactions and "
        "score every close pair.",
    )
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    ap.add_argument("--example-path", action="store_true",
                    help="print the path of the bundled example network and exit")
    sub = ap.add_subparsers(dest="command")

    def common(p):
        p.add_argument("network", help="edge list: two columns of protein names (TSV or CSV)")
        p.add_argument("--dim", type=int, default=5, help="embedding dimension (default 5)")
        p.add_argument("-o", "--output", help="output CSV (default: standard output)")
        p.add_argument("--all-components", action="store_true",
                       help="embed every component (default: the largest connected component)")

    p = sub.add_parser("distances", help="embed and write the distance of every pair")
    common(p)
    p = sub.add_parser("predict", help="Algorithm 1: non-adjacent pairs closer than epsilon")
    common(p)
    p.add_argument("--epsilon", type=float, required=True, help="distance threshold")
    p = sub.add_parser("scores", help="Algorithm 2: confidence scores of pairs within delta")
    common(p)
    p.add_argument("--delta", type=float, default=DELTA, help=f"distance cut-off (default {DELTA})")
    p.add_argument("--prior", type=float, default=PRIOR_EDGE,
                   help=f"prior P(edge) (default {PRIOR_EDGE})")
    p.add_argument("--learn-set-size", type=int, default=None,
                   help="training distances per class (default: min(18000, edges))")
    p.add_argument("--seed", type=int, default=0, help="random seed for the training sample and EM")
    p.add_argument("--min-score", type=float, default=0.0, help="write only pairs scoring at least this")
    p.add_argument("--false-positives", help="also write edges further apart than delta to this TSV")
    args = ap.parse_args(argv)

    if args.example_path:
        print(example_path())
        return 0
    if not args.command:
        ap.error("a command is required: distances, predict or scores")
    net = read_network(args.network)
    if not args.all_components:
        net = largest_component(net)
    D = pairwise_distances(embed(net, args.dim))
    with _open(args.output) as f:
        if args.command == "distances":
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["protein_a", "protein_b", "distance"])
            iu, ju = np.triu_indices(net.n, 1)
            for i, j in zip(iu, ju):
                w.writerow([net.nodes[i], net.nodes[j], f"{D[i, j]:.6f}"])
        elif args.command == "predict":
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["protein_a", "protein_b", "distance"])
            for i, j in predict(net, D, args.epsilon):
                w.writerow([net.nodes[i], net.nodes[j], f"{D[i, j]:.6f}"])
        else:
            size = args.learn_set_size or min(18000, net.m)
            f_edge, f_non = learn_densities(net, D, size=size, rng=args.seed)
            sc = confidence_scores(net, D, f_edge, f_non, prior_edge=args.prior, delta=args.delta)
            write_scores(net, sc[sc["score"] >= args.min_score], f)
            if args.false_positives:
                with open(args.false_positives, "w", encoding="utf-8") as g:
                    g.write("protein_a\tprotein_b\tdistance\n")
                    for i, j in candidate_false_positives(net, D, args.delta):
                        g.write(f"{net.nodes[i]}\t{net.nodes[j]}\t{D[i, j]:.6f}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

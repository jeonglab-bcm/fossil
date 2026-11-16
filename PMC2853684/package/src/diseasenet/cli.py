"""Command line: diseasenet NETWORK CANDIDATES [-m METHOD ...] [--clusters FILE] [-o OUTPUT.csv]."""

from __future__ import annotations

import argparse
import csv
import sys

from . import (
    __version__,
    cluster_scores,
    example_path,
    neighborhood_scores,
    oti_scores,
    prop_scores,
    read_candidates,
    read_network,
    rw_scores,
)

METHODS = {
    "neighborhood": lambda net, ann, c: neighborhood_scores(net, ann, c),
    "oti": lambda net, ann, c: oti_scores(net, ann, c),
    "rw": lambda net, ann, c: rw_scores(net, ann, c),
    "prop": lambda net, ann, c: prop_scores(net, ann, c),
}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="diseasenet",
        description="Leave-one-out gene-disease scores from a protein interaction network "
        "(Navlakha and Kingsford 2010).",
    )
    ap.add_argument("network", nargs="?", help="interactions, two protein names per line")
    ap.add_argument("candidates", nargs="?", help="CSV with columns gene, disease, known (1 or 0)")
    ap.add_argument("-m", "--method", action="append", choices=sorted(METHODS) + ["clusters"],
                    help="score to compute (repeat for several; default: neighborhood, oti, rw, prop)")
    ap.add_argument("--clusters", help="clusters, one per line, members separated by tabs (for -m clusters)")
    ap.add_argument("--self-loops", action="store_true", help="add a self-interaction to every protein")
    ap.add_argument("-o", "--output", help="output CSV (default: standard output)")
    ap.add_argument("--example-path", action="store_true", help="print the bundled example network and candidates and exit")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = ap.parse_args(argv)

    if args.example_path:
        print(example_path("network.tsv"))
        print(example_path("candidates.csv"))
        return 0
    if not args.network or not args.candidates:
        ap.error("NETWORK and CANDIDATES are required")
    methods = args.method or ["neighborhood", "oti", "rw", "prop"]
    if "clusters" in methods and not args.clusters:
        ap.error("-m clusters needs --clusters FILE")
    net = read_network(args.network, self_loops=args.self_loops)
    cands = read_candidates(args.candidates)
    ann = cands.annotations()
    cols = {}
    for m in methods:
        if m == "clusters":
            with open(args.clusters, encoding="utf-8") as f:
                clusters = [line.rstrip("\n").split("\t") for line in f if line.strip()]
            cols[m] = cluster_scores(clusters, ann, cands)
        else:
            cols[m] = METHODS[m](net, ann, cands)
    out = open(args.output, "w", newline="", encoding="utf-8") if args.output else sys.stdout
    try:
        w = csv.writer(out)
        w.writerow(["gene", "disease", "known", *methods])
        for k, (g, d, kn) in enumerate(zip(cands.genes, cands.diseases, cands.known)):
            w.writerow([g, d, int(kn), *(repr(float(cols[m][k])) for m in methods)])
    finally:
        if args.output:
            out.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

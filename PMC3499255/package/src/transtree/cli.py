"""Command line for transtree.

    transtree EPI.csv HAMMING.csv --s 8176 --m 2.076e-5 [-o OUT.json] [--iters N] [--seed K]

Reads an epidemiological CSV (premise,x_km,y_km,Tobs,Tend,Dobs) and a square
Hamming-distance CSV, runs the MCMC, and writes a JSON summary: the inferred
most-likely transmission tree, each premise's source probabilities, and the
posterior medians and 95% intervals of the mean latency duration and mean
transmission distance.
"""

from __future__ import annotations

import argparse
import json
import sys

import numpy as np

from . import MCMCConfig, __version__, example_path, read_dataset, run_mcmc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="transtree", description=__doc__.splitlines()[2].strip())
    ap.add_argument("epi", nargs="?", help="CSV: premise,x_km,y_km,Tobs,Tend,Dobs")
    ap.add_argument("hamming", nargs="?", help="square Hamming-distance CSV (no header)")
    ap.add_argument("--s", type=float, default=8176.0, help="sequence length")
    ap.add_argument("--m", type=float, default=2.076e-5, help="substitution rate per nt per day")
    ap.add_argument("--iters", type=int, default=50000)
    ap.add_argument("--burn", type=float, default=0.4)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("-o", "--output", help="output JSON (default: standard output)")
    ap.add_argument("--example-path", action="store_true",
                    help="print the path of the bundled example input and exit")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = ap.parse_args(argv)

    if args.example_path:
        print(example_path("example_epi.csv"))
        return 0
    if not args.epi or not args.hamming:
        ap.error("EPI and HAMMING csv paths are required")

    data = read_dataset(args.epi, args.hamming, s=args.s, m=args.m)
    post = run_mcmc(data, MCMCConfig(iters=args.iters, burn_in_frac=args.burn, seed=args.seed))
    lat = post.median_ci(post.mean_latency)
    dist = post.median_ci(post.mean_distance)
    result = dict(
        names=list(data.names),
        most_likely_tree=[("external" if s == -1 else data.names[s]) for s in post.best_tree],
        most_likely_tree_probability=float(post.best_tree_prob),
        source_probabilities={data.names[i]: {
            ("external" if j == data.I else data.names[j]): round(float(post.trans_prob[i, j]), 4)
            for j in range(data.I + 1) if post.trans_prob[i, j] > 0}
            for i in range(data.I)},
        mean_latency_days=dict(median=lat[0], ci95=[lat[1], lat[2]]),
        mean_transmission_distance_km=dict(median=dist[0], ci95=[dist[1], dist[2]]),
    )
    text = json.dumps(result, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    else:
        sys.stdout.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Command line.

  mlagq INPUT.csv --outcome y --group group --fixed 1 z x x:z --random 1 x [--cov] [-o OUT.csv]
  mlagq --simulate --groups 30 --size 30 --var0 0.67 --reps 50 [--seed S] [-o OUT.csv]

The first form fits a multilevel logistic model and writes parameter, estimate, se (CSV); the fit's status goes
to standard error. The second runs replicates of one cell of the paper's design and writes the % converged, the
% relative bias and the non-coverage of each parameter.
"""

from __future__ import annotations

import argparse
import csv
import sys

from . import __version__, example_path, fit_table, read_long_csv
from . import simulation as sim


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="mlagq",
        description="Multilevel logistic regression by maximum likelihood with adaptive Gauss-Hermite quadrature "
                    "(Moineddin, Matheson and Glazier 2007).",
    )
    ap.add_argument("input", nargs="?", help="CSV with one row per observation")
    ap.add_argument("--outcome", default="y", help="0/1 outcome column (default y)")
    ap.add_argument("--group", default="group", help="group column (default group)")
    ap.add_argument("--fixed", nargs="+", default=["1", "z", "x", "x:z"],
                    help="fixed effects: 1 for the intercept, a column name, or a:b for a product (default 1 z x x:z)")
    ap.add_argument("--random", nargs="+", default=["1", "x"],
                    help="one or two random effects in the same notation (default 1 x)")
    ap.add_argument("--cov", action="store_true", help="estimate the covariance of the two random effects")
    ap.add_argument("--start", nargs="+", type=float,
                    help="starting values: the fixed effects, then the variance parameters")
    ap.add_argument("--qpoints", type=int, help="quadrature points per dimension (default: chosen as NLMIXED does)")
    ap.add_argument("-o", "--output", help="output CSV (default: standard output)")
    ap.add_argument("--simulate", action="store_true", help="run replicates of one cell of the paper's design")
    ap.add_argument("--groups", type=int, default=30)
    ap.add_argument("--size", type=int, default=30)
    ap.add_argument("--var0", type=float, default=0.67)
    ap.add_argument("--reps", type=int, default=20)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--example-path", action="store_true", help="print the path of the bundled example input and exit")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    a = ap.parse_args(argv)

    if a.example_path:
        print(example_path())
        return 0
    out = open(a.output, "w", newline="", encoding="utf-8") if a.output else sys.stdout
    w = csv.writer(out, lineterminator="\n")
    try:
        if a.simulate:
            cell = {"id": "cli", "index": 0, "groups": a.groups, "size": a.size, "gamma": sim.GAMMA_MAIN,
                    "var0": a.var0, "var1": 1.0, "dists": None}
            recs = [sim.run_replicate("main", cell, r, a.seed)[0] for r in range(a.reps)]
            s = sim.summarize(recs, sim.GAMMA_MAIN, a.var0, 1.0, scale="variance", ci="variance")
            w.writerow(["parameter", "converged_pct", "bias_pct", "noncoverage"])
            for p in sim.PARAMS:
                w.writerow([p, f"{s['converged_pct']:.1f}", f"{s[p]['bias_pct']:.4f}", f"{s[p]['noncoverage']:.4f}"])
            return 0
        if not a.input:
            ap.error("INPUT is required (or --simulate)")
        f = fit_table(read_long_csv(a.input), a.outcome, a.group, a.fixed, a.random, start=a.start, cov=a.cov,
                      qpoints=a.qpoints)
        w.writerow(["parameter", "estimate", "se"])
        for n, e, s in zip(f.names, f.estimate, f.se):
            w.writerow([n, f"{e:.6f}", f"{s:.6f}"])
        print(f"status {f.status}, converged {f.converged}, {f.iterations} iterations, {f.qpoints} quadrature "
              f"points per dimension, log-likelihood {f.loglik:.6f}", file=sys.stderr)
    finally:
        if a.output:
            out.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

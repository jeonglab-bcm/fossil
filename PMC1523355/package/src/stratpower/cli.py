"""Command line.

  stratpower test TRIAL.csv (--subgroup COLUMN | --weights COL=W,COL=W,...) [-o OUT.csv]
      Interaction test of a subgroup or a risk score with treatment on one trial's data.
  stratpower power [--n-rf 6] [--prevalence .25] [--effect 2] [--scale or] [--cer0 .0075]
                   [--harm .003] [--iterations 2000] [--seed 0]
      Power of the conventional (one RF), dichotomized-index and continuous-index analyses by simulation.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys

from . import __version__, example_path
from .core import interaction_test, population, read_trial, risk_score, simulate_power


def _weights(s: str) -> dict[str, float]:
    out = {}
    for part in s.split(","):
        k, _, v = part.partition("=")
        if not k or not v:
            raise argparse.ArgumentTypeError(f"bad weight {part!r}; use COLUMN=WEIGHT")
        out[k.strip()] = float(v)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="stratpower", description="Risk-stratified vs conventional subgroup analysis "
                                 "of clinical trials (Hayward et al. 2006).")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    ap.add_argument("--example-path", action="store_true", help="print the path of the bundled example trial and exit")
    sub = ap.add_subparsers(dest="cmd")

    t = sub.add_parser("test", help="interaction test on a trial's data (CSV with arm, outcome and covariates)")
    t.add_argument("input")
    g = t.add_mutually_exclusive_group(required=True)
    g.add_argument("--subgroup", help="a 0/1 column: conventional subgroup analysis")
    g.add_argument("--weights", type=_weights, help="risk score as COLUMN=WEIGHT,...: risk-stratified analysis")
    t.add_argument("-o", "--output", help="output CSV (default: standard output)")

    p = sub.add_parser("power", help="power of the three analyses by simulation")
    p.add_argument("--n-rf", type=int, default=6)
    p.add_argument("--prevalence", type=float, default=0.25)
    p.add_argument("--effect", type=float, default=2.0, help="odds ratio (or relative risk) of each RF")
    p.add_argument("--scale", choices=["or", "rr"], default="or")
    p.add_argument("--cer0", type=float, default=0.0075, help="5-year control event rate with no RF")
    p.add_argument("--harm", type=float, default=0.003, help="treatment complications per person-year")
    p.add_argument("--n-per-arm", type=int, default=4400)
    p.add_argument("--iterations", type=int, default=2000)
    p.add_argument("--seed", type=int, default=0)

    args = ap.parse_args(argv)
    if args.example_path:
        print(example_path())
        return 0
    if args.cmd == "test":
        data = read_trial(args.input)
        if args.subgroup:
            if args.subgroup not in data:
                ap.error(f"no column {args.subgroup!r}")
            z, label = data[args.subgroup], args.subgroup
        else:
            z, label = risk_score(data, args.weights), "score"
        r = interaction_test(z, data["arm"], data["outcome"])
        f = open(args.output, "w", newline="", encoding="utf-8") if args.output else sys.stdout
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["subgroup", "term", "coef", "se"])
        for term in ("intercept", "z", "arm", "z_x_arm"):
            w.writerow([label, term, repr(r["coef"][term]), repr(r["se"][term])])
        w.writerow([label, "p_interaction", repr(r["p_interaction"]), ""])
        if args.output:
            f.close()
        return 0
    if args.cmd == "power":
        pop = population(args.n_rf, args.prevalence, args.effect, args.cer0, args.scale)
        k = pop.count()
        r = simulate_power(pop, {"conventional": pop.patterns[:, 0], "dichotomized": (k >= 2) * 1.0, "continuous": k},
                           iterations=args.iterations, seed=args.seed, n_per_arm=args.n_per_arm, harm_per_year=args.harm)
        print(json.dumps({n: round(v["power"], 4) for n, v in r.items()}, indent=1))
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())

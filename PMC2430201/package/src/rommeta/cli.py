"""Command line.

  rommeta meta INPUT.csv [-o OUTPUT.csv] [--measure MD SMD RoM] [--z 1.96]
  rommeta simulate --sd 40 --effect 0.5 --n-exp 10 --n-contr 10 --k 5 [--tau 0.5] [--skewed] [--reps 10000] [--seed 1]
  rommeta --example-path
"""

from __future__ import annotations

import argparse
import json
import sys

from . import MEASURES, Z95, Scenario, __version__, analyze, example_path, read_studies, run_scenario, write_results


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="rommeta", description="Ratio of means (RoM), MD and SMD random-effects "
                                 "meta-analysis, and the simulation study of Friedrich, Adhikari and Beyene (2008).")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    ap.add_argument("--example-path", action="store_true", help="print the path of the bundled example input and exit")
    sub = ap.add_subparsers(dest="command")

    m = sub.add_parser("meta", help="pool a CSV of studies (columns mean_exp, sd_exp, n_exp, mean_contr, sd_contr, n_contr)")
    m.add_argument("input")
    m.add_argument("-o", "--output", help="output CSV (default: standard output)")
    m.add_argument("--measure", nargs="+", choices=MEASURES, default=list(MEASURES))
    m.add_argument("--z", type=float, default=Z95, help=f"CI multiplier (default {Z95}, the paper's)")

    s = sub.add_parser("simulate", help="run one scenario of the simulation study and print its performance as JSON")
    s.add_argument("--sd", type=float, required=True, help="SD of both arms, %% of the control mean (10, 40, 70)")
    s.add_argument("--effect", type=float, required=True, help="true SMD (0.2, 0.5, 0.8)")
    s.add_argument("--n-exp", type=int, required=True)
    s.add_argument("--n-contr", type=int, required=True)
    s.add_argument("--k", type=int, required=True, help="trials per meta-analysis")
    s.add_argument("--tau", type=float, default=0.0, help="heterogeneity in SD units (0 or 0.5)")
    s.add_argument("--skewed", action="store_true", help="draw from the paper's skewed mixture instead of a normal")
    s.add_argument("--reps", type=int, default=10_000)
    s.add_argument("--seed", type=int, default=None)
    args = ap.parse_args(argv)

    if args.example_path:
        print(example_path())
        return 0
    if args.command == "meta":
        results = analyze(read_studies(args.input), measures=args.measure, z=args.z)
        if args.output:
            write_results(results, args.output)
        else:
            write_results(results, sys.stdout)
        return 0
    if args.command == "simulate":
        sc = Scenario(sd=args.sd, effect=args.effect, n_exp=args.n_exp, n_contr=args.n_contr, k=args.k, tau=args.tau,
                      distribution="skewed" if args.skewed else "normal")
        res = run_scenario(sc, args.reps, seed=args.seed)
        keep = ("bias", "coverage", "power", "i2")
        print(json.dumps({"scenario": sc.as_dict(), "true": sc.true,
                          "performance": {m: {k: round(v[k], 2) for k in keep} for m, v in res.items()}}, indent=1))
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())

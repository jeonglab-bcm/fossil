"""Command line.

  robustrr fit DATA.csv --outcome y --covariates x z z^2 [-o OUT.csv] [--copies C] [--no-copy]
  robustrr simulate --rr 2.0 --outcome-rate 10 --form nonlinear --level strong [--n 1500] [--reps 1000]
                    [--seed 1] [-o OUT.json]
"""

from __future__ import annotations

import argparse
import csv
import json
import sys

from . import DEFAULT_COPIES, __version__, example_path, fit_relative_risk, read_table, run_scenario, scenario, summarize

COLUMNS = ["model", "term", "log_rr", "se", "rr", "ci_low", "ci_high", "method", "max_fitted"]


def write_rows(rows, f):
    w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: (f"{v:.10g}" if isinstance(v, float) else v) for k, v in r.items()})


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="robustrr", description="Relative risks by robust Poisson and log-binomial "
                                 "(COPY method) regression, and the outlier simulation of Chen et al. (2014).")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    ap.add_argument("--example-path", action="store_true", help="print the path of the bundled example data and exit")
    sub = ap.add_subparsers(dest="command")
    f = sub.add_parser("fit", help="fit both models to a CSV of records")
    f.add_argument("data", help="CSV with a header; the outcome column holds 0 or 1")
    f.add_argument("--outcome", required=True, help="outcome column (0/1)")
    f.add_argument("--covariates", nargs="+", required=True, help="covariate columns, exposure first; name^2 adds a square")
    f.add_argument("--copies", type=float, default=DEFAULT_COPIES, help=f"C of the COPY method (default {DEFAULT_COPIES:,})")
    f.add_argument("--no-copy", action="store_true", help="report the plain log-binomial fit even when it does not converge")
    f.add_argument("-o", "--output", help="output CSV (default: standard output)")
    s = sub.add_parser("simulate", help="run one scenario of the simulation study")
    s.add_argument("--rr", type=float, required=True, choices=[1.5, 2.0])
    s.add_argument("--outcome-rate", type=int, required=True, choices=[10, 25, 40])
    s.add_argument("--form", required=True, choices=["linear", "nonlinear"])
    s.add_argument("--level", required=True, choices=["moderate", "strong"])
    s.add_argument("--n", type=int, default=1500)
    s.add_argument("--reps", type=int, default=1000)
    s.add_argument("--seed", type=int, default=1)
    s.add_argument("-o", "--output", help="output JSON (default: standard output)")
    args = ap.parse_args(argv)
    if args.example_path:
        print(example_path())
        return 0
    if args.command == "fit":
        rows = fit_relative_risk(read_table(args.data), args.outcome, args.covariates, copy=not args.no_copy,
                                 copies=args.copies)
        if args.output:
            with open(args.output, "w", newline="", encoding="utf-8") as fh:
                write_rows(rows, fh)
        else:
            write_rows(rows, sys.stdout)
        return 0
    if args.command == "simulate":
        sc = scenario(args.rr, args.outcome_rate, args.form, args.level)
        res = run_scenario(sc, n=args.n, reps=args.reps, seed=args.seed)
        out = {f"{int(round(100 * r))}%": {"LB": summarize(d["lb"], sc["beta1"]), "RP": summarize(d["rp"], sc["beta1"]),
                                           "copy_used": int(d["copy"].sum())} for r, d in res.items()}
        text = json.dumps({"scenario": {k: v for k, v in sc.items()}, "n": args.n, "reps": args.reps, "seed": args.seed,
                           "results": out}, indent=1)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as fh:
                fh.write(text + "\n")
        else:
            print(text)
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())

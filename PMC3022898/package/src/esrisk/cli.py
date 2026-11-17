"""Command line.

  esrisk estimate COUNTS.csv [-o OUT.csv] [--zero-cells RULE] [--digits N]
  esrisk simulate --p-exposed P --p-unexposed P --rr RR --n1 N --n2 N [--reps R] [--seed S] [-o OUT.json]
"""

from __future__ import annotations

import argparse
import json
import math
import sys

from . import ZERO_CELL_RULES, __version__, estimate_table, evaluate, example_path, read_counts, simulate, write_rows


def _clean(obj):
    if isinstance(obj, float):
        return None if not math.isfinite(obj) else obj
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    return obj


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="esrisk", description="Exposure-specific risk from two independent samples "
                                 "(Reichmann et al. 2011): simple and revised product-based estimators and their 95% CIs.")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    ap.add_argument("--example-path", action="store_true", help="print the path of the bundled example input and exit")
    sub = ap.add_subparsers(dest="command")

    e = sub.add_parser("estimate", help="estimates and CIs for each row of a CSV of counts")
    e.add_argument("input", help="CSV with columns label, d1, n1, d2_exposed, n2_exposed, d2_unexposed, n2_unexposed")
    e.add_argument("-o", "--output", help="output CSV (default: standard output)")
    e.add_argument("--zero-cells", choices=ZERO_CELL_RULES, default="unbounded",
                   help="log CIs when sample 2 has no cases in a group (default: unbounded, the interval (0, inf))")
    e.add_argument("--digits", type=int, default=6, help="decimals in the output (default 6)")

    s = sub.add_parser("simulate", help="one setting of the paper's simulation study; prints its measures as JSON")
    s.add_argument("--p-exposed", type=float, required=True, help="exposure probability P(E)")
    s.add_argument("--p-unexposed", type=float, required=True, help="risk of disease in the unexposed P(D|not E)")
    s.add_argument("--rr", type=float, required=True, help="relative risk of disease given exposure")
    s.add_argument("--n1", type=int, required=True, help="size of sample 1 (overall risk)")
    s.add_argument("--n2", type=int, required=True, help="size of sample 2 (relative risk, exposure)")
    s.add_argument("--reps", type=int, default=1000, help="pairs of samples (default 1000)")
    s.add_argument("--population", type=int, default=10_000_000, help="population size (default 10 million)")
    s.add_argument("--seed", type=int, default=1, help="random seed (default 1)")
    s.add_argument("-o", "--output", help="output JSON (default: standard output)")

    args = ap.parse_args(argv)
    if args.example_path:
        print(example_path())
        return 0
    if args.command == "estimate":
        rows = estimate_table(read_counts(args.input), zero_cells=args.zero_cells, digits=args.digits)
        if args.output:
            with open(args.output, "w", newline="", encoding="utf-8") as f:
                write_rows(rows, f)
        else:
            write_rows(rows, sys.stdout)
        return 0
    if args.command == "simulate":
        est, *_ = simulate(args.p_exposed, args.p_unexposed, args.rr, args.n1, args.n2, args.reps,
                           args.population, rng=args.seed)
        res = _clean(evaluate(est, args.rr * args.p_unexposed))
        text = json.dumps(res, indent=1)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(text + "\n")
        else:
            print(text)
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())

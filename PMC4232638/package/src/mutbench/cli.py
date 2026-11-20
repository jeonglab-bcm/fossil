"""Command line.

  mutbench evaluate INPUT.csv [-o OUT.csv] [--boot 1000] [--seed 0]
      performance of each predictor (accuracy, sensitivity, specificity, PPV, NPV, composite) with
      bootstrap 95% intervals
  mutbench kappa INPUT.csv [-o OUT.csv]
      Cohen's kappa and its interval for every pair of predictors
  mutbench combine INPUT.csv --predictors A B C ... [--splits 1000] [--seed 0] [-o OUT.csv]
      every 'at least p of n' combination of the given predictors, mean and 95% interval over random
      two-thirds / one-third splits
  mutbench --example-path      the bundled example input

INPUT.csv: a column 'label' (non-neutral, neutral; any other value is left out of the performance) and one
column per predictor holding its categories (Driver, Passenger, Damaging, ...). Columns 'id', 'gene' and
'mutation' are carried along and not read as predictors.
"""

from __future__ import annotations

import argparse
import sys

import numpy as np

from . import (
    STATS,
    __version__,
    cohen_kappa,
    combination_calls,
    combination_name,
    combinations,
    evaluate,
    example_path,
    random_splits,
    read_calls_csv,
    split_sample,
    write_rows,
)


def _out(path):
    return open(path, "w", newline="", encoding="utf-8") if path else sys.stdout


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="mutbench", description="Benchmark mutation effect predictors against functionally labelled mutations.")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    ap.add_argument("--example-path", action="store_true", help="print the path of the bundled example input and exit")
    sub = ap.add_subparsers(dest="cmd")
    e = sub.add_parser("evaluate", help="performance of each predictor with bootstrap intervals")
    e.add_argument("input")
    e.add_argument("-o", "--output")
    e.add_argument("--boot", type=int, default=1000, help="bootstrap resamples (0: no intervals; default 1000)")
    e.add_argument("--seed", type=int, default=0)
    k = sub.add_parser("kappa", help="Cohen's kappa of every pair of predictors")
    k.add_argument("input")
    k.add_argument("-o", "--output")
    c = sub.add_parser("combine", help="'at least p of n' combinations over random splits")
    c.add_argument("input")
    c.add_argument("--predictors", nargs="+", required=True)
    c.add_argument("--splits", type=int, default=1000)
    c.add_argument("--seed", type=int, default=0)
    c.add_argument("-o", "--output")
    args = ap.parse_args(argv)

    if args.example_path:
        print(example_path())
        return 0
    if not args.cmd:
        ap.error("give a command: evaluate, kappa or combine")
    labels, calls = read_calls_csv(args.input)
    if args.cmd == "evaluate":
        rows = evaluate(labels, calls, n_boot=args.boot, seed=args.seed)
    elif args.cmd == "kappa":
        names = list(calls)
        rows = []
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                kv, lo, hi = cohen_kappa(calls[a], calls[b])
                rows.append({"predictor_a": a, "predictor_b": b, "kappa": kv, "low": lo, "high": hi})
    else:
        missing = [p for p in args.predictors if p not in calls]
        if missing:
            ap.error(f"no column for {missing}")
        keep = ~np.isnan(labels)
        y = labels[keep]
        sel = {p: calls[p][keep] for p in args.predictors}
        combos = combinations(args.predictors)
        res = split_sample(y, combination_calls(sel, combos), random_splits(len(y), args.splits, seed=args.seed))
        rows = []
        for i, (m, p) in enumerate(combos):
            row = {"combination": combination_name(m, p), "n": len(m), "p": p}
            for s in ("subset1", "subset2"):
                for st in STATS:
                    row[f"{st}_{s}"] = float(res[s][st]["mean"][i])
                    row[f"{st}_{s}_low"] = float(res[s][st]["low"][i])
                    row[f"{st}_{s}_high"] = float(res[s][st]["high"][i])
            rows.append(row)
    f = _out(args.output)
    try:
        write_rows(rows, f)
    finally:
        if args.output:
            f.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

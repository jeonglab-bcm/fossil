"""Command line: cfsenn TRAIN [TEST] [-o PREDICTIONS.csv] [--bags N] [--seed S].

Fits the ensemble on TRAIN (CSV or TSV: first column ``class``, then one column per gene) and
classifies the samples of TEST. Without TEST it reports leave-one-out cross-validation on TRAIN.
"""

from __future__ import annotations

import argparse
import csv
import sys

import numpy as np

from . import DEFAULTS, __version__, accuracy, cross_validate, example_path, read_table, run


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="cfsenn",
        description="Classify expression samples with combinational feature selection and an ensemble "
        "of neural networks (Liu et al. 2004).",
    )
    ap.add_argument("train", nargs="?", help="training table: column 'class', then one column per gene")
    ap.add_argument("test", nargs="?", help="test table with the same genes (omit for leave-one-out CV)")
    ap.add_argument("-o", "--output", help="predictions CSV (default: standard output)")
    ap.add_argument("--bags", type=int, default=DEFAULTS["n_bags"], help="bootstrap resamples (default: 100)")
    ap.add_argument("--seed", type=int, default=0, help="random seed (default: 0)")
    ap.add_argument("--example-path", action="store_true", help="print the path of the bundled example training table and exit")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = ap.parse_args(argv)

    if args.example_path:
        print(example_path())
        return 0
    if not args.train:
        ap.error("TRAIN is required")
    train = read_table(args.train)
    if args.test:
        res = run(train, read_table(args.test), n_bags=args.bags, seed=args.seed)
        rows = res["predictions"]
        acc = res["accuracy"]
    else:
        X, y, _, classes = train
        pred = cross_validate(X, y, np.arange(len(y)), n_bags=args.bags, seed=args.seed)
        rows = [{"sample": i + 1, "true": classes[t], "predicted": classes[p], "confidence": ""}
                for i, (t, p) in enumerate(zip(y, pred))]
        acc = accuracy(y, pred)
    out = open(args.output, "w", newline="", encoding="utf-8") if args.output else sys.stdout
    w = csv.DictWriter(out, fieldnames=["sample", "true", "predicted", "confidence"], lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    if args.output:
        out.close()
    print(f"{acc['correct']} of {acc['total']} correct ({acc['percent']}%)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Command line: diabclass INPUT.csv [--scheme I|II] [--kernel rbf] [--C C --gamma G] [-o OUT.csv].

Trains on the rows whose `set` column is "train" (all cases and an equal number of random
non-cases, as in the paper) and writes the decision value of every row whose `set` is "test",
with the case label when the input has one. Without --C, C and gamma come from grid.py's search.
"""

from __future__ import annotations

import argparse
import csv
import sys

import numpy as np

from . import KERNELS, SVMClassifier, __version__, auc, encode, example_path, labels, read_records


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="diabclass",
        description="SVM decision values for diabetes status from simple variables (Yu et al. 2010).",
    )
    ap.add_argument("input", nargs="?", help="CSV: one person per row, the scheme's variables, "
                    "'set' (train/test) and, for training rows, 'case' (1/0)")
    ap.add_argument("-o", "--output", help="output CSV (default: standard output)")
    ap.add_argument("--scheme", choices=["I", "II"], default="I", help="variable set (default I)")
    ap.add_argument("--kernel", choices=KERNELS, default="rbf", help="SVM kernel (default rbf)")
    ap.add_argument("--C", type=float, help="penalty C (default: grid search)")
    ap.add_argument("--gamma", type=float, help="kernel gamma (default: grid search)")
    ap.add_argument("--seed", type=int, default=0, help="seed for the balanced sample and the CV folds")
    ap.add_argument("--example-path", action="store_true",
                    help="print the path of the bundled example input and exit")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = ap.parse_args(argv)

    if args.example_path:
        print(example_path())
        return 0
    if not args.input:
        ap.error("INPUT is required")
    rows = read_records(args.input)
    train = [r for r in rows if r.get("set") == "train"]
    test = [r for r in rows if r.get("set") == "test"]
    if not train or not test:
        ap.error("INPUT needs rows with set = train and set = test")
    model = SVMClassifier(args.kernel, args.C, args.gamma, seed=args.seed)
    model.fit(encode(train, args.scheme), labels(train))
    score = model.decision_function(encode(test, args.scheme))
    has_case = all(r.get("case", "") != "" for r in test)
    f = open(args.output, "w", newline="", encoding="utf-8") if args.output else sys.stdout
    w = csv.writer(f)
    w.writerow(["id", "decision_value"] + (["case"] if has_case else []))
    for i, (r, s) in enumerate(zip(test, score)):
        w.writerow([r.get("id", i), f"{s:.10g}"] + ([r["case"]] if has_case else []))
    if args.output:
        f.close()
    msg = f"kernel {args.kernel}, C {model.C:g}, gamma {model.gamma if model.gamma else 0:g}"
    if has_case:
        msg += f", test AUC {auc(labels(test), score):.4f}"
    print(msg, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Command line: adrfusion INPUT [--feature-set SET] [--algorithm ALG] [-o SCORES.csv] [--metrics M.json]."""

from __future__ import annotations

import argparse
import csv
import json
import sys

from . import ALGORITHMS, FEATURE_SETS, __version__, cross_validated_scores, example_path, micro_metrics, read_dataset, score_table


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="adrfusion",
        description="Cross-validated ADR prediction (Liu et al. 2012): one classifier per ADR on binary drug "
                    "features; writes every (drug, ADR) score and prints the micro-averaged AUC, ACC, precision and recall.",
    )
    ap.add_argument("input", nargs="?", help="drug file in the pipe-delimited format of Liu et al. (see the README)")
    ap.add_argument("--feature-set", default="chem+bio+pheno",
                    help=f"blocks joined by '+', e.g. {', '.join(FEATURE_SETS)} (default: chem+bio+pheno)")
    ap.add_argument("--algorithm", default="svm", choices=ALGORITHMS, help="classifier (default: svm)")
    ap.add_argument("--scores", default="probability", choices=("probability", "decision"),
                    help="SVM output: Platt probability (as LIBSVM -b 1, the default) or decision value")
    ap.add_argument("--seed", type=int, default=0, help="random seed of the SVM probability fit and RF (default: 0)")
    ap.add_argument("--jobs", type=int, default=1, help="worker processes (default: 1; -1 for every core)")
    ap.add_argument("-o", "--output", help="CSV of scores: drug, adr, label, score (default: none)")
    ap.add_argument("--metrics", help="write the micro-averaged metrics as JSON to this file (default: standard output)")
    ap.add_argument("--example-path", action="store_true", help="print the path of the bundled example input and exit")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = ap.parse_args(argv)

    if args.example_path:
        print(example_path())
        return 0
    if not args.input:
        ap.error("INPUT is required")
    data = read_dataset(args.input)
    if data.folds is None:
        ap.error("the input has no fold field; add one (adrfusion.stratified_folds) and write it with write_dataset")
    S = cross_validated_scores(data, args.feature_set, args.algorithm, seed=args.seed, scores=args.scores, n_jobs=args.jobs)
    if args.output:
        with open(args.output, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["drug", "adr", "label", "score"], lineterminator="\n")
            w.writeheader()
            for r in score_table(data, S):
                w.writerow({**r, "score": repr(r["score"])})
    m = micro_metrics(data.Y, S).as_dict()
    text = json.dumps(m, indent=1)
    if args.metrics:
        with open(args.metrics, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Command line.

  prospectr-adtree train DATA.arff [--iterations 15] [--search zpure] [--tree TREE.txt] [-o SCORES.csv] [--cv 10]
  prospectr-adtree score GENES.csv [-o SCORES.csv]

train: build Weka 3.4's alternating decision tree on an ARFF file (the class is the last attribute)
       and write each row's score; --cv K writes Weka's K-fold cross-validated scores instead.
score: score genes with PROSPECTR's published tree (Adie et al. 2005, Figure 2). GENES.csv has a
       'gene' column and any of the feature columns (prospectr_adtree.FEATURES); empty = unknown.
"""

from __future__ import annotations

import argparse
import csv
import sys

from . import FEATURES, ADTree, __version__, cross_validate, evaluate, normalise, read_arff, score


def _open(path):
    return open(path, "w", newline="", encoding="utf-8") if path else sys.stdout


def cmd_train(a) -> int:
    d = read_arff(a.data)
    classes = [int(r[d.class_index]) for r in d.rows]
    if a.cv:
        rows = sorted(cross_validate(d, a.iterations, a.search, a.cv, a.seed), key=lambda r: r["index"])
        scores = [r["score"] for r in rows]
        folds = [r["fold"] for r in rows]
    else:
        model = ADTree(a.iterations, a.search).fit(d)
        scores = model.scores(d)
        folds = [-1] * len(scores)
        if a.tree:
            with open(a.tree, "w", encoding="utf-8") as f:
                f.write(model.to_weka_string() + "\n")
    ev = evaluate(classes, scores)
    names = d.class_attribute.values
    with _open(a.output) as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["row", "fold", "class", "score"])
        for i, (c, s, k) in enumerate(zip(classes, scores, folds)):
            w.writerow([i, k, names[c], repr(s)])
    print(f"accuracy {ev['pct_correct']:.2f}%  kappa {ev['kappa']:.4f}  AUC {ev['auc_disease']:.4f}", file=sys.stderr)
    return 0


def cmd_score(a) -> int:
    with open(a.genes, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows or "gene" not in rows[0]:
        raise SystemExit("GENES.csv needs a 'gene' column")
    with _open(a.output) as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["gene", "raw_score", "normalised_score"])
        for r in rows:
            g = {k: float(r[k]) for k in FEATURES if r.get(k) not in (None, "")}
            raw = score(g)
            w.writerow([r["gene"], f"{raw:.3f}", f"{normalise(raw):.6f}"])
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="prospectr-adtree", description="PROSPECTR scores and Weka 3.4 alternating decision trees.")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("train", help="build an alternating decision tree on an ARFF file")
    t.add_argument("data", help="ARFF file; the last attribute is the two-valued class")
    t.add_argument("--iterations", type=int, default=15, help="boosting iterations (Weka -B; default 15, as PROSPECTR)")
    t.add_argument("--search", default="zpure", choices=["all", "heaviest", "zpure", "random"], help="Weka -E (default zpure = -E -1)")
    t.add_argument("--cv", type=int, default=0, metavar="K", help="write K-fold cross-validated scores (Weka's folds)")
    t.add_argument("--seed", type=int, default=1, help="cross-validation seed (default 1, as Weka)")
    t.add_argument("--tree", help="write the tree as Weka prints it")
    t.add_argument("-o", "--output", help="scores CSV (default: standard output)")
    s = sub.add_parser("score", help="score genes with PROSPECTR's published tree")
    s.add_argument("genes", help="CSV with a 'gene' column and feature columns")
    s.add_argument("-o", "--output", help="scores CSV (default: standard output)")
    a = ap.parse_args(argv)
    return cmd_train(a) if a.cmd == "train" else cmd_score(a)


if __name__ == "__main__":
    sys.exit(main())

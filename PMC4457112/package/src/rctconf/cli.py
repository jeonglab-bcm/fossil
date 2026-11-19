"""Command line.

  rctconf train CITATIONS.csv -o MODEL.npz [--sets SET ...]   train on labelled citations (column rct)
  rctconf score MODEL.npz CITATIONS.csv [-o SCORES.csv]       margin and confidence of each citation
"""

from __future__ import annotations

import argparse
import sys

from . import CITATION_SETS, RCTModel, __version__, example_path, read_citations, train, write_scores
from .features import ALL_SETS


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="rctconf", description="RCT confidence of MEDLINE citations (Cohen et al. 2015).")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    ap.add_argument("--example-path", metavar="NAME", nargs="?", const="citations_train.csv",
                    help="print the path of a bundled example file and exit")
    sub = ap.add_subparsers(dest="cmd")
    t = sub.add_parser("train", help="train a model on citations with an rct column")
    t.add_argument("citations")
    t.add_argument("-o", "--output", required=True, help="model file (.npz)")
    t.add_argument("--sets", nargs="+", default=list(CITATION_SETS), choices=ALL_SETS, metavar="SET",
                   help=f"feature sets (default: the citation sets). Known: {', '.join(ALL_SETS)}")
    t.add_argument("--seed", type=int, default=0)
    s = sub.add_parser("score", help="score citations with a trained model")
    s.add_argument("model")
    s.add_argument("citations")
    s.add_argument("-o", "--output", help="output CSV (default: standard output)")
    a = ap.parse_args(argv)

    if a.example_path:
        print(example_path(a.example_path))
        return 0
    if a.cmd == "train":
        recs = read_citations(a.citations)
        if any(r.get("rct") in (None, "") for r in recs):
            ap.error("every citation needs an rct value (1 or 0) for training")
        m = train(recs, [r["rct"] for r in recs], a.sets, seed=a.seed)
        m.save(a.output)
        print(f"{a.output}: {m.n_features} features, {m.meta['n_train']} citations", file=sys.stderr)
        return 0
    if a.cmd == "score":
        m = RCTModel.load(a.model)
        recs = read_citations(a.citations)
        f = m.margins(recs)
        c = m.confidence_from_margins(f)
        rows = []
        for r, fi, ci in zip(recs, f, c):
            row = {"pmid": r["pmid"], "margin": float(fi), "confidence": float(ci)}
            if r.get("rct") not in (None, ""):
                row["rct"] = r["rct"]
            rows.append(row)
        if a.output:
            with open(a.output, "w", newline="", encoding="utf-8") as fh:
                write_scores(rows, fh)
        else:
            write_scores(rows, sys.stdout)
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())

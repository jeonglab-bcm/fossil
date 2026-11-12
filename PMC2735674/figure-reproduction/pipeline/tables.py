#!/usr/bin/env python3
"""Tables 1 to 4: leave-one-out AUC and AUPR of the twelve methods on each dataset.

Reads the score matrices written by compute_scores.py, aggregates them with the paper's
m(x, y) = max(x, y), and writes the twelve rows of each table next to the published values.

    tables.py --scores scores --out tables.json --published published_tables.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

import blmdti as B

DATASETS = {"e": "Table 1", "ic": "Table 2", "gpcr": "Table 3", "nr": "Table 4"}
#: The twelve rows of every table, in the paper's order, each as the scores it aggregates.
ROWS = [
    ("KRMd", ("krmd",)),
    ("BLMd", ("blmd",)),
    ("m(KRMd,BLMd)", ("krmd", "blmd")),
    ("KRMt", ("krmt",)),
    ("BLMt", ("blmt",)),
    ("m(KRMt,BLMt)", ("krmt", "blmt")),
    ("m(KRMd,KRMt)", ("krmd", "krmt")),
    ("m(BLMd,BLMt)", ("blmd", "blmt")),
    ("m(KRMd,KRMt,BLMd,BLMt)", ("krmd", "krmt", "blmd", "blmt")),
    ("NNd", ("nnd",)),
    ("NNt", ("nnt",)),
    ("m(NNd,NNt)", ("nnd", "nnt")),
]
#: Rows whose AUC the paper copies from Yamanishi et al. (2008) rather than recomputing: the
#: starred values of its Tables 1 to 4. Their AUPR is the paper's own.
COPIED_AUC = {"KRMd", "KRMt"}


def load_scores(folder: Path, dataset: str) -> tuple[np.ndarray, dict]:
    scores = {}
    adjacency = None
    for method in ("krmd", "krmt", "blmd", "blmt", "nnd", "nnt"):
        path = folder / f"{dataset}_{method}.npz"
        if not path.is_file():
            raise SystemExit(f"missing {path}")
        with np.load(path, allow_pickle=False) as f:
            scores[method] = f["scores"]
            if adjacency is None:
                adjacency = f["adjacency"]
            elif not np.array_equal(adjacency, f["adjacency"]):
                raise SystemExit(f"{path}: a different network from the other methods")
        unscored = int(np.isnan(scores[method]).sum())
        if unscored:
            raise SystemExit(f"{path}: {unscored} pairs have no score")
    return adjacency, scores


def table(dataset: str, adjacency: np.ndarray, scores: dict, aupr_rule: str, standardize: bool) -> list[dict]:
    labels = B.interactions(adjacency)
    rows = []
    for name, parts in ROWS:
        combined = B.aggregate(*[scores[p] for p in parts], standardize=standardize and len(parts) > 1)
        rows.append(
            {
                "method": name,
                "auc": round(100.0 * B.auc(labels, combined), 1),
                "aupr": round(100.0 * B.aupr(labels, combined, rule=aupr_rule), 1),
                "auc_copied_from_yamanishi_2008": name in COPIED_AUC,
            }
        )
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scores", type=Path, required=True)
    ap.add_argument("--published", type=Path, required=True, help="the paper's printed values")
    ap.add_argument("--aupr-rule", default="trapezoid", choices=("trapezoid", "step"))
    ap.add_argument(
        "--plain-max",
        action="store_true",
        help="aggregate with max of the raw scores instead of max of the z-scores",
    )
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    published = json.loads(args.published.read_text())
    standardize = not args.plain_max
    out = {"aupr_rule": args.aupr_rule, "standardize_before_max": standardize, "tables": {}}
    for dataset, title in DATASETS.items():
        adjacency, scores = load_scores(args.scores, dataset)
        rows = table(dataset, adjacency, scores, args.aupr_rule, standardize)
        for row in rows:
            printed = published[dataset][row["method"]]
            row["published_auc"] = printed["auc"]
            row["published_aupr"] = printed["aupr"]
            row["auc_difference"] = round(row["auc"] - float(printed["auc"]), 1)
            row["aupr_difference"] = round(row["aupr"] - float(printed["aupr"]), 1)
        out["tables"][dataset] = {
            "title": title,
            "drugs": int(adjacency.shape[0]),
            "targets": int(adjacency.shape[1]),
            "interactions": int(adjacency.sum()),
            "rows": rows,
        }
        print(f"{title} ({dataset}):", flush=True)
        for row in rows:
            print(
                f"  {row['method']:24s} AUC {row['auc']:5.1f} (paper {row['published_auc']:>5s},"
                f" {row['auc_difference']:+.1f})  AUPR {row['aupr']:5.1f}"
                f" (paper {row['published_aupr']:>5s}, {row['aupr_difference']:+.1f})",
                flush=True,
            )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

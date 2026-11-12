"""Consensus Random Forest of Fig. 2a (Sec. 2.2 and 3.4).

    consensus.py DATA_DIR WEKA_JAR consensus.json [--java java] [--folds 10] [--seed 1]

The paper: "a consensus method that incorporates all 13 tested methods into a Random Forest
classifier (Breiman, 2001; Witten and Frank, 1999). For each tested gene-disease pair, a 13D vector
was created with entries containing each method's score for the pair ... we required a minimum
yes probability of theta, which we varied from 0.5 (default) to 0.9." It cites Weka and states
nothing else. We use Weka's RandomForest with its defaults (10 trees, log2(13) + 1 = 4 features per
split, seed 1) and 10-fold stratified cross-validation (our split, numpy seed 1), so each pair is scored by a forest
that did not see it. The 13 features are the scores of Neighborhood, Oti1-3 (1 when the method
predicts the pair), GS1-3, GS-All (the largest of the GS1-3 scores), MCL, VI-CutL, VI-CutS, Prop
and RW, from the HPRD prediction files (our rerun equals them for Neighborhood, Oti, MCL, Prop and
RW).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np

import diseasenet as dn

FEATURES = ["Neighborhood", "Oti1", "Oti2", "Oti3", "GS1", "GS2", "GS3", "GS-All", "MCL", "VI-CutL", "VI-CutS", "Prop", "RW"]
THETAS = [0.5, 0.6, 0.7, 0.8, 0.9]


def feature_matrix(data: Path):
    preds = data / "preds"
    cands = dn.read_candidates(preds / "locus_disease_preds-HPRD-LOC")
    raw = {}
    for f in ("neighborhood", "oti", "gs", "mcl", "vicut", "prop", "rw"):
        raw.update(dn.read_scores(preds / f"{f}_preds-HPRD-LOC"))
    keys = list(zip(cands.genes, cands.diseases))
    col = {m: np.array([s[k] for k in keys]) for m, s in raw.items()}
    x = np.column_stack(
        [
            col["Neighborhood"],
            (col["Oti"] >= 1).astype(float),
            (col["Oti"] >= 2).astype(float),
            (col["Oti"] >= 3).astype(float),
            col["GS1"],
            col["GS2"],
            col["GS3"],
            np.maximum(np.maximum(col["GS1"], col["GS2"]), col["GS3"]),
            col["MCL"],
            col["VI-CutH"],
            col["VI-CutL"],
            col["Prop"],
            col["RW"],
        ]
    )
    return cands, x


def write_arff(path: Path, x: np.ndarray, y: np.ndarray):
    with open(path, "w") as f:
        f.write("@relation consensus\n")
        for name in FEATURES:
            f.write(f"@attribute '{name}' numeric\n")
        f.write("@attribute class {yes,no}\n@data\n")
        for row, lab in zip(x, y):
            f.write(",".join(repr(float(v)) for v in row) + ("," + ("yes" if lab else "no")) + "\n")


def parse_predictions(text: str, n: int) -> np.ndarray:
    """Yes-probability of each instance from Weka's `-p 0 -distribution` output."""
    prob = np.full(n, np.nan)
    started = False
    for line in text.splitlines():
        parts = line.split()
        if not started:
            if parts[:1] == ["inst#"]:
                started = True
            continue
        if not parts:
            continue
        idx = int(parts[0]) - 1
        dist = parts[-1].replace("*", "").split(",")
        prob[idx] = float(dist[0])
    return prob


def folds_of(y: np.ndarray, k: int, seed: int) -> np.ndarray:
    """Stratified fold number of each pair: within each class, a seeded permutation dealt in turn."""
    rng = np.random.default_rng(seed)
    fold = np.empty(len(y), dtype=int)
    for cls in (True, False):
        idx = np.flatnonzero(y == cls)
        idx = idx[rng.permutation(len(idx))]
        fold[idx] = np.arange(len(idx)) % k
    return fold


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data", type=Path)
    ap.add_argument("weka", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--java", default="java")
    ap.add_argument("--folds", type=int, default=10)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--trees", type=int, default=10)
    args = ap.parse_args()

    cands, x = feature_matrix(args.data)
    y = cands.known
    fold = folds_of(y, args.folds, args.seed)
    prob = np.full(len(y), np.nan)
    with tempfile.TemporaryDirectory() as tmp:
        for k in range(args.folds):
            tr, te = fold != k, fold == k
            a_tr, a_te = Path(tmp) / f"train{k}.arff", Path(tmp) / f"test{k}.arff"
            write_arff(a_tr, x[tr], y[tr])
            write_arff(a_te, x[te], y[te])
            cmd = [
                args.java, "-Xmx6g", "-cp", str(args.weka), "weka.classifiers.trees.RandomForest",
                "-I", str(args.trees), "-K", "0", "-S", str(args.seed),
                "-t", str(a_tr), "-T", str(a_te), "-p", "0", "-distribution",
            ]
            out = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
            prob[np.flatnonzero(te)] = parse_predictions(out, int(te.sum()))
    if np.isnan(prob).any():
        raise RuntimeError("missing Weka predictions")
    res = {
        "weka": args.weka.name,
        "settings": {
            "trees": args.trees,
            "features_per_split": "log2(13) + 1 = 4 (Weka default -K 0)",
            "forest_seed": args.seed,
            "cross_validation": f"{args.folds} stratified folds, numpy seed {args.seed}",
        },
        "points": [],
        "points_strict": [],
    }
    for t in THETAS:
        for key, pred in (("points", prob >= t), ("points_strict", prob > t)):
            p, r, n = dn.precision_recall(pred, y)
            res[key].append({"theta": t, "precision": p, "recall": r, "n": n})
    args.out.write_text(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

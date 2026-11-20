"""Cross-validated scores of every (drug, ADR) pair, for each model the paper reports.

Usage: run_models.py DATA_DIR OUT_DIR MODEL [MODEL ...] [--jobs N] [--seed S]

DATA_DIR holds random_group_cv_data.indication and ade_feature_list (fetch_inputs.sh). A MODEL is
ALGORITHM:FEATURE_SET[:paper] (":paper" weights the classes by 1 - their share, as in the paper's
further analysis), e.g. svm:chem, rf:chem+bio+pheno:paper. Every model runs on the folds of Liu et al.'s
file (each drug's fold for each ADR), through the package adrfusion. Writes OUT_DIR/<model>.npy
(drugs x ADRs, float64; not committed) with the model name's ':' and '+' kept.
"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np

import adrfusion as A


def load(data_dir):
    cuis = [l.split("|")[0] for l in (Path(data_dir) / "ade_feature_list").read_text().splitlines() if l]
    return A.read_dataset(Path(data_dir) / "random_group_cv_data.indication", cuis)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("out")
    ap.add_argument("models", nargs="+")
    ap.add_argument("--jobs", type=int, default=-1)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    data = load(a.data)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    D = A.block_distances(data)
    for m in a.models:
        alg, fs, *w = m.split(":")
        t = time.time()
        S = A.cross_validated_scores(data, fs, alg, seed=a.seed, n_jobs=a.jobs,
                                     class_weight="paper" if w == ["paper"] else None, distances=D)
        np.save(out / f"{m}.npy", S)
        print(f"{m}: {time.time() - t:.0f} s", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()

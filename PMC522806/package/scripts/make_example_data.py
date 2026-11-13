#!/usr/bin/env python3
"""Write the bundled example input and its expected output.

The input is synthetic two-class expression data: 500 genes, 40 training and 20 test samples,
half of each class. Genes 1-30 are informative in three co-expressed blocks of 10 (a shared
block factor plus noise); in class "tumor" their log-scale mean is shifted by +1.5 (block 1),
-1.5 (block 2) and +1.0 (block 3) standard deviations. The other 470 genes are noise. Values are
exp(log-scale value) * 100, like intensities.

The expected output is the class each test sample was drawn from: it comes from the generator,
not from the package, so the package's tests check it against something independent.

Run from the package folder: python3 scripts/make_example_data.py
"""

import csv
from pathlib import Path

import numpy as np

DATA = Path(__file__).resolve().parent.parent / "src" / "cfsenn" / "data"
GENES = 500
SHIFT = {0: 1.5, 1: -1.5, 2: 1.0}  # block -> shift in SD units for class "tumor"


def draw(n_per_class, rng):
    labels = ["normal"] * n_per_class + ["tumor"] * n_per_class
    X = rng.normal(0.0, 1.0, (2 * n_per_class, GENES))
    for b in range(3):
        factor = rng.normal(0.0, 1.0, (2 * n_per_class, 1))
        cols = slice(10 * b, 10 * b + 10)
        X[:, cols] = 0.6 * factor + 0.8 * X[:, cols]
        X[n_per_class:, cols] += SHIFT[b]
    return labels, np.round(np.exp(0.5 * X + 5.0), 2)


def write(path, labels, X):
    with open(path, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["class"] + [f"g{i + 1}" for i in range(GENES)])
        for lab, row in zip(labels, X):
            w.writerow([lab] + [f"{v:.2f}" for v in row])


def main():
    rng = np.random.default_rng(522806)
    ytr, Xtr = draw(20, rng)
    yte, Xte = draw(10, rng)
    write(DATA / "example_train.csv", ytr, Xtr)
    write(DATA / "example_test.csv", yte, Xte)
    with open(DATA / "example_test_expected.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["sample", "class"])
        for i, lab in enumerate(yte):
            w.writerow([i + 1, lab])


if __name__ == "__main__":
    main()

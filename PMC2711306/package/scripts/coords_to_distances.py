"""Pairwise distances of the authors' coordinates (row r is protein P{r:03d}) as CSV."""
import sys

import numpy as np

X = np.loadtxt(sys.argv[1], delimiter=",", ndmin=2)
n = X.shape[0]
with open(sys.argv[2], "w") as f:
    f.write("protein_a,protein_b,distance\n")
    for i in range(n):
        for j in range(i + 1, n):
            f.write(f"P{i + 1:03d},P{j + 1:03d},{np.sqrt(((X[i] - X[j]) ** 2).sum()):.6f}\n")

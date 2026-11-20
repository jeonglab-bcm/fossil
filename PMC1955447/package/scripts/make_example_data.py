"""Write the bundled example input: one data set of the paper's design (Moineddin et al. 2007, Methods), drawn
with plain NumPy (not with mlagq), 40 groups of 25, random-intercept variance 0.67 (ICC 0.17), random-slope
variance 1, gamma = (-1.0, 0.3, 0.3, 0.3).

Usage: python scripts/make_example_data.py   (writes src/mlagq/data/clustered_binary.csv)
"""
from pathlib import Path

import numpy as np

rng = np.random.default_rng(20070716)          # the paper's publication date
J, n = 40, 25
z = rng.standard_normal(J)
u0 = rng.standard_normal(J) * np.sqrt(0.67)
u1 = rng.standard_normal(J)
x = rng.standard_normal((J, n))
eta = -1.0 + 0.3 * z[:, None] + (0.3 + 0.3 * z[:, None]) * x + u0[:, None] + u1[:, None] * x
y = (rng.random((J, n)) < 1 / (1 + np.exp(-eta))).astype(int)
out = Path(__file__).resolve().parents[1] / "src" / "mlagq" / "data" / "clustered_binary.csv"
with open(out, "w") as f:
    f.write("group,z,x,y\n")
    for j in range(J):
        for i in range(n):
            f.write(f"g{j + 1:02d},{z[j]:.6f},{x[j, i]:.6f},{y[j, i]}\n")
print(f"wrote {out}: {J * n} rows, prevalence {y.mean():.3f}")

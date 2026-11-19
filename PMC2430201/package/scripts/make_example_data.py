"""Write src/rommeta/data/trials.csv: one synthetic meta-analysis of 8 trials of a continuous outcome.

Control means near 100 (SD 40% of the mean), a true ratio of means of 1.2, heterogeneity of 0.5 SD
added to each arm's mean as in the paper's design, unequal trial sizes; means and SDs rounded to 0.1 as a
report would print them. Run once; the expected output (trials_expected.csv) comes from
scripts/metafor_expected.R, not from this package.
"""
import csv
from pathlib import Path

import numpy as np

rng = np.random.default_rng(20080521)
sizes = [(12, 12), (15, 14), (20, 21), (24, 25), (30, 30), (41, 39), (55, 52), (80, 78)]
out = Path(__file__).resolve().parents[1] / "src" / "rommeta" / "data" / "trials.csv"
rows = []
for i, (ne, nc) in enumerate(sizes, 1):
    u = rng.normal(0, 0.5 / np.sqrt(2) * 40, 2)
    xe = rng.normal(120 + u[0], 40, ne)
    xc = rng.normal(100 + u[1], 40, nc)
    rows.append({"study": f"Trial {i}", "mean_exp": f"{xe.mean():.1f}", "sd_exp": f"{xe.std(ddof=1):.1f}", "n_exp": ne,
                 "mean_contr": f"{xc.mean():.1f}", "sd_contr": f"{xc.std(ddof=1):.1f}", "n_contr": nc})
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
print(out)

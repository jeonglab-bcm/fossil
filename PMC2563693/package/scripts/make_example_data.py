"""Write the bundled example: a synthetic two-class expression set, four gene sets, and the
expected CORGs computed here, independently of the package.

  python scripts/make_example_data.py

Design: 40 samples (20 "case", 20 "control"), 120 genes G001-G120 with standard normal noise
(seed 2008). Planted shifts in the case samples (in noise standard deviations):
  SET_UP     12 genes; G001, G002, G003 up by 1.6, 1.2 and 0.9
  SET_DOWN   10 genes; G021, G022 down by 1.4 and 1.0
  SET_MIXED  15 genes; G041 up by 1.3, G042 down by 1.3
  SET_NULL    8 genes; no shift
Values are 8 + 0.5 x (noise + shift), rounded to three decimals, as on a log2 scale.

The expected output is computed with scipy.stats.ttest_ind and plain loops written for this
script, not with pacorg: z-score each gene over all samples, rank a set's members by t
(descending when their mean t is positive), and add genes while the |t| of the combined z-score
(sum over sqrt(k)) increases.
"""

import csv
import math
from pathlib import Path

import numpy as np
from scipy.stats import ttest_ind

OUT = Path(__file__).resolve().parents[1] / "src" / "pacorg" / "data"
SETS = {
    "SET_UP": [f"G{i:03d}" for i in range(1, 13)],
    "SET_DOWN": [f"G{i:03d}" for i in range(21, 31)],
    "SET_MIXED": [f"G{i:03d}" for i in range(41, 56)],
    "SET_NULL": [f"G{i:03d}" for i in range(101, 109)],
}
SHIFT = {"G001": 1.6, "G002": 1.2, "G003": 0.9, "G021": -1.4, "G022": -1.0, "G041": 1.3, "G042": -1.3}


def main():
    rng = np.random.default_rng(2008)
    genes = [f"G{i:03d}" for i in range(1, 121)]
    labels = ["case"] * 20 + ["control"] * 20
    case = np.array([l == "case" for l in labels])
    X = rng.standard_normal((len(genes), len(labels)))
    for g, s in SHIFT.items():
        X[genes.index(g), case] += s
    X = np.round(8 + 0.5 * X, 3)

    with open(OUT / "example.gct", "w", encoding="utf-8") as f:
        f.write("#1.2\n%d\t%d\n" % X.shape)
        f.write("NAME\tDESCRIPTION\t" + "\t".join(f"S{j + 1:02d}" for j in range(len(labels))) + "\n")
        for g, row in zip(genes, X):
            f.write(g + "\tna\t" + "\t".join(f"{v:.3f}" for v in row) + "\n")
    with open(OUT / "example.cls", "w", encoding="utf-8") as f:
        f.write(f"{len(labels)} 2 1\n# case control\n" + " ".join(labels) + "\n")
    with open(OUT / "example.gmt", "w", encoding="utf-8") as f:
        for name, members in SETS.items():
            f.write(name + "\tsynthetic\t" + "\t".join(members) + "\n")

    # Expected output, independently of pacorg. Labels sort as ["case", "control"], so the
    # package's case class (the second in sorted order) is "control": t = control - case.
    X = np.loadtxt(OUT / "example.gct", skiprows=3, usecols=range(2, 42), delimiter="\t")
    Z = np.array([(r - r.mean()) / r.std(ddof=1) for r in X])
    pos = ~case

    def t(v):
        return ttest_ind(v[pos], v[~pos]).statistic

    rows = []
    for name, members in SETS.items():
        idx = [genes.index(g) for g in members]
        ts = [t(Z[i]) for i in idx]
        order = sorted(range(len(idx)), key=lambda k: -ts[k] if np.mean(ts) > 0 else ts[k])
        chosen = [idx[order[0]]]
        best = abs(t(Z[chosen[0]]))
        for k in order[1:]:
            trial = chosen + [idx[k]]
            score = abs(t(sum(Z[i] for i in trial) / math.sqrt(len(trial))))
            if score > best:
                chosen, best = trial, score
            else:
                break
        tian = sum(ts) / math.sqrt(len(ts))
        act = sum(Z[i] for i in chosen) / math.sqrt(len(chosen))
        rows.append([name, len(members), len(idx), len(chosen), " ".join(genes[i] for i in chosen),
                     repr(float(tian)), repr(float(t(act)))])
    with open(OUT / "example_expected.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["pathway", "members", "measured", "n_corgs", "corgs", "tian", "score"])
        w.writerows(rows)
    for r in rows:
        print(r[0], r[4], r[6][:6])


if __name__ == "__main__":
    main()

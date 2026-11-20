"""How far Table 2 moves with the seed of LIBSVM's probability fit (-b 1 runs an internal 5-fold CV on a
random split to fit Platt's sigmoid; the paper's seed and platform are unknown).

Usage: seed_spread.py DATA_DIR PUBLISHED_VALUES.json OUT.json SEED_DIR [SEED_DIR ...]

Each SEED_DIR holds svm:<set>.npy for the six feature sets, from run_models.py --seed N. Writes, for each
printed cell of Table 2, our value at every seed, the range, and whether the paper's value lies inside
the range widened by half a printed unit.
"""
import json
import sys
from pathlib import Path

import numpy as np

import adrfusion as A

from run_models import load

SETS = ["chem", "bio", "pheno", "chem+bio", "chem+pheno", "chem+bio+pheno"]


def main():
    data_dir, pubf, out, *dirs = sys.argv[1:]
    data = load(data_dir)
    Y = data.Y
    sub = Y.sum(0) > 50
    pub = json.load(open(pubf))["table2"]
    cells = []
    for fs in SETS:
        vals = {"all": [], "50+": []}
        for d in dirs:
            S = np.load(Path(d) / f"svm:{fs}.npy")
            vals["all"].append(A.micro_metrics(Y, S).as_dict())
            vals["50+"].append(A.micro_metrics(Y[:, sub], S[:, sub]).as_dict())
        for part in ("all", "50+"):
            for k in ("auc", "acc", "precision", "recall"):
                v = [round(x[k], 10) for x in vals[part]]
                e = pub[fs][part][k]
                half = 0.5 * 10 ** -len(e.split(".")[1])
                cells.append({"name": f"{fs}|{part}|{k}", "expected": e, "seeds": v, "min": min(v), "max": max(v),
                              "range": round(max(v) - min(v), 10),
                              "paper_inside": bool(min(v) - half <= float(e) <= max(v) + half)})
    inside = sum(c["paper_inside"] for c in cells)
    summary = {"seeds": len(dirs), "cells": len(cells), "paper_inside": inside,
               "max_range": {k: max(c["range"] for c in cells if c["name"].endswith(k)) for k in ("auc", "acc", "precision", "recall")}}
    json.dump({"summary": summary, "cells": cells}, open(out, "w"), indent=1)
    print(f"seed spread: the paper's value lies in our range for {inside} of {len(cells)} cells", file=sys.stderr)


if __name__ == "__main__":
    main()

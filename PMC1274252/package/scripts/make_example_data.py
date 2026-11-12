#!/usr/bin/env python3
"""Write the bundled example input: a synthetic two-class ARFF file shaped like PROSPECTR's.

200 genes with five features (gene length, exons, mouse identity, signal peptide, 3' UTR length),
some values missing, classes drawn from a logistic model of the features. The expected outputs
(example_train_weka_tree.txt, example_train_weka_scores.tsv, example_train_weka_cv.tsv) come from
Weka 3.4.3 itself (figure-reproduction/pipeline/WekaRun.java), not from this package.

Run from the package folder: python3 scripts/make_example_data.py
"""

import math
import random
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "src" / "prospectr_adtree" / "data"


def main():
    rnd = random.Random(20051)
    rows = []
    for _ in range(200):
        gl = round(math.exp(rnd.gauss(10, 1.2)))
        ex = max(1, int(rnd.expovariate(1 / 9)))
        mi = 0 if rnd.random() < 0.15 else round(rnd.uniform(40, 100), 1)
        sp = 1 if rnd.random() < 0.25 else 0
        u3 = None if rnd.random() < 0.1 else round(rnd.expovariate(1 / 700))
        z = 0.6 * (math.log(gl) - 10) + 0.04 * (ex - 9) + 0.02 * (mi - 60) + 0.9 * sp + rnd.gauss(0, 1)
        cls = "disease" if z > 0 else "normal"
        rows.append((gl, ex, mi, sp, u3, cls))
    with open(DATA / "example_train.arff", "w", newline="\n") as f:
        f.write("% Synthetic example for prospectr_adtree (scripts/make_example_data.py); not real genes\n")
        f.write("@relation example\n@attribute gene_length numeric\n@attribute exons numeric\n")
        f.write("@attribute mouse_identity numeric\n@attribute sigpep {0,1}\n@attribute len_3utr numeric\n")
        f.write("@attribute phenotype {disease,normal}\n@data\n")
        for gl, ex, mi, sp, u3, cls in rows:
            f.write(f"{gl},{ex},{mi:g},{sp},{'?' if u3 is None else u3},{cls}\n")


if __name__ == "__main__":
    main()

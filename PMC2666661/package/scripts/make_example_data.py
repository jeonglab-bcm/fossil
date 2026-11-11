"""Write the bundled example input: one simulated case-control data set (Meng et al. 2009, model
H4M4, design K4S4, LD model r1): 250 cases and 250 controls, 4 risk SNPs, 96 noise SNPs and one
perfect LD proxy for each risk SNP (104 SNPs).

  python scripts/make_example_data.py src/rfld/data/h4m4_r1.csv

Columns: status (1 case, 0 control), then snp1..snp104 (number of risk alleles 0, 1, 2).
snp1-snp4 are the risk SNPs and snp101-snp104 their proxies (copies of snp1-snp4).
"""
import csv
import sys

import numpy as np

from rfld.simulate import MODELS, snp_dataset

X, y, kinds = snp_dataset(np.random.default_rng(20090305), MODELS["H4M4"], "r1")
with open(sys.argv[1], "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["status"] + [f"snp{j + 1}" for j in range(X.shape[1])])
    for yi, row in zip(y, X):
        w.writerow([int(yi)] + [int(v) for v in row])

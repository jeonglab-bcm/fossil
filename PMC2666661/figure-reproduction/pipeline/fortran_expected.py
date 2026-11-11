"""Expected output of the package's example: Breiman and Cutler's Fortran Random Forests 5.1 on the
example data (RF0, unmodified; RF1, prog.f with our patch of the revised tree builder), mean and SD
over 5 seeds of 5000 trees each. Run with the port check; the result is committed as
package/src/rfld/data/h4m4_r1_expected.csv.

  fortran_expected.py PROG_F EXAMPLE.csv OUT.csv [--workdir DIR]
"""
import argparse
import csv
import os

import numpy as np

from port_check import build, run_fortran
from rfld.forest import r2_matrix

ap = argparse.ArgumentParser()
ap.add_argument("prog")
ap.add_argument("example")
ap.add_argument("out")
ap.add_argument("--workdir", default="fortran_expected_work")
a = ap.parse_args()
a.workdir = os.path.abspath(a.workdir)
os.makedirs(a.workdir, exist_ok=True)
rows = list(csv.reader(open(a.example)))
names = rows[0][1:]
data = np.array(rows[1:], dtype=int)
y, X = data[:, 0], data[:, 1:]
ld = r2_matrix(X) > 0.5
res = {}
for rf1 in (False, True):
    ims, ims1, tvs = [], [], []
    for seed in (101, 202, 303, 404, 505):
        exe = build(a.prog, a.workdir, X.shape[1], seed, rf1)
        im, tv = run_fortran(exe, X, y, ld, os.path.join(a.workdir, f"run_{int(rf1)}_{seed}"))
        ims.append(im)
        tvs.append(tv)
        ims1.append(np.where(tv > 0, im * 5000 / np.maximum(tv, 1), 0.0))
    key = "rf1" if rf1 else "rf0"
    res[key] = (np.mean(ims, 0), np.std(ims, 0, ddof=1), np.mean(ims1, 0), np.std(ims1, 0, ddof=1), np.mean(tvs, 0))
with open(a.out, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["snp", "rf0_im0", "rf0_im0_sd", "rf0_im1", "rf0_im1_sd", "rf0_trees",
                "rf1_im0", "rf1_im0_sd", "rf1_im1", "rf1_im1_sd", "rf1_trees"])
    for j, n in enumerate(names):
        r0, r1 = res["rf0"], res["rf1"]
        w.writerow([n] + [f"{r0[i][j]:.4f}" for i in range(4)] + [f"{r0[4][j]:.1f}"]
                   + [f"{r1[i][j]:.4f}" for i in range(4)] + [f"{r1[4][j]:.1f}"])
print("wrote", a.out)

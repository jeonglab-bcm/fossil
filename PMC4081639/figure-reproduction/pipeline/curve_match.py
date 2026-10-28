import sys, json
import numpy as np
from scipy import ndimage
sys.path.insert(0, ".")
from fit_render import fit, paper, SPEC
P = paper("2"); x0, x1, y0, y1 = SPEC["2"]["box"]
for f2 in ("fig2_data_native.csv", "fig2_data.csv"):  # this platform's R, then x86 arithmetic
    r, al = fit("2", "cm", 166, {"f2": f2})
    A = al[y0+3:y1-3, x0+3:x1-3] < 120; B = P[y0+3:y1-3, x0+3:x1-3] < 120
    Ad = ndimage.binary_dilation(A, iterations=1); Bd = ndimage.binary_dilation(B, iterations=1)
    print(f2, "paper curve px covered by ours: %.3f   ours covered by paper: %.3f" % ((B & Ad).sum() / B.sum(), (A & Bd).sum() / A.sum()))

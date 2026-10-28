import sys, json
import numpy as np
from scipy import ndimage
sys.path.insert(0, ".")
from fit_render import fit, paper, SPEC
P = paper("6"); x0, x1, y0, y1 = SPEC["6"]["box"]
M = np.ones(P.shape, bool); M[y0 - 2:y1 + 3, x0 - 2:x1 + 3] = False
M[:, :x0 - 30] = False   # exclude y-title column (position is tuned separately)
yl = json.load(open("fig6_scale.json"))["ylim"]
base = {"ytitle_size": 12.7, "ytitle_gap": 2.15, "ytitle_hjust": 0.48, "title_gap": 3.1, "xtext_gap": 7.05, "xtext_vjust": 0.9375, "f6": "fig6_data_scaled.csv", "ylim": yl}
for dpi in map(int, sys.argv[1].split(",")):
    r, al = fit("6", "cm", dpi, base)
    A = (al < 170) & M; B = (P < 170) & M
    dA = ndimage.distance_transform_edt(~A); dB = ndimage.distance_transform_edt(~B)
    print(dpi, "chamfer %.3f" % ((dB[A].mean() + dA[B].mean()) / 2), "shift", r["shift"], flush=True)

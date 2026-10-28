import sys, json
import numpy as np
from scipy import ndimage
sys.path.insert(0, ".")
from fit_render import fit, paper, SPEC
def chamfer(al, P, box):
    x0, x1, y0, y1 = box
    m = np.ones(P.shape, bool); m[y0 - 2:y1 + 3, x0 - 2:x1 + 3] = False
    A = (al < 170) & m; B = (P < 170) & m
    dA = ndimage.distance_transform_edt(~A); dB = ndimage.distance_transform_edt(~B)
    return float((dB[A].mean() + dA[B].mean()) / 2)
fig = sys.argv[1]; dpis = [int(v) for v in sys.argv[2].split(",")]
res = []
for font in ("cm", "times"):
    for dpi in dpis:
        r, al = fit(fig, font, dpi)
        r["chamfer"] = chamfer(al, paper(fig), SPEC[fig]["box"]); r["font"] = font
        print(fig, font, dpi, "shift", r["shift"], "chamfer %.3f" % r["chamfer"], flush=True)
        res.append(r)
best = min(res, key=lambda r: r["chamfer"])
print("BEST", json.dumps(best, default=int))

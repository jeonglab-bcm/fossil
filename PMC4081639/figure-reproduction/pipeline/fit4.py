import sys, json
import numpy as np
from scipy import ndimage
sys.path.insert(0, ".")
from fit_render import fit, paper, SPEC
from offsets import runs
def text_mask(P, fig):
    x0, x1, y0, y1 = SPEC[fig]["box"]; D = P < 170; M = np.zeros(P.shape, bool)
    rl = runs(D[:, :x0 - 1].sum(0))
    if fig in ("2", "4"):
        lab = rl[1] if len(rl) >= 3 else rl[-1]; M[y0 - 8:y1 + 9, lab[0]:lab[1] + 1] = True
    rb = runs(D[y1 + 2:, :].sum(1)); xt = rb[1] if len(rb) >= 3 else rb[-1]
    M[y1 + 2 + xt[0]:y1 + 3 + xt[1], x0 - 25:] = True
    if fig in ("4", "5"): M[:, x1 + 3:] = True
    if fig == "6": M[y0 - 25:y0 - 1, x0:x1] = True
    return M
def chamfer(al, P, M):
    A = (al < 170) & M; B = (P < 170) & M
    dA = ndimage.distance_transform_edt(~A); dB = ndimage.distance_transform_edt(~B)
    return float((dB[A].mean() + dA[B].mean()) / 2)
fig, dpis, ratios = sys.argv[1], [int(v) for v in sys.argv[2].split(",")], [float(v) for v in sys.argv[3].split(",")]
P = paper(fig); M = text_mask(P, fig); res = []
for dpi in dpis:
    for q in ratios:
        r, al = fit(fig, "cm", dpi, None, None, round(dpi * q))
        c = chamfer(al, P, M); res.append((c, dpi, round(dpi * q)))
        print(fig, dpi, round(dpi * q), "chamfer %.3f" % c, flush=True)
print("BEST", fig, min(res))

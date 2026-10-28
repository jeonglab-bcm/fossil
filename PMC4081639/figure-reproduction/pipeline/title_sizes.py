import sys, json
import numpy as np
sys.path.insert(0, ".")
from fit_render import fit, paper, SPEC
from offsets import runs
def ytitle_extent(a, x0):
    D = a < 170; rl = runs(D[:, :x0 - 1].sum(0)); c0, c1 = rl[0]
    rows = np.where(D[:, c0:c1 + 1].any(1))[0]
    return rows.max() - rows.min() + 1, c1 - c0 + 1
cfgs = {"2": (166, {}), "4": (125, {}), "5": (116, {}), "6": (120, {})}
for fig, (dpi, extra) in cfgs.items():
    P = paper(fig); x0 = SPEC[fig]["box"][0]
    r, al = fit(fig, "cm", dpi, extra)
    ours_raw = ytitle_extent(al, x0 + 0)
    pp = ytitle_extent(P, x0)
    print(f"fig {fig}: paper y-title length {pp[0]}px x {pp[1]}px; ours@12pt {ours_raw[0]}px x {ours_raw[1]}px -> paper size ~ {12 * pp[0] / ours_raw[0]:.2f}pt", flush=True)

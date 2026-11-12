"""Read the published Figure 5 bar heights.

usage: figure5_read.py PUBLISHED_PNG OUT_JSON

Four panels, each with x = distance 0..150 and y = discriminant weight -52..21. The pixel map is
fitted to the tick marks of each panel (y: 20 to -50 in steps of 10; x: 20 to 140 in steps of 20;
nothing inside the plot is fitted). For each distance d the bar is the dark run that touches the
zero row in the columns within 0.8 px of x(d) (bars are 2 px wide at a 3.46 px pitch); its far end gives the value (one pixel is about
0.17 in weight). Bars shorter than a pixel read as 0. Distance 0 lies on the left axis line;
it is read from the columns just right of the line.
"""
import json
import sys

import numpy as np
from PIL import Image

PANELS = {
    "A": {"box": (79, 598, 46, 470), "title": "Top-1-gram pair (G,G) of SVM-DT"},
    "B": {"box": (678, 1198, 46, 470), "title": "Top-1-gram pair (L,L) of SVM-DT"},
    "C": {"box": (79, 598, 584, 1008), "title": "Residue pair (G,G) of SVM-DR"},
    "D": {"box": (678, 1198, 584, 1008), "title": "Residue pair (L,L) of SVM-DR"},
}
Y_TICKS = [20, 10, -10, -20, -30, -40, -50]
X_TICKS = [20, 40, 60, 80, 100, 120, 140]


def centres(mask_idx):
    out, s, p = [], None, None
    for i in mask_idx:
        if s is None:
            s = p = i
        elif i == p + 1:
            p = i
        else:
            out.append((s + p) / 2)
            s = p = i
    if s is not None:
        out.append((s + p) / 2)
    return out


def tick_map(dark, box):
    x0, x1, y0, y1 = box
    # left-axis ticks: 6 px stubs inside the box; keep those at the expected spacing
    ys = centres(np.flatnonzero(dark[y0 + 3:y1 - 2, x0 + 2:x0 + 8].sum(1) >= 5) + y0 + 3)
    xs = centres(np.flatnonzero(dark[y1 - 8:y1 - 1, x0 + 2:x1 - 2].sum(0) >= 6) + x0 + 2)
    # The top tick is 20 and the bottom -50; ticks are 10 apart. Pick the candidates nearest
    # a regular grid between the outermost two.
    top, bot = ys[0], ys[-1]
    step = (bot - top) / 7.0
    yfit = []
    for k, v in enumerate([20, 10, 0, -10, -20, -30, -40, -50]):
        want = top + k * step
        c = min(ys, key=lambda y: abs(y - want))
        if abs(c - want) < 2 and v != 0:
            yfit.append((v, c))
    xfit = []
    left = xs[0] if xs[0] > x0 + 20 else xs[1]
    xstep = (xs[-1] - left) / 6.0
    for k, v in enumerate(X_TICKS):
        want = left + k * xstep
        c = min(xs, key=lambda x: abs(x - want))
        if abs(c - want) < 2:
            xfit.append((v, c))
    by, ay = np.polyfit([v for v, _ in yfit], [c for _, c in yfit], 1)
    bx, ax = np.polyfit([v for v, _ in xfit], [c for _, c in xfit], 1)
    res = max(np.max(np.abs(np.polyval([by, ay], [v for v, _ in yfit]) - [c for _, c in yfit])),
              np.max(np.abs(np.polyval([bx, ax], [v for v, _ in xfit]) - [c for _, c in xfit])))
    return {"y_px": [float(ay), float(by)], "x_px": [float(ax), float(bx)],
            "ticks_used": [len(yfit), len(xfit)], "fit_residual_px": float(res)}


def read_bars(dark, box, m):
    x0, x1, y0, y1 = box
    ay, by = m["y_px"]
    ax, bx = m["x_px"]
    zero = ay
    vals = []
    for d in range(0, 151):
        cx = ax + bx * d
        cols = [c for c in range(int(np.floor(cx - 0.8)), int(np.ceil(cx + 0.8)) + 1)
                if abs(c - cx) <= 0.8 and x0 + 1 <= c <= x1 - 1]
        if d == 0:
            cols = [x0 + 1, x0 + 2]
        best = 0.0
        for c in cols:
            col = dark[:, c]
            z = int(round(zero))
            if not col[z - 1:z + 2].any():
                continue
            up = z
            while up - 1 > y0 + 1 and col[up - 1]:
                up -= 1
            dn = z
            while dn + 1 < y1 - 1 and col[dn + 1]:
                dn += 1
            v_up = (up - 0.5 - zero) / by     # by < 0: rows above zero are positive
            v_dn = (dn + 0.5 - zero) / by
            for v in (v_up, v_dn):
                if abs(v) > abs(best):
                    best = v
        vals.append(round(float(best), 2))
    return vals


def main(png, out):
    g = np.asarray(Image.open(png).convert("L")).astype(int)
    dark = g < 140
    res = {}
    for k, p in PANELS.items():
        m = tick_map(dark, p["box"])
        res[k] = {**p, **m, "values": read_bars(dark, p["box"], m)}
        print(k, m["ticks_used"], round(m["fit_residual_px"], 2), res[k]["values"][:12])
    json.dump(res, open(out, "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

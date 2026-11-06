"""Figure 3's pixel-to-data map and the published marker positions.

usage: figure3_axes.py PUBLISHED_PNG OUT_JSON

The map is fitted to the tick marks only (nothing inside the plot is fitted): the major ticks
inside the axes box at y = 0.86..0.94 (step 0.02) and x = 0..200 (step 50). The published series
are then read as marker centroids: red filled circles (SVM-DT) and black filled squares
(SVM-DR), as connected components of at least 150 px, outside the legend box.
"""
import json
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

Y_TICKS = [0.94, 0.92, 0.90, 0.88, 0.86]
X_TICKS = [0, 50, 100, 150, 200]


def runs(idx):
    groups, cur = [], [idx[0]]
    for i in idx[1:]:
        if i == cur[-1] + 1:
            cur.append(i)
        else:
            groups.append(cur)
            cur = [i]
    groups.append(cur)
    return [float(np.mean(g)) for g in groups]


def axes(img):
    g = np.asarray(img.convert("L")).astype(float)
    dark = g < 100
    H, W = dark.shape
    rows = np.flatnonzero(dark.sum(1) > 0.5 * W)
    cols = np.flatnonzero(dark.sum(0) > 0.5 * H)
    top, bottom = runs(list(rows))[0], runs(list(rows))[-1]
    left, right = runs(list(cols))[0], runs(list(cols))[-1]
    li, bi = int(round(left)) + 3, int(round(bottom)) - 3
    yt = [y for y in range(int(top) + 3, int(bottom) - 2) if dark[y, li:li + 13].sum() >= 11]
    xt = [x for x in range(li, int(right) - 2) if dark[bi - 10:bi, x].sum() >= 8]
    yc, xc = runs(yt), runs(xt)
    assert len(yc) == len(Y_TICKS) and len(xc) == len(X_TICKS), (yc, xc)
    by, ay = np.polyfit(Y_TICKS, yc, 1)
    bx, ax = np.polyfit(X_TICKS, xc, 1)
    res_y = float(np.max(np.abs(np.polyval([by, ay], Y_TICKS) - yc)))
    res_x = float(np.max(np.abs(np.polyval([bx, ax], X_TICKS) - xc)))
    return {"box_px": [left, right, top, bottom], "y_tick_px": yc, "x_tick_px": xc,
            "y_px": [ay, by], "x_px": [ax, bx], "fit_residual_px": max(res_x, res_y),
            "xlim": [(left - ax) / bx, (right - ax) / bx],
            "ylim": [(bottom - ay) / by, (top - ay) / by]}


def markers(img, ax):
    rgb = np.asarray(img.convert("RGB")).astype(int)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    red = (r > 180) & (g < 110) & (b < 110)
    black = (r < 90) & (g < 90) & (b < 90)
    left, right, top, bottom = ax["box_px"]
    inside = np.zeros_like(red)
    inside[int(top) + 4:int(bottom) - 3, int(left) + 4:int(right) - 3] = True
    out = {}
    for name, mask in (("SVM-DT", red), ("SVM-DR", black)):
        # opening removes the 1-2 px connecting lines, keeping the filled markers
        m = ndimage.binary_opening(mask & inside, structure=np.ones((7, 7)))
        lab, n = ndimage.label(m)
        pts = []
        for k in range(1, n + 1):
            yy, xx = np.nonzero(lab == k)
            if len(yy) < 150:
                continue
            pts.append((float(xx.mean()), float(yy.mean()), int(len(yy))))
        pts.sort()
        out[name] = pts
    return out


def main(png, out):
    img = Image.open(png)
    ax = axes(img)
    mk = markers(img, ax)
    a_x, b_x = ax["x_px"]
    a_y, b_y = ax["y_px"]
    series = {}
    for name, pts in mk.items():
        # the legend sample sits at x > 150 in data units and between 0.875 and 0.895
        vals = [((x - a_x) / b_x, (y - a_y) / b_y, n) for x, y, n in pts]
        vals = [v for v in vals if not (v[0] > 120 and 0.87 < v[1] < 0.90)]
        series[name] = [{"dmax": round(v[0], 1), "roc": round(v[1], 5), "px": v[2]} for v in vals]
    ax["series"] = series
    json.dump(ax, open(out, "w"), indent=1)
    for k, v in series.items():
        print(k, [(p["dmax"], p["roc"]) for p in v])
    print("fit residual px", ax["fit_residual_px"], "xlim", ax["xlim"], "ylim", ax["ylim"])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

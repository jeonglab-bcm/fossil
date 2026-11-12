"""Values read off the published figures (pixel positions, mapped through the axis frame).

Usage: read_published.py PUBLISHED_DIR OUT.json

Fig. 1: the ACC (black squares) and MCC (red circles) markers for LG = 1..14. The frame of the
plot is found from its dark border; its edges are the axis limits printed at its corners
(x 0 to 16, y 0.40 to 1.00). A marker is the run of rows in which at least 6 of the 13 columns
around the LG position carry the marker colour (connecting lines are 1 to 2 px thick).
Fig. 2A: the grey level of each of the 400 cells (median of the 7 x 7 pixels at its centre), read
as a linear grey scale from white (0) to black (150, the colour bar's ends); the box spans x 28 to
273 and y 23 to 275. Fig. 2B: the height of each bar (axis 0 at y 544, 60 at y 380, groups 55 px
apart, bars 11 px wide).
Fig. 3 and Fig. 5: the frame and axis limits (0 to 100 % on both axes), for drawing our curves on
the published grid.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def frame(img, thresh=110):
    g = img.mean(2)
    dark = g < thresh
    rows = np.where(dark.sum(1) > 0.5 * img.shape[1])[0]
    cols = np.where(dark.sum(0) > 0.5 * img.shape[0])[0]
    return int(cols.min()), int(cols.max()), int(rows.min()), int(rows.max())


def marker_rows(mask, xc, half=6, need=6):
    sub = mask[:, int(round(xc)) - half: int(round(xc)) + half + 1]
    rows = np.where(sub.sum(1) >= need)[0]
    if not len(rows):
        return None
    # the biggest run of consecutive rows
    runs = np.split(rows, np.where(np.diff(rows) > 1)[0] + 1)
    run = max(runs, key=len)
    return float(run.mean())


def main(pubdir, out):
    res = {}
    im = np.array(Image.open(Path(pubdir) / "fig1.png").convert("RGB")).astype(int)
    left, right, top, bottom = frame(im)
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    black = (r < 100) & (g < 100) & (b < 100)
    red = (r > 170) & (g < 110) & (b < 110)
    black[:, : left + 3] = black[:, right - 2:] = False
    black[: top + 3] = black[bottom - 2:] = False
    px = lambda x: left + (right - left) * x / 16.0
    val = lambda y: 0.40 + (bottom - y) / (bottom - top) * 0.60
    acc, mcc = [], []
    for lg in range(1, 15):
        acc.append(round(val(marker_rows(black, px(lg))), 4))
        mcc.append(round(val(marker_rows(red, px(lg))), 4))
    res["fig1"] = {"frame_px": [left, right, top, bottom], "x_limits": [0, 16], "y_limits": [0.40, 1.00],
                   "px_per_unit_y": (bottom - top) / 0.60, "LG": list(range(1, 15)), "ACC": acc, "MCC": mcc}
    g2 = np.array(Image.open(Path(pubdir) / "fig2.png").convert("L")).astype(float)
    aa = "ARNDCQEGHILKMFPSTWYV"
    x0, x1, y0, y1 = 28, 273, 23, 275
    cw, ch = (x1 - x0) / 20, (y1 - y0) / 20
    V = np.zeros((20, 20))
    for i in range(20):
        for k in range(20):
            cx, cy = int(x0 + cw * (k + .5)), int(y0 + ch * (i + .5))
            V[i, k] = (1 - np.median(g2[cy - 3:cy + 4, cx - 3:cx + 4]) / 255) * 150
    order = list(np.argsort(-V.ravel(), kind="stable"))
    rank = lambda p: order.index(aa.index(p[0]) * 20 + aa.index(p[1])) + 1
    rgb2 = np.array(Image.open(Path(pubdir) / "fig2.png").convert("RGB")).astype(float)
    bars = {}
    for kk, pair in enumerate(["RR", "RP", "PR", "AR"]):
        vals = []
        for l in range(5):
            xc = int(round(55.5 + 55 * l + (kk - 1.5) * 11))
            col = rgb2[326:544, xc - 2:xc + 3].mean(1)
            same = np.abs(col - col[-3]).sum(1) < 120
            r = len(same) - 1
            while r > 0 and same[r - 1]:
                r -= 1
            vals.append(round((544 - (r + 326) + 0.5) / (544 - 380) * 60, 1))
        bars[pair] = vals
    res["fig2"] = {"a_cells": np.round(V, 1).tolist(),
                   "a_top8": ["".join((aa[k // 20], aa[k % 20])) for k in order[:8]],
                   "a_rank": {p: rank(p) for p in ("RR", "RP", "PR", "AR")}, "b_bars": bars}
    for k in (3, 4, 5):
        im = np.array(Image.open(Path(pubdir) / f"fig{k}.png").convert("RGB")).astype(int)
        res[f"fig{k}"] = {"frame_px": list(frame(im)), "note": "outer frame; the axis limits sit inside it"}
    Path(out).write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res["fig1"]))


if __name__ == "__main__":
    main(*sys.argv[1:3])

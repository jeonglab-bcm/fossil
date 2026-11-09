"""Values read off the published figures (pixel positions, mapped through the axis frame).

Usage: read_published.py PUBLISHED_DIR OUT.json

Fig. 1: the ACC (black squares) and MCC (red circles) markers for LG = 1..14. The frame of the
plot is found from its dark border; its edges are the axis limits printed at its corners
(x 0 to 16, y 0.40 to 1.00). A marker is the run of rows in which at least 6 of the 13 columns
around the LG position carry the marker colour (connecting lines are 1 to 2 px thick).
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
    for k in (3, 4, 5):
        im = np.array(Image.open(Path(pubdir) / f"fig{k}.png").convert("RGB")).astype(int)
        res[f"fig{k}"] = {"frame_px": list(frame(im)), "note": "outer frame; the axis limits sit inside it"}
    Path(out).write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res["fig1"]))


if __name__ == "__main__":
    main(*sys.argv[1:3])

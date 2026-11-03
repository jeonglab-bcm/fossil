"""Read the box statistics of the published Fig. 2 from its pixels.

ggplot2 places the 7 methods of each panel at x = 1..7 on a discrete axis expanded by 0.6, with
boxes 0.75 wide. For each box this reads, in F.score units: the whisker ends (dark line along the
box centre), the hinges (extent of the fill colour beside the centre) and the median (dark row
inside the fill). Usage: python3 fig2_measure.py <figure-2.jpg> <out.json>
"""
import json
import sys

import numpy as np
from PIL import Image

METHODS = ["GABi.block", "GABi.cor", "GABi.highvar", "ISA", "CC", "Plaid", "Bimax"]
STRUCTURES = ["block", "cor", "highvar"]


def long_columns(g, top, bottom, frac=0.9):
    cov = (g[top:bottom] < 150).mean(axis=0)
    cols = np.where(cov > frac)[0]
    return [float(c.mean()) for c in np.split(cols, np.where(np.diff(cols) > 1)[0] + 1)]


def main():
    path, out = sys.argv[1], sys.argv[2]
    rgb = np.asarray(Image.open(path).convert("RGB")).astype(int)
    g = rgb.mean(axis=2)
    sat = rgb.max(axis=2) - rgb.min(axis=2)

    # Panel interior: below the strip (row 36) and above the bottom border (row 1285).
    top, bottom = 40, 1280
    borders = long_columns(g, top, bottom)
    panels = [(borders[0], borders[1]), (borders[2], borders[3]), (borders[4], borders[5])]

    # y calibration from the tick marks left of the first panel.
    x0 = int(round(borders[0]))
    band = g[:, x0 - 6: x0 - 1]
    rows = np.where((band < 170).sum(axis=1) >= 4)[0]
    rows = rows[(rows > top) & (rows < bottom)]
    ticks = [float(r.mean()) for r in np.split(rows, np.where(np.diff(rows) > 1)[0] + 1)]
    vals = [1.0, 0.75, 0.5, 0.25, 0.0]
    slope, icpt = np.polyfit(ticks, vals, 1)
    to_val = lambda y: float(slope * y + icpt)

    res = {"y_ticks_px": ticks, "y_per_px": float(slope), "panels_px": panels, "boxes": {}}
    for s, (pl, pr) in zip(STRUCTURES, panels):
        unit = (pr - pl) / 7.2
        res["boxes"][s] = {}
        for k, m in enumerate(METHODS, start=1):
            cx = pl + (k - 0.4) * unit
            c = int(round(cx))
            side = int(round(cx + 0.2 * unit))
            fill = np.where(sat[top:bottom, side] > 60)[0] + top
            dark_side = np.where(g[top:bottom, side] < 90)[0] + top
            box = {}
            if len(fill):
                q3_px, q1_px = fill.min() - 0.5, fill.max() + 0.5
                inner = dark_side[(dark_side > fill.min()) & (dark_side < fill.max())]
                # A median on a hinge overlays the box border; take that hinge.
                med_px = float(inner.mean()) if len(inner) else (
                    q1_px if g[int(fill.max()) + 1: int(fill.max()) + 4, side].min() < 90 else q3_px)
            else:
                # Degenerate box: hinges and median coincide on one dark row.
                q3_px = q1_px = med_px = float(dark_side.mean())
            box["q1"], box["q3"] = to_val(q1_px), to_val(q3_px)
            box["median"] = to_val(med_px) if med_px is not None else None
            # Whiskers: dark pixels on the centre column contiguous with the box.
            col = g[:, c - 2: c + 3].min(axis=1) < 150
            y = int(np.floor(q3_px))
            while y > top and col[y - 1]:
                y -= 1
            box["upper"] = to_val(y)
            y = int(np.ceil(q1_px))
            while y < bottom and col[y + 1]:
                y += 1
            box["lower"] = to_val(y)
            # Outlier dots: separate dark runs on the centre column beyond the whiskers.
            dots = np.where(col[top:bottom])[0] + top
            runs = np.split(dots, np.where(np.diff(dots) > 1)[0] + 1) if len(dots) else []
            box["outliers"] = [to_val(float(r.mean())) for r in runs
                               if len(r) and (r.max() < to_px(box["upper"], slope, icpt) - 2 or
                                              r.min() > to_px(box["lower"], slope, icpt) + 2)]
            res["boxes"][s][m] = {k2: (round(v, 4) if isinstance(v, float) else
                                       [round(o, 4) for o in v] if isinstance(v, list) else v)
                                  for k2, v in box.items()}
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
    for s in STRUCTURES:
        for m in METHODS:
            b = res["boxes"][s][m]
            print(f"{s:8s} {m:13s} lo {b['lower']:.3f} q1 {b['q1']:.3f} med "
                  f"{b['median'] if b['median'] is None else round(b['median'], 3)} q3 {b['q3']:.3f} "
                  f"hi {b['upper']:.3f} out {len(b['outliers'])}")


def to_px(v, slope, icpt):
    return (v - icpt) / slope


if __name__ == "__main__":
    main()

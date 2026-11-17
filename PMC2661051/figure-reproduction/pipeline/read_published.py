#!/usr/bin/env python3
"""Read the plotted values of Figs 2, 3 and 4 off the published figure files (Springer originals,
1200 px wide).

Each axis is calibrated from its own tick marks (pixel rows or columns found in the image and
listed below with the tick labels they carry); nothing inside the plot box is fitted.

- Figs 2 and 4, right panels: the bar heights at p-value cutoff 0.01, resampling (black) and
  permutation (blue), for the eight gene set statistics. A bar's top is the first dark pixel
  (grey < 128) in its middle column below the legend.
- Fig. 3: the counts of the two histograms (mean pairwise correlation, bins of 0.01 from -0.01 to
  0.30; mean absolute correlation, bins of 0.005 from 0.125 to 0.325).

Usage: read_published.py FIGDIR OUT.json
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

STATS = ["mean", "median", "maxmean", "es", "wilcoxon", "condfdr", "globaltest", "hotelling"]


def grey(path):
    return np.asarray(Image.open(path).convert("L")).astype(int)


def find_ticks(a, x0, x1, rows):
    """Rows where the short tick marks left of a y axis are dark."""
    return [y for y in rows if a[y, x0:x1].mean() < 160]


def bars(path, top_value):
    a = grey(path)
    # y axis of the right panel: x = 646; tick marks at x 642-645
    ticks = find_ticks(a, 642, 646, range(60, 530))
    zero, top = max(ticks), min(ticks)
    scale = (zero - top) / top_value  # pixels per set
    out = {"axis": {"tick_rows": ticks, "zero_row": zero, "top_row": top, "top_value": top_value,
                    "pixels_per_unit": round(scale, 4)}, "bars": {}}
    for k, st in enumerate(STATS):
        for method, x in (("resampling", 677 + 64 * k), ("permutation", 698 + 64 * k)):
            col = a[100:zero + 1, x]
            dark = np.where(col < 128)[0]
            t = 100 + dark.min() if len(dark) else zero
            v = (zero - t) / scale
            out["bars"][f"{st}.{method}"] = {"column": x, "top_row": int(t), "value": round(float(v), 2),
                                             "read": int(round(v))}
    return out


def histogram(a, zero_row, rows_per_count, x_of, lo, width, nbins, top_limit):
    counts = []
    for i in range(nbins):
        centre = lo + (i + 0.5) * width
        x = int(round(x_of(centre)))
        col = a[top_limit:int(zero_row) + 1, x]
        dark = np.where(col < 128)[0]
        t = top_limit + dark.min() if len(dark) else zero_row
        counts.append({"bin": [round(lo + i * width, 3), round(lo + (i + 1) * width, 3)], "column": x,
                       "value": round(float((zero_row - t) / rows_per_count), 2),
                       "read": int(round((zero_row - t) / rows_per_count))})
    return counts


def fig3(path):
    a = grey(path)
    # x axis ticks (both panels): 0.00 at column 165.5, 0.30 at 1041.5 (columns found at rows 358-369)
    xt0, xt1 = 165.5, 1041.5
    x_of = lambda v: xt0 + (v - 0.0) / 0.30 * (xt1 - xt0)
    # top panel y ticks: 0 at row 347.5 ... 60 at row 99 (rows found left of the axis at x 88-95)
    top_ticks = find_ticks(a, 88, 96, range(80, 360))
    bot_ticks = find_ticks(a, 88, 96, range(580, 840))
    top_zero, top_hi = (347 + 348) / 2, 99
    bot_zero, bot_hi = (827 + 828) / 2, 599
    top = histogram(a, top_zero, (top_zero - top_hi) / 60, x_of, -0.01, 0.01, 31, 95)
    bot = histogram(a, bot_zero, (bot_zero - bot_hi) / 40, x_of, 0.125, 0.005, 40, 560)
    return {"axis": {"x_ticks": {"0.00": xt0, "0.30": xt1}, "top_tick_rows": top_ticks, "bottom_tick_rows": bot_ticks},
            "mean_correlation": top, "mean_abs_correlation": bot}


def main():
    figdir, out = Path(sys.argv[1]), Path(sys.argv[2])
    res = {"fig2": bars(figdir / "Fig2.png", 250), "fig4": bars(figdir / "Fig4.png", 80),
           "fig3": fig3(figdir / "Fig3.png")}
    res["fig3"]["total_top"] = sum(b["read"] for b in res["fig3"]["mean_correlation"])
    res["fig3"]["total_bottom"] = sum(b["read"] for b in res["fig3"]["mean_abs_correlation"])
    out.write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main()

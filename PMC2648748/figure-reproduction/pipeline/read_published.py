"""Read the plotted values off the paper's Figs 2 and 3.

usage: read_published.py FIG2_PNG FIG3_PNG OUT_JSON

The figures are base-R graphics (barplot and notched boxplot), embedded in the paper's PDF as
2400 x 1200 images. For each of the six panels of a figure we find the frame (3-px black lines),
fit the pixel-to-value map of the y axis to its tick marks (0, 20, ... ; nothing inside the frame
is fitted) and record the fit residual, then read:

* Fig. 2: the top edge of each of the 16 bars (4 MAFs x 4 methods), at the bar centre given by
  barplot's geometry (bars at 1 + 5g + b, x range [1, 20] padded by 4%). Power is a count out of
  100 data sets, so each reading is also rounded to an integer.
* Fig. 3: for each of the 4 boxes, the median (the thick line), the box hinges, the whisker ends
  and the outliers, read along the box's centre column.
"""
import json
import sys

import numpy as np
from PIL import Image

DARK = 60  # black ink (outlines, text); the bar fills are grey 102, 153, 204 and 250


def load(path):
    return np.asarray(Image.open(path).convert("L"), dtype=int)


def runs(mask):
    """(start, end) of consecutive True runs in a 1-D boolean array (end inclusive)."""
    out, start = [], None
    for i, v in enumerate(mask):
        if v and start is None:
            start = i
        if not v and start is not None:
            out.append((start, i - 1))
            start = None
    if start is not None:
        out.append((start, len(mask) - 1))
    return out


def frames(a):
    """Panel frames: centres of the long horizontal and vertical black lines."""
    dark = a < DARK
    h, w = a.shape
    rows = [c for c in runs(dark.sum(axis=1) > 0.6 * w * 0.7) if c[1] - c[0] <= 6]
    ys = [(s + e) / 2 for s, e in rows]
    # frame sides are dark over the whole height of both rows of frames (bar outlines are not)
    span = np.zeros(h, bool)
    for r in range(0, len(ys) - 1, 2):
        span[int(ys[r]):int(ys[r + 1])] = True
    cols = [c for c in runs(dark[span].mean(axis=0) > 0.97) if c[1] - c[0] <= 6]
    xs = [(s + e) / 2 for s, e in cols]
    if len(ys) != 4 or len(xs) != 6:
        raise SystemExit(f"expected 2 x 3 frames, found rows {ys} cols {xs}")
    return [(xs[2 * c], ys[2 * r], xs[2 * c + 1], ys[2 * r + 1]) for r in range(2) for c in range(3)]


def y_ticks(a, frame, labels):
    """Fit value -> pixel row from the tick marks left of the frame."""
    x0, y0, x1, y1 = frame
    col = a[:, int(x0) - 12] < DARK
    centres = [(s + e) / 2 for s, e in runs(col) if e - s <= 6 and y0 - 30 <= s <= y1 + 30]
    if len(centres) != len(labels):
        raise SystemExit(f"found {len(centres)} ticks for labels {labels} in frame {frame}")
    vals = np.array(sorted(labels, reverse=True), float)
    pix = np.array(centres)
    b, c = np.polyfit(vals, pix, 1)
    resid = float(np.max(np.abs(pix - (b * vals + c))))
    return b, c, resid


def bar_top(a, x, y_zero):
    """Pixel row of a bar's top edge, scanning up from the baseline at column x.

    The baseline (y = 0) is a 3-px black line. A bar of height 0 is only that line, with
    background (255) above it; a bar of height 1 (3.8 px) merges its top edge with it; otherwise
    the fill (grey 102 to 250) runs up to the black top edge."""
    y = int(round(y_zero))
    while a[y - 1, x] < DARK:              # up through the baseline (and a merged top edge)
        y -= 1
    if y_zero - y > 3:                     # thicker than the baseline: the top edge sits on it
        return y + 1.5
    if a[y - 3, x] >= 254:                 # background above the baseline: zero height
        return y_zero
    while a[y - 1, x] >= DARK:             # up through the fill
        y -= 1
    top = y - 1
    while a[top - 1, x] < DARK:
        top -= 1
    return (top + y - 1) / 2


def fig2(path):
    a = load(path)
    out = []
    for p, fr in enumerate(frames(a)):
        x0, y0, x1, y1 = fr
        b, c, resid = y_ticks(a, fr, [0, 20, 40, 60, 80, 100])
        unit = (x1 - x0) / (19 * 1.08)
        bars = []
        for g in range(4):
            for m in range(4):
                xc = x0 + (1.5 + 5 * g + m - (1 - 19 * 0.04)) * unit
                top = bar_top(a, int(round(xc)), c)
                v = (top - c) / b
                bars.append({"maf_index": g, "method_index": m, "value": round(v, 2),
                             "count": int(round(v)), "x_px": round(xc, 1), "y_px": top})
        out.append({"panel": p, "frame": fr, "tick_fit_max_residual_px": round(resid, 2),
                    "px_per_unit": round(-b, 3), "bars": bars})
    return out


def fig3(path):
    a = load(path)
    out = []
    for p, fr in enumerate(frames(a)):
        x0, y0, x1, y1 = fr
        b, c, resid = y_ticks(a, fr, [0, 20, 40, 60, 80])
        unit = (x1 - x0) / (4 * 1.08)        # boxplot: boxes at 1..4, x range [0.5, 4.5] + 4%
        boxes = []
        for g in range(4):
            xc = x0 + (1 + g - (0.5 - 4 * 0.04)) * unit
            # median: the thick line, read in a column off the dashed whisker (centre) line
            xm = int(round(xc + 0.12 * unit))
            col = a[int(y0) + 3:int(y1) - 2, xm] < DARK
            rr = [(s + int(y0) + 3, e + int(y0) + 3) for s, e in runs(col)]
            thick = max(rr, key=lambda t: t[1] - t[0])
            med_px = (thick[0] + thick[1]) / 2
            # maximum: the topmost ink near the centre column; a ring (outlier circle) gives two
            # short runs around its centre, a whisker cap a single 3-px line
            xi = int(round(xc))
            col = a[int(y0) + 3:int(y1) - 2, xi] < DARK
            rc = [(s + int(y0) + 3, e + int(y0) + 3) for s, e in runs(col)]
            first = rc[0]
            if len(rc) > 1 and rc[1][0] - first[1] <= 8 and rc[1][1] - first[0] <= 13:
                max_px = (first[0] + rc[1][1]) / 2      # outlier circle
                kind = "outlier"
            else:
                max_px = (first[0] + first[1]) / 2      # whisker cap
                kind = "whisker"
            boxes.append({"maf_index": g, "x_px": round(xc, 1),
                          "median": round((med_px - c) / b, 2),
                          "median_line_px": thick[1] - thick[0] + 1,
                          "max": round((max_px - c) / b, 2), "max_kind": kind})
        out.append({"panel": p, "frame": fr, "tick_fit_max_residual_px": round(resid, 2),
                    "px_per_unit": round(-b, 3), "boxes": boxes})
    return out


def main():
    f2, f3, outp = sys.argv[1:4]
    res = {"fig2": fig2(f2), "fig3": fig3(f3)}
    with open(outp, "w") as fh:
        json.dump(res, fh, indent=1)


if __name__ == "__main__":
    main()

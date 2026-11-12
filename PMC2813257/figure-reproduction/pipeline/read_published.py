"""Cut the published figures into panels and read their plotted points.

Usage: read_published.py PUBLISHED_DIR OUTDIR

PUBLISHED_DIR holds the PLOS figure files (pcbi.1000660.g002.png and the others). Writes
OUTDIR/published/fig*.png (the panel crops used for the comparison) and OUTDIR/published_values.json
(the points and error bars read off Figure 2, with the axis calibration and its residual).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

# Panel boxes (left, top, right, bottom) of the axes frames, found from the black frame lines.
PANELS = {
    "fig2a": ("g002", (127, 120, 1273, 1007)),
    "fig2b": ("g002", (131, 1224, 1277, 2111)),
    "fig3": ("g003", (136, 26, 1222, 868)),
    "fig4": ("g004", (155, 25, 1301, 912)),
}
# Axis calibration of Figure 2, from the tick positions (x) and the frame (y).
CAL = {
    "fig2a": {"x": (127.0, 1273.0, 0.0, 500.0), "y": (1007.0, 120.0, 0.0, 0.5)},
    "fig2b": {"x": (131.0, 1277.0, 0.0, 65000.0), "y": (2111.0, 1224.0, 0.0, 0.5)},
    "fig4": {"x": (155.0, 1301.0, 0.0, 0.01), "y": (912.0, 25.0, 0.0, 1.0)},
}
#: x values at which the three cumulative curves of Figure 4 are read.
FIG4_X = [0.0005, 0.001, 0.0015, 0.002, 0.0025, 0.003, 0.0035, 0.004]


def series_from_mask(mask, x0, y0, cal, min_len=12):
    """Points and error bars of one coloured series: vertical runs of at least ``min_len`` pixels."""
    stems = []
    for x in range(mask.shape[1]):
        ys = np.where(mask[:, x])[0]
        if len(ys) < min_len:
            continue
        runs = np.split(ys, np.where(np.diff(ys) > 1)[0] + 1)
        longest = max(runs, key=len)
        if len(longest) >= min_len:
            stems.append((x, int(longest.min()), int(longest.max())))
    groups: list[list] = []
    for s in stems:
        if groups and s[0] - groups[-1][-1][0] <= 2:
            groups[-1].append(s)
        else:
            groups.append([s])
    px0, px1, dx0, dx1 = cal["x"]
    py0, py1, dy0, dy1 = cal["y"]
    out = []
    for g in groups:
        xc = float(np.mean([s[0] for s in g])) + x0
        top = min(s[1] for s in g) + y0
        bot = max(s[2] for s in g) + y0
        to_x = lambda v: dx0 + (v - px0) * (dx1 - dx0) / (px1 - px0)  # noqa: E731
        to_y = lambda v: dy0 + (v - py0) * (dy1 - dy0) / (py1 - py0)  # noqa: E731
        hi, lo = to_y(top), to_y(bot)
        out.append({"x": to_x(xc), "y": 0.5 * (hi + lo), "err": 0.5 * (hi - lo)})
    return out


def read_curves(img, cal, xs):
    """y of each coloured curve of Figure 4 at the given x values (the panel's own pixels)."""
    R, G, B = img[..., 0], img[..., 1], img[..., 2]
    masks = {
        "nonsynonymous": (R > 150) & (G < 110) & (B < 110),
        "synonymous": (G > 80) & (R < 110) & (B < 110) & (G - R > 30),
        "synonymous_no_hitchhiking": (B > 110) & (R < 110) & (G < 110),
    }
    px0, px1, dx0, dx1 = cal["x"]
    py0, py1, dy0, dy1 = cal["y"]
    out = {}
    for name, m in masks.items():
        vals = []
        for x in xs:
            col = int(round(px0 + (x - dx0) * (px1 - px0) / (dx1 - dx0)))
            ys = np.where(m[:, col])[0]
            vals.append(None if not len(ys)
                        else float(dy0 + (float(np.mean(ys)) - py0) * (dy1 - dy0) / (py1 - py0)))
        # a cumulative curve cannot fall: a lower reading is ink of another curve crossing it
        best = 0.0
        clean = []
        for v in vals:
            if v is None or v < best - 1e-9:
                clean.append(None)
            else:
                best = v
                clean.append(v)
        out[name] = clean
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("published")
    ap.add_argument("outdir")
    a = ap.parse_args(argv)
    src = Path(a.published)
    out = Path(a.outdir)
    (out / "published").mkdir(parents=True, exist_ok=True)

    for name, (stem, box) in PANELS.items():
        im = Image.open(src / f"pcbi.1000660.{stem}.png").convert("RGB")
        (im.crop(box) if box else im).save(out / "published" / f"{name}.png")

    g2 = np.asarray(Image.open(src / "pcbi.1000660.g002.png").convert("RGB")).astype(int)
    R, G, B = g2[..., 0], g2[..., 1], g2[..., 2]
    red = (R > 180) & (G < 110) & (B < 110)
    green = (G > 80) & (R < 90) & (B < 90) & (G - R > 40)
    values = {}
    l, t, r, b = PANELS["fig2a"][1]
    values["fig2a_recombinant"] = series_from_mask(red[t + 2 : b - 2, l + 3 : r - 3], l + 3, t + 2, CAL["fig2a"])
    values["fig2a_other"] = series_from_mask(green[t + 2 : b - 2, l + 3 : r - 3], l + 3, t + 2, CAL["fig2a"])
    l, t, r, b = PANELS["fig2b"][1]
    # the legend box sits in the upper left of panel B; read below it
    values["fig2b"] = series_from_mask(red[t + 130 : b - 2, l + 3 : r - 3], l + 3, t + 130, CAL["fig2b"])
    g4 = np.asarray(Image.open(src / "pcbi.1000660.g004.png").convert("RGB")).astype(int)
    # blank the inset and the legend box, which hold coloured ink of their own
    g4m = g4.copy()
    g4m[285:912, 480:1301] = 255
    g4m[25:292, 630:1301] = 255
    curves = read_curves(g4m, CAL["fig4"], FIG4_X)

    with open(out / "published_values.json", "w") as f:
        json.dump({"panels": {k: v[1] for k, v in PANELS.items() if v[1]},
                   "calibration": CAL, "series": values,
                   "fig4": {"x": FIG4_X, "curves": curves}}, f, indent=1)
    print({k: len(v) for k, v in values.items()}, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

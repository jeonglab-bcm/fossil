"""Read bar heights (Fig. 3) and line points (Fig. 2) off the published raster figures.

Usage: digitize.py PUBLISHED_DIR OUT.json

Both figures are 1494 px wide PNGs (PLOS "large" size). The y axis of each panel is calibrated
from its horizontal grid lines, whose values are the printed tick labels (Fig. 3: 0.4 to 1 in
steps of 0.1; Fig. 2: 0 to 8 or 0 to 4 in steps of 1); the fit residual is recorded. Nothing
inside the plot is fitted. Values read this way are assumptions of kind read_from_figure.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

FIG3_COLOURS = {
    "Gene": (68, 114, 172),
    "PAC": (170, 68, 66),
    "PAC_random": (219, 132, 61),
    "Mean": (139, 165, 77),
    "Median": (115, 90, 147),
    "PCA": (70, 155, 172),
}
FIG2_COLOURS = {
    "PAC": (75, 108, 180),
    "Genes": (155, 52, 100),
    "CORGs": (155, 204, 60),
    "PAC_all": (100, 100, 155),
}
WITHIN = ["NF-kB", "Leukemia", "Prostate", "Breast Netherlands", "Breast USA", "Lung Michigan", "Lung Boston"]
CROSS = ["Breast Netherlands -> Breast USA", "Breast USA -> Breast Netherlands",
         "Lung Michigan -> Lung Boston", "Lung Boston -> Lung Michigan"]


def load(path):
    return np.asarray(Image.open(path).convert("RGB")).astype(int)


def mask(im, colour, tol=28):
    return np.all(np.abs(im - np.array(colour)) <= tol, axis=2)


def gridlines(im, box, min_frac=0.6):
    """Rows inside box (x0, y0, x1, y1) that are mostly grey: grid lines and the axis."""
    x0, y0, x1, y1 = box
    sub = im[y0:y1, x0:x1]
    grey = (np.abs(sub[..., 0] - sub[..., 1]) < 12) & (np.abs(sub[..., 1] - sub[..., 2]) < 12) & (sub[..., 0] < 200)
    rows = np.where(grey.mean(axis=1) > min_frac)[0] + y0
    merged = []
    for r in rows:
        if merged and r - merged[-1][-1] <= 2:
            merged[-1].append(r)
        else:
            merged.append([r])
    return [float(np.mean(m)) for m in merged]


def calibrate(rows, tick, bottom, bottom_value, edges=()):
    """Fit value = a + b * row through the interior grid lines.

    rows: detected grid rows; tick: the value step between grid lines; bottom: the row of the
    panel's lower frame and bottom_value its value (or the value of the nearest grid line below
    it). Rows at the frame edges are dropped; the remaining lines are numbered by their spacing.
    """
    inner = [r for r in rows if all(abs(r - e) > 3 for e in edges)]
    diffs = np.diff(inner)
    step = float(np.median([d for d in diffs if d < 1.5 * diffs.min()]))
    low = max(inner)
    v_low = bottom_value + round((bottom - low) / step) * tick
    vals = [v_low + round((low - r) / step) * tick for r in inner]
    b, a = np.polyfit(inner, vals, 1)
    return float(a), float(b), float(np.max(np.abs(a + b * np.array(inner) - np.array(vals))))


def nearest(im, colours, tol):
    """Label each pixel with the index of the nearest colour, or -1 when none is within tol."""
    c = np.array(list(colours.values()))
    d = np.sqrt(((im[:, :, None, :] - c[None, None]) ** 2).sum(-1))
    lab = d.argmin(-1)
    lab[d.min(-1) > tol] = -1
    return lab


def fig3(path):
    im = load(path)
    out = {}
    for panel, box, names, ticks in [
        ("A", (105, 40, 1255, 490), WITHIN, [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4]),
        ("B", (92, 630, 640, 875), CROSS, [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4]),
    ]:
        rows = gridlines(im, box)
        x0, y0, x1, y1 = box
        # the bars stand on the 0.4 axis: their lowest coloured row is the axis
        anymask = np.zeros(im.shape[:2], bool)
        for c in FIG3_COLOURS.values():
            anymask |= mask(im, c)
        bar_rows = np.where(anymask[y0:y1, x0:x1].sum(axis=1) > 20)[0]
        bottom = float(bar_rows.max() + y0 + 0.5)
        a, b, resid = calibrate([r for r in rows if r < bottom - 3] + [bottom], 0.1, bottom, 0.4)
        bars = []
        for m, c in FIG3_COLOURS.items():
            mk = mask(im[y0:y1, x0:x1], c)
            cols = np.where(mk.sum(axis=0) > 8)[0]
            if len(cols) == 0:
                continue
            runs, cur = [], [cols[0]]
            for x in cols[1:]:
                if x - cur[-1] <= 1:
                    cur.append(x)
                else:
                    runs.append(cur)
                    cur = [x]
            runs.append(cur)
            for r in runs:
                if len(r) < 10:
                    continue
                mid = r[len(r) // 2]
                ys = np.where(mk[:, r[2] : r[-2]].mean(axis=1) > 0.8)[0]
                if len(ys) == 0:
                    continue
                top = ys.min() + y0
                bars.append((x0 + mid, m, a + b * (top - 0.5), (x0 + r[0], x0 + r[-1])))
        bars.sort()
        groups, cur = [], []
        for x, m, v, ext in bars:
            if cur and (m in [g[1] for g in cur] or x - cur[-1][0] > 60):
                groups.append(cur)
                cur = []
            cur.append((x, m, v, ext))
        groups.append(cur)
        groups = [g for g in groups if len(g) >= 2]
        out[panel] = {"calibration_residual": resid, "a": a, "b": b,
                      "groups": {n: {m: round(v, 4) for _, m, v, _ in g} for n, g in zip(names, groups)},
                      "extent": {n: {m: [int(e[0]), int(e[1])] for _, m, _, e in g} for n, g in zip(names, groups)}}
    return out


def fig2(path):
    im = load(path)
    # panel plot boxes (x0, y0, x1, y1) and y ranges, read from the 1494 x 2302 figure
    boxes = {
        "A": ((118, 105, 690, 435), 8), "B": ((882, 95, 1452, 440), 4),
        "C": ((122, 690, 692, 1032), 8), "D": ((884, 688, 1450, 1030), 4),
        "E": ((126, 1275, 696, 1620), 8), "F": ((882, 1275, 1464, 1618), 4),
        "G": ((130, 1860, 696, 2205), 8), "H": ((888, 1860, 1466, 2205), 4),
    }
    out = {}
    for panel, ((x0, y0, x1, y1), top) in boxes.items():
        rows = gridlines(im, (x0 + 5, y0 - 6, x1 - 5, y1 + 6), 0.5)
        edges = (rows[0], rows[-1])
        a, b, resid = calibrate(rows, 1.0, rows[-1], 0.0, edges)
        # x positions of the five categories: evenly spaced, first and last at the box edges
        xs = np.linspace(x0, x1, 5)
        series = {}
        lab = nearest(im[y0 - 8 : y1 + 8], FIG2_COLOURS, 40)
        for si, (s, c) in enumerate(FIG2_COLOURS.items()):
            mk = np.zeros(im.shape[:2], bool)
            mk[y0 - 8 : y1 + 8] = lab == si
            vals = []
            for x in xs:
                xi = int(round(x))
                win = mk[y0 - 8 : y1 + 8, max(xi - 3, 0) : xi + 4]
                ys = np.where(win.sum(axis=1) >= 2)[0]
                if not len(ys):
                    vals.append(None)
                    continue
                # the largest run of rows: the series' own line and marker, not stray edge pixels of
                # a neighbouring series of a similar colour
                runs = np.split(ys, np.where(np.diff(ys) > 2)[0] + 1)
                run = max(runs, key=len)
                vals.append(round(a + b * (y0 - 8 + float(np.median(run))), 3))
            # A reading that jumps more than a quarter of the axis from its nearest readable
            # neighbour is another series' marker sitting on this one (Fig. 2C at 1%): unreadable.
            for i, v in enumerate(vals):
                nb = [vals[j] for j in (i - 1, i + 1) if 0 <= j < len(vals) and vals[j] is not None]
                if v is not None and nb and min(abs(v - n) for n in nb) > top / 4:
                    vals[i] = None
            series[s] = vals
        out[panel] = {"calibration_residual": resid, "series": series, "a": a, "b": b,
                      "x": [float(x) for x in xs], "box": [x0, y0, x1, y1]}
    return out


def main(pub: Path, out: Path):
    res = {"fig3": fig3(pub / "figure-3.png"), "fig2": fig2(pub / "figure-2.png")}
    out.write_text(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    print(json.dumps(main(Path(sys.argv[1]), Path(sys.argv[2])), indent=1))

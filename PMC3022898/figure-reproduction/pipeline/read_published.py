"""Read the bar heights of Figs 1-4 off the published JPEGs.

Usage: read_published.py FIG_DIR OUT.json

Each figure is an Excel bar chart: three RR groups (1.0, 2.0, 5.0) of four bars (ESR_S log, ESR_R log,
ESR_R binomial, empirical), y from 0.00 to 0.20. The pixel-to-data map comes from the axes alone:

* y: the centres of the eleven tick labels 0.00, 0.02, ..., 0.20 (rows of label ink left of the axis),
  fitted by least squares; the residual is recorded.
* bars: on the row just above the x axis, each group is one run of bar ink; its four bars split it
  evenly. A bar's top is where the column profile, scanned down from the plot top, first crosses
  half-way between the background (255) and the darkest pixel of the bar's border; the median over
  the bar's inner columns, with linear interpolation between rows.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

LABELS = [round(0.02 * i, 2) for i in range(11)]
SERIES = ["esr_s_log", "esr_r_log", "esr_r_binomial", "empirical"]
GROUPS = ["1.0", "2.0", "5.0"]


def longest_run(mask):
    best, cur, end = 0, 0, -1
    for i, v in enumerate(mask):
        cur = cur + 1 if v else 0
        if cur > best:
            best, end = cur, i
    return best, end - best + 1


def geometry(g):
    h, w = g.shape
    dark = g < 180
    # y axis: the column with the longest vertical run of ink; x axis: the row with the longest horizontal run
    col = max(range(w), key=lambda c: longest_run(dark[:, c])[0])
    row = max(range(h), key=lambda r: longest_run(dark[r, :])[0])
    run_len, run_start = longest_run(dark[:, col])
    top = run_start
    right = col + longest_run(dark[row, col:])[0] - 1
    return {"axis_x": int(col), "axis_y": int(row), "plot_top": int(top), "plot_right": int(right)}


def tick_label_rows(g, geo):
    """Centres (rows) of the eleven y tick labels, from label ink in the band left of the axis."""
    x0 = geo["axis_x"]
    band = g[:, max(0, x0 - 28):x0 - 3] < 160  # clear of the rotated axis title further left
    ink = band.sum(1)
    rows, clusters, cur = np.nonzero(ink)[0], [], []
    for r in rows:
        if cur and r > cur[-1] + 2:
            clusters.append(cur)
            cur = []
        cur.append(r)
    if cur:
        clusters.append(cur)
    centres = [float(np.average(c, weights=ink[c])) for c in clusters
               if geo["plot_top"] - 8 <= np.mean(c) <= geo["axis_y"] + 8]
    if len(centres) != len(LABELS):
        raise SystemExit(f"found {len(centres)} tick labels, expected {len(LABELS)}")
    return sorted(centres, reverse=True)  # 0.00 at the bottom


def bar_extents(g, geo):
    """Left and right column of each bar: each group is one run of ink on the row above the x axis."""
    y = geo["axis_y"] - 4
    row = g[y, geo["axis_x"] + 1:geo["plot_right"]]
    ink = row < 245
    runs, start = [], None
    for i, v in enumerate(ink):
        if v and start is None:
            start = i
        if not v and start is not None:
            runs.append((start, i - 1))
            start = None
    if start is not None:
        runs.append((start, len(ink) - 1))
    # A white bar has ink only at its border: merge runs closer than a bar width into one group.
    groups = []
    for a, b in runs:
        if groups and a - groups[-1][1] < 32:  # within a group: at most one white bar's interior (~26 px)
            groups[-1] = (groups[-1][0], b)
        else:
            groups.append((a, b))
    groups = [(a + geo["axis_x"] + 1, b + geo["axis_x"] + 1) for a, b in groups if b - a > 60]
    if len(groups) != 3:
        raise SystemExit(f"found {len(groups)} bar groups, expected 3")
    # A group without its first bar (Fig. 4 has no ESR_S bar at RR 5.0) is narrower: the bars sit
    # against its right end, so take its start one full group width back from there.
    full = max(b - a + 1 for a, b in groups)
    groups = [(b - full + 1, b) if (b - a + 1) < full - 10 else (a, b) for a, b in groups]
    bars = []
    for a, b in groups:
        wbar = (b - a + 1) / 4
        bars.append([(a + i * wbar, a + (i + 1) * wbar - 1) for i in range(4)])
    return bars


def bar_top(g, geo, left, right):
    """Row of a bar's top edge (sub-pixel), or None if there is no bar (Fig. 4, ESR_S at RR 5.0)."""
    cols = range(int(np.ceil(left)) + 3, int(np.floor(right)) - 2)
    tops = []
    for c in cols:
        prof = g[geo["plot_top"] + 2:geo["axis_y"] - 1, c].astype(float)
        idx = np.nonzero(prof < 200)[0]  # first ink: a fill or a border line
        if not len(idx):
            continue
        i = idx[0]
        level = (255.0 + prof[i:i + 3].min()) / 2  # half-way to the border's darkest pixel
        while i > 0 and prof[i - 1] < level:
            i -= 1
        while prof[i] >= level:
            i += 1
        a, b = (prof[i - 1], prof[i]) if i > 0 else (255.0, prof[i])
        frac = (a - level) / (a - b) if a != b else 0.0
        tops.append(geo["plot_top"] + 2 + i - 1 + frac)
    if len(tops) < len(cols) / 2:
        return None
    return float(np.median(tops))


def read(path):
    g = np.asarray(Image.open(path).convert("L")).astype(int)
    geo = geometry(g)
    centres = tick_label_rows(g, geo)
    slope, icpt = np.polyfit(centres, LABELS, 1)  # value = slope * row + icpt
    resid = float(np.max(np.abs(np.polyval([slope, icpt], centres) - LABELS)))
    bars = bar_extents(g, geo)
    out = {"size": [int(g.shape[1]), int(g.shape[0])], "geometry": geo, "tick_rows": centres,
           "value_per_px": float(-slope), "tick_fit_max_residual": resid,
           "zero_row": float(-icpt / slope), "bars": {}}
    for grp, ext in zip(GROUPS, bars):
        for ser, (a, b) in zip(SERIES, ext):
            top = bar_top(g, geo, a, b)
            # The edge crossing sits half a pixel above the border line's centre; the axis line centre is 0.
            val = None if top is None else float(slope * (top + 0.5) + icpt)
            out["bars"][f"{grp}|{ser}"] = {"left": a, "right": b, "top_row": top, "value": val}
    return out


def main():
    fig_dir, out = sys.argv[1:3]
    res = {}
    for i in range(1, 5):
        res[f"fig{i}"] = read(Path(fig_dir) / f"1471-2288-11-1-{i}.jpg")
    Path(out).write_text(json.dumps(res, indent=1) + "\n")
    for f, r in res.items():
        vals = ", ".join(f"{k.split('|')[1][:6]}@{k.split('|')[0]} {v['value']:.4f}" if v["value"] is not None else f"{k} none"
                         for k, v in r["bars"].items())
        print(f"{f}: tick fit residual {r['tick_fit_max_residual']:.5f}; {vals}", file=sys.stderr)


if __name__ == "__main__":
    main()

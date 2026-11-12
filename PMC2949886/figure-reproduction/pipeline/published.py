"""Read the plotted values out of the authors' original figure files.

BMC serves the authors' original figures (R 2.10.0 and cairo PDFs) as
electronic supplementary material, and Figures S1 to S9 sit as vector graphics in
Additional File 1. Every curve is a path with its own coordinates, so the
plotted numbers can be read back exactly: each panel's pixel-to-data map is
fitted to its tick marks and printed tick labels (nothing inside the panel is
fitted), and each series is identified by its line style and colour.

Writes published_values.json: for each figure and panel, the axis maps (with
their fit residuals), the panel box in PDF points, and the series in data units
with their drawing style.
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pymupdf

NUM = re.compile(r"^-?\d+(\.\d+)?$")


def polyline(g):
    pts = []
    for it in g["items"]:
        if it[0] == "l":
            if not pts:
                pts.append((it[1].x, it[1].y))
            pts.append((it[2].x, it[2].y))
    return pts


def ticks_and_labels(page):
    """Tick marks (short black strokes) matched to the numeric labels next to them."""
    ticks = []
    for g in page.get_drawings():
        it = g["items"]
        if len(it) == 1 and it[0][0] == "l" and (g.get("color") or (1,))[0] == 0:
            a, b = it[0][1], it[0][2]
            if abs(a.x - b.x) < 0.01 and 2 < abs(a.y - b.y) < 9:
                ticks.append(("x", a.x, min(a.y, b.y), max(a.y, b.y)))
            elif abs(a.y - b.y) < 0.01 and 2 < abs(a.x - b.x) < 9:
                ticks.append(("y", a.y, min(a.x, b.x), max(a.x, b.x)))
    labels = []
    for w in page.get_text("words"):
        if NUM.match(w[4]):
            labels.append((float(w[4]), (w[0] + w[2]) / 2, (w[1] + w[3]) / 2))
    return ticks, labels


def fit_axis(ticks, labels, kind, lo, hi, tol=1.6, cross=None, exclude=()):
    """Linear map pixel -> data from the ticks of one axis inside [lo, hi]
    (and, when given, with the tick's other coordinate inside cross)."""
    pairs = {}
    for k, pos, c0, c1 in ticks:
        if k != kind or not (lo - 1 <= pos <= hi + 1):
            continue
        if cross and not (cross[0] <= c0 and c1 <= cross[1]):
            continue
        mid = (pos, (c0 + c1) / 2) if kind == "x" else ((c0 + c1) / 2, pos)
        if any(b[0] + 0.5 < mid[0] < b[2] - 0.5 and b[1] + 0.5 < mid[1] < b[3] - 0.5 for b in exclude):
            continue                                   # a marker stroke inside a panel, not a tick
        for val, cx, cy in labels:
            c, o = (cx, cy) if kind == "x" else (cy, cx)
            if abs(c - pos) < tol and c0 - 30 < o < c1 + 30:   # the label sits next to its tick
                pairs[round(pos, 2)] = val
    if len(pairs) < 2:
        raise ValueError(f"fewer than two labelled {kind} ticks in [{lo}, {hi}]")
    px = np.array(list(pairs.keys()))
    val = np.array(list(pairs.values()))
    A = np.vstack([px, np.ones_like(px)]).T
    coef, *_ = np.linalg.lstsq(A, val, rcond=None)
    resid = float(np.max(np.abs(A @ coef - val)))
    return {"slope": float(coef[0]), "intercept": float(coef[1]), "ticks": len(pairs),
            "max_residual": resid}


def to_data(pts, xm, ym):
    return [[xm["slope"] * x + xm["intercept"], ym["slope"] * y + ym["intercept"]] for x, y in pts]


def style(g):
    return {"color": [round(c, 3) for c in (g.get("color") or (0, 0, 0))],
            "width": g.get("width"), "dashes": g.get("dashes")}


def inside(pts, box, pad=1.0):
    x0, y0, x1, y1 = box
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs) >= x0 - pad and max(xs) <= x1 + pad and min(ys) >= y0 - pad and max(ys) <= y1 + pad


def panel_maps(page, box, xr=None, yr=None, ycross=None, xcross=None, exclude=None):
    ticks, labels = ticks_and_labels(page)
    x0, y0, x1, y1 = box
    ex = exclude or []
    xm = fit_axis(ticks, labels, "x", *(xr or (x0, x1)), cross=xcross, exclude=ex)
    ym = fit_axis(ticks, labels, "y", *(yr or (y0, y1)), cross=ycross, exclude=ex)
    return xm, ym


def lines_in(page, box, minpts=3, xonly=False):
    out = []
    for g in page.get_drawings():
        pts = polyline(g)
        if len(pts) >= minpts and inside(pts, (box[0], -1e9, box[2], 1e9) if xonly else box):
            out.append((g, pts))
    return out


DASH = {"[] 0": "solid", "[ 4.5 7.5 ] 0": "dashed", "[ 0 6 ] 0": "dotted",
        "[ 0 6 4.5 6 ] 0": "dashdot",
        # Additional File 1 figures are scaled by 0.6496
        "[ 2.923245 4.872075 ] 0": "dashed", "[ 0 3.8976598 ] 0": "dotted",
        "[ 0 3.8976598 2.923245 3.8976598 ] 0": "dashdot",
        "[ 6 6 ] 0": "dashed", "[ 1.5 4.5 ] 0": "dotted"}


def panel_record(box, xm, ym, series, styles, extra=None):
    rec = {"box": box, "x_map": xm, "y_map": ym, "series": series, "style": styles}
    if extra:
        rec.update(extra)
    return rec


# ---------------------------------------------------------------- figures

def fig1(page):
    """Two lattice panels of p-value densities; solid = fold change, dashed = no
    filter, dotted = variance filter (the caption calls the variance curve dashed)."""
    names = {"solid": "foldchange", "dashed": "none", "dotted": "variance"}
    boxes = {"null": (20.38, 38.59, 233.28, 177.2), "alternative": (233.29, 38.59, 446.19, 177.2)}
    out = {}
    for pn, box in boxes.items():
        xm, ym = panel_maps(page, box, yr=(38.59, 177.2))
        series, styles = {}, {}
        for g, pts in lines_in(page, box, minpts=50, xonly=True):
            nm = names[DASH[g["dashes"]]]
            series[nm] = to_data(pts, xm, ym)
            styles[nm] = style(g)
        out[pn] = panel_record(box, xm, ym, series, styles)
    return out


def fig2(page):
    """Histogram of each filter statistic (light blue bars), step lines for H0
    (blue) and Ha (red), and grey decile lines."""
    boxes = {"foldchange": (29.5, 20.0, 170.0, 222.5), "signal": (197.5, 20.0, 338.0, 222.5),
             "variance": (365.5, 20.0, 500.0, 222.5)}
    out = {}
    drawings = page.get_drawings()
    for pn, box in boxes.items():
        xm, ym = panel_maps(page, box, ycross=(box[0] - 8, box[0] + 1))
        series, styles, bars, deciles = {}, {}, [], []
        for g in drawings:
            col = tuple(round(c, 3) for c in (g.get("color") or ()))
            if g["type"] == "fs" and col == (0.776, 0.886, 1.0):
                r = g["rect"]
                if box[0] - 1 <= r.x0 and r.x1 <= box[2] + 1:
                    bars.append([xm["slope"] * r.x0 + xm["intercept"], xm["slope"] * r.x1 + xm["intercept"],
                                 ym["slope"] * r.y0 + ym["intercept"]])
                continue
            pts = polyline(g)
            if not pts or not inside(pts, box):
                continue
            if col == (0.745, 0.745, 0.745) and len(pts) == 2:
                deciles.append(xm["slope"] * pts[0][0] + xm["intercept"])
            elif col in ((0.212, 0.392, 0.545), (1.0, 0.271, 0.0)) and len(pts) > 10:
                nm = "null" if col[0] < 0.5 else "alternative"
                series[nm] = to_data(pts, xm, ym)
                styles[nm] = style(g)
        bars.sort()
        out[pn] = panel_record(box, xm, ym, series, styles,
                               {"histogram": bars, "deciles": sorted(deciles)})
    return out


def fig3(page):
    """pi0 against the fraction removed: solid = fold change, dashed = variance,
    dash-dot = signal, thin solid curve = best filter, thin solid frame = random."""
    box = (33.3, 12.7, 448.0, 413.4)
    xm, ym = panel_maps(page, box, yr=(80, 340))
    names = {("solid", 1.5): "foldchange", ("dashed", 1.5): "variance", ("dashdot", 1.5): "signal",
             ("solid", 0.75): "best"}
    series, styles = {}, {}
    random = []
    for g in page.get_drawings():
        pts = polyline(g)
        if not pts or not inside(pts, box):
            continue
        key = (DASH.get(g["dashes"]), g.get("width"))
        if key in names and len(pts) > 5:
            series[names[key]] = to_data(pts, xm, ym)
            styles[names[key]] = style(g)
        elif key == ("solid", 0.75) and len(pts) == 2 and (g.get("color") or (1,))[0] == 0:
            (xa, ya), (xb, yb) = pts
            if abs(ya - yb) < 0.01 and abs(xa - 58.8) < 0.5:       # pi0 = 0.8 from x = 0 to 1
                random = [(xa, ya), (xb, yb)] + random
            elif abs(xa - xb) < 0.01 and abs(xa - 422.5) < 0.5 and max(ya, yb) > 400:
                random = random + [(xb, yb)]
    series["random"] = to_data(random, xm, ym)
    styles["random"] = {"color": [0, 0, 0], "width": 0.75, "dashes": "[] 0"}
    return {"main": panel_record(box, xm, ym, series, styles)}


def fig4(page):
    """Achieved FDR against fraction removed; dashed = variance, dotted = signal,
    dash-dot = fold change (caption)."""
    boxes = {"BH": (30.52, 38.59, 232.3, 226.69), "aBH": (232.31, 38.59, 434.09, 226.69),
             "BY": (30.52, 241.1, 232.3, 429.2), "qvalue": (232.31, 241.1, 434.09, 429.2)}
    names = {"dashed": "variance", "dotted": "signal", "dashdot": "foldchange"}
    out = {}
    for pn, box in boxes.items():
        xm, ym = panel_maps(page, box)
        series, styles = {}, {}
        for g, pts in lines_in(page, box, minpts=8):
            nm = names[DASH[g["dashes"]]]
            series[nm] = to_data(pts, xm, ym)
            styles[nm] = style(g)
        out[pn] = panel_record(box, xm, ym, series, styles)
    return out


FRACTIONS = [0, .1, .2, .3, .4, .5, .6, .7, .8, .9, .99]
JET11 = [(0.0, 0.0, 0.498), (0.0, 0.0, 0.898), (0.0, 0.298, 1.0), (0.0, 0.698, 1.0), (0.098, 1.0, 0.898),
         (0.498, 1.0, 0.498), (0.898, 1.0, 0.098), (1.0, 0.698, 0.0), (1.0, 0.298, 0.0), (0.898, 0.0, 0.0),
         (0.498, 0.0, 0.0)]


def coloured_curves(page, boxes, minpts=10):
    out = {}
    for pn, box in boxes.items():
        xm, ym = panel_maps(page, box)
        series, styles = {}, {}
        for g, pts in lines_in(page, box, minpts=minpts):
            col = tuple(round(c, 3) for c in (g.get("color") or ()))
            if col in JET11:
                nm = f"{FRACTIONS[JET11.index(col)]:g}"
                series[nm] = to_data(pts, xm, ym)
                styles[nm] = style(g)
        out[pn] = panel_record(box, xm, ym, series, styles)
    return out


def fig5(page):
    """Power against the BH level; one curve per fraction removed (0 dark blue to 0.9 dark red)."""
    boxes = {"foldchange": (48.52, 39.64, 187.68, 168.2), "signal": (187.68, 39.64, 326.84, 168.2),
             "variance": (326.84, 39.64, 466.0, 168.2)}
    return coloured_curves(page, boxes)


def fig6(page):
    """FDR-bias test for the fold-change filter: boxplots of the per-permutation
    p-values, achieved-FDR lines and the test's p-value above each box."""
    box = (32.0, 25.0, 440.0, 412.6)
    ticks, labels = ticks_and_labels(page)
    ym = fit_axis(ticks, labels, "y", 40, 410)
    centres = sorted(t[1] for t in ticks if t[0] == "x" and t[2] > 410)
    fractions = [0, .1, .2, .3, .4, .5, .6, .7, .8, .9, .99]
    xm = {"slope": None, "intercept": None, "categories": dict(zip([f"{f:g}" for f in fractions], centres))}
    names = {"solid": "bonferroni", "dashed": "BH", "dotted": "BY", "dashdot": "aBH"}
    series, styles = {}, {}
    drawings = page.get_drawings()
    for g in drawings:
        pts = polyline(g)
        if len(pts) == 11 and g.get("width") == 1.5:
            nm = names[DASH[g["dashes"]]]
            series[nm] = [[f, ym["slope"] * y + ym["intercept"]] for f, (_, y) in zip(fractions, pts)]
            styles[nm] = style(g)
    # boxplot statistics: medians are the 2.25-wide strokes; boxes are the rectangles;
    # whisker ends are the short solid horizontal strokes
    med, boxes_, whisk = {}, {}, {}
    for g in drawings:
        pts = polyline(g)
        if g.get("width") == 2.25 and len(pts) == 2:
            cx = (pts[0][0] + pts[1][0]) / 2
            med[cx] = ym["slope"] * pts[0][1] + ym["intercept"]
        if len(g["items"]) == 1 and g["items"][0][0] in ("re", "qu"):
            r = g["rect"]
            if r.width < 40:
                boxes_[(r.x0 + r.x1) / 2] = (ym["slope"] * r.y1 + ym["intercept"], ym["slope"] * r.y0 + ym["intercept"])
        if g.get("width") == 0.75 and g["dashes"] == "[] 0" and len(pts) == 2 and abs(pts[0][1] - pts[1][1]) < 0.01:
            w = abs(pts[0][0] - pts[1][0])
            if 5 < w < 20:
                whisk.setdefault((pts[0][0] + pts[1][0]) / 2, []).append(ym["slope"] * pts[0][1] + ym["intercept"])

    def near(d, c):
        k = min(d, key=lambda k: abs(k - c))
        return d[k] if abs(k - c) < 2 else None

    stats = {}
    for f, c in zip(fractions, centres):
        w = sorted(near(whisk, c) or [])
        b = near(boxes_, c)
        stats[f"{f:g}"] = {"median": near(med, c), "q1": b[0] if b else None, "q3": b[1] if b else None,
                           "whisker_low": w[0] if w else None, "whisker_high": w[-1] if w else None}
    top = sorted([(w[0], w[4]) for w in page.get_text("words") if w[1] < 45 and (w[4] == "***" or NUM.match(w[4]))])
    tests = dict(zip([f"{f:g}" for f in fractions], [t[1] for t in top]))
    return {"foldchange": panel_record(box, xm, ym, series, styles, {"boxplots": stats, "test_labels": tests})}


def segment_series(page, box, xm, ym, xs, width, min_y):
    """Series drawn by cairo as separate segments between markers (R type 'b'):
    colour gives the filter, dash pattern the subset size; each point is read off
    the lines through the segments."""
    colours = {(0.0, 0.0, 0.0): "foldchange", (1.0, 0.0, 0.0): "variance", (0.0, 1.0, 0.0): "signal"}
    sizes = {"solid": "24", "dashed": "16", "dotted": "8"}
    xs_px = [(f - xm["intercept"]) / xm["slope"] for f in xs]
    segs = {}
    for g in page.get_drawings():
        col = tuple(round(c, 3) for c in (g.get("color") or ()))
        if g.get("width") is None or abs(g["width"] - width) > 0.01 or col not in colours:
            continue
        it = g["items"]
        if len(it) == 1 and it[0][0] == "l":
            a, b = it[0][1], it[0][2]
            if abs(a.x - b.x) > 6 and min(a.y, b.y) > min_y and box[0] <= min(a.x, b.x) and max(a.x, b.x) <= box[2]:
                key = (colours[col], sizes[DASH[g["dashes"]]])
                segs.setdefault(key, []).append(((a.x, a.y), (b.x, b.y)))
    series, styles = {}, {}
    for (filt, n), ss in segs.items():
        vals = {i: [] for i in range(len(xs_px))}
        for (xa, ya), (xb, yb) in ss:
            if xa > xb:
                xa, ya, xb, yb = xb, yb, xa, ya
            i = max(k for k, x in enumerate(xs_px[:-1]) if x <= xa + 0.5) if xa + 0.5 >= xs_px[0] else 0
            s_ = (yb - ya) / (xb - xa)
            vals[i].append(ya + s_ * (xs_px[i] - xa))
            vals[i + 1].append(ya + s_ * (xs_px[i + 1] - xa))
        pts = [[float(xs[i]), ym["slope"] * float(np.mean(v)) + ym["intercept"]] for i, v in vals.items() if v]
        nm = f"{filt}.n{n}"
        series[nm] = pts
        styles[nm] = {"color": [c for c, f in colours.items() if f == filt][0], "width": width,
                      "dashes": [k for k, v in DASH.items() if v == {"24": "solid", "16": "dashed", "8": "dotted"}[n]
                                 and (k.startswith("[ 6") or k.startswith("[ 1.5") or k == "[] 0")][0]}
    return series, styles


def fig7(page):
    """Leukemia subsets: achieved FDR against fraction removed; black circles =
    fold change, red triangles = variance, green plus = signal; solid n = 24,
    dashed n = 16, dotted n = 8."""
    box = (32.0, 10.0, 480.0, 300.4)
    xm, ym = panel_maps(page, box, yr=(15, 295))
    series, styles = segment_series(page, box, xm, ym, [round(0.1 * i, 1) for i in range(10)], 1.5, 60)
    return {"main": panel_record(box, xm, ym, series, styles)}


def s5(page):
    """Leukemia subsets: power against fraction removed (Additional File 1, Figure 5)."""
    box = (175.0, 150.0, 455.0, 388.6)
    xm, ym = panel_maps(page, box, yr=(150, 385))
    series, styles = segment_series(page, box, xm, ym, [round(0.1 * i, 1) for i in range(10)], 0.974, 150)
    return {"main": panel_record(box, xm, ym, series, styles)}


def lattice_lines(page, boxes, names, minpts=8):
    out = {}
    for pn, box in boxes.items():
        xm, ym = panel_maps(page, box, exclude=list(boxes.values()))
        series, styles = {}, {}
        for g, pts in lines_in(page, box, minpts=minpts):
            nm = names.get(DASH.get(g["dashes"]))
            if nm:
                series[nm] = to_data(pts, xm, ym)
                styles[nm] = style(g)
        out[pn] = panel_record(box, xm, ym, series, styles)
    return out


def s2(page):
    """Power against fraction removed, four FDR methods (Additional File 1, Figure 2)."""
    boxes = {"BH": (179.5, 145.6, 310.6, 267.8), "aBH": (310.6, 145.6, 441.7, 267.8),
             "BY": (179.5, 277.2, 310.6, 399.4), "qvalue": (310.6, 277.2, 441.7, 399.4)}
    return lattice_lines(page, boxes, {"dashed": "variance", "dotted": "signal", "dashdot": "foldchange"})


def s3(page):
    """Power against achieved FDR over BH levels, one curve per fraction (Additional File 1, Figure 3)."""
    boxes = {"foldchange": (179.5, 152.2, 269.9, 235.7), "signal": (269.9, 152.2, 360.3, 235.7),
             "variance": (360.3, 152.2, 450.7, 235.7)}
    return coloured_curves(page, boxes, minpts=5)


def s4(page):
    """FDR-bias test, all three filters (Additional File 1, Figure 4): boxplots,
    achieved-FDR lines (BH red, aBH blue, q-value cyan, BY green, Bonferroni black)
    and the test p-values above the panels."""
    out = {}
    cols = {(0.0, 0.0, 0.0): "bonferroni", (1.0, 0.0, 0.0): "BH", (0.0, 0.804, 0.0): "BY",
            (0.0, 0.0, 1.0): "aBH", (0.0, 1.0, 1.0): "qvalue"}
    ticks, labels = ticks_and_labels(page)
    for pn, x0 in (("variance", 174.1), ("signal", 283.2), ("foldchange", 392.3)):
        box = (x0 - 14, 140.0, x0 + 84, 400.0)
        ym = fit_axis(ticks, labels, "y", 140, 400, cross=(x0 - 40, x0 - 4))
        cats = [x0 + 7.0 * k for k in range(11)]
        xm = {"slope": None, "intercept": None, "categories": dict(zip([f"{f:g}" for f in FRACTIONS], cats))}
        series, styles = {}, {}
        for g, pts in lines_in(page, box, minpts=9):
            col = tuple(round(c, 3) for c in (g.get("color") or ()))
            if col in cols and abs(g.get("width", 0) - 0.974) < 0.01:
                nm = cols[col]
                series[nm] = [[FRACTIONS[int(round((x - x0) / 7.0))], ym["slope"] * y + ym["intercept"]] for x, y in pts]
                styles[nm] = style(g)
        med = {}
        for g in page.get_drawings():
            pts = polyline(g)
            if g.get("width") and abs(g["width"] - 1.4616) < 0.01 and len(pts) == 2 and box[0] <= pts[0][0] <= box[2]:
                c = (pts[0][0] + pts[1][0]) / 2
                med[f"{FRACTIONS[int(round((c - x0) / 7.0))]:g}"] = ym["slope"] * pts[0][1] + ym["intercept"]
        top = sorted([(w[0], w[4]) for w in page.get_text("words")
                      if 125 < w[1] < 142 and box[0] <= w[0] <= box[2]])
        out[pn] = panel_record(box, xm, ym, series, styles, {"medians": med, "test_labels": [t[1] for t in top]})
    return out


def s6(page):
    """Wilcoxon rank-sum test with BH: FDR (left) and power (right) against fraction removed."""
    boxes = {"fdr": (183.1, 131.6, 287.0, 235.7), "power": (343.2, 131.6, 450.7, 235.7)}
    names = {"solid": "foldchange", "dashed": "signal", "dotted": "variance"}
    out = {}
    for pn, box in boxes.items():                   # two base-graphics plots, each with its own y axis
        xm, ym = panel_maps(page, box, ycross=(box[0] - 5, box[0] + 0.5), xcross=(box[3] - 0.5, box[3] + 5))
        series, styles = {}, {}
        for g, pts in lines_in(page, box, minpts=8):
            nm = names.get(DASH.get(g["dashes"]))
            if nm:
                series[nm] = to_data(pts, xm, ym)
                styles[nm] = style(g)
        out[pn] = panel_record(box, xm, ym, series, styles)
    return out


def regression_lines(page, boxes):
    """Least-squares lines drawn over scatter plots: intercept and slope per colour."""
    cols = {(1.0, 0.0, 0.0): "B25", (0.0, 1.0, 0.0): "B50", (0.0, 0.0, 1.0): "C10", (0.0, 0.0, 0.0): "C20"}
    out = {}
    for pn, box in boxes.items():
        xm, ym = panel_maps(page, box, xcross=(box[1] - 15, box[3] + 15), exclude=list(boxes.values()))
        lines = {}
        for g in page.get_drawings():
            col = tuple(round(c, 3) for c in (g.get("color") or ()))
            pts = polyline(g)
            if col in cols and len(pts) == 2 and abs(g.get("width", 0) - 0.487) < 0.01 and inside(pts, box, 2) \
                    and abs(pts[0][0] - pts[1][0]) > 20:
                (xa, ya), (xb, yb) = to_data(pts, xm, ym)
                slope = (yb - ya) / (xb - xa)
                lines[cols[col]] = {"intercept": ya - slope * xa, "slope": slope, "x": [xa, xb]}
        out[pn] = panel_record(box, xm, ym, {}, {}, {"lines": lines})
    return out


def s8(page):
    """Achieved FDR with filtering before (B) or after (C) the correction against none (A)."""
    return regression_lines(page, {"foldchange": (183.1, 145.6, 272.3, 235.7), "signal": (272.3, 145.6, 361.5, 235.7),
                                   "variance": (361.5, 145.6, 450.7, 235.7)})


def s9(page):
    """Power with filtering before (B) or after (C) the correction against none (A)."""
    return regression_lines(page, {"foldchange": (183.1, 381.0, 272.3, 471.0), "signal": (272.3, 381.0, 361.5, 471.0),
                                   "variance": (361.5, 381.0, 450.7, 471.0)})


FIGURES = {"fig1": ("MOESM2.pdf", 0, fig1), "fig2": ("MOESM3.pdf", 0, fig2), "fig3": ("MOESM4.pdf", 0, fig3),
           "fig4": ("MOESM5.pdf", 0, fig4), "fig5": ("MOESM6.pdf", 0, fig5), "fig6": ("MOESM7.pdf", 0, fig6),
           "fig7": ("MOESM8.pdf", 0, fig7),
           "figS2": ("MOESM1.PDF", 10, s2), "figS3": ("MOESM1.PDF", 11, s3), "figS4": ("MOESM1.PDF", 13, s4),
           "figS5": ("MOESM1.PDF", 14, s5), "figS6": ("MOESM1.PDF", 15, s6), "figS8": ("MOESM1.PDF", 18, s8),
           "figS9": ("MOESM1.PDF", 18, s9)}


def read_all(src):
    out = {}
    for fid, (fn, pg, fun) in FIGURES.items():
        doc = pymupdf.open(Path(src) / fn)
        out[fid] = {"file": fn, "page": pg, "size": [doc[pg].rect.width, doc[pg].rect.height],
                    "panels": fun(doc[pg])}
    return out


if __name__ == "__main__":
    src, dest = sys.argv[1], sys.argv[2]
    vals = read_all(src)
    Path(dest).write_text(json.dumps(vals, indent=1))
    for fid, f in vals.items():
        for pn, p in f["panels"].items():
            print(fid, pn, {k: len(v) for k, v in p["series"].items()},
                  "resid", round(p["x_map"].get("max_residual") or 0, 4), round(p["y_map"]["max_residual"], 4))

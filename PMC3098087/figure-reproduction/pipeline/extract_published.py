#!/usr/bin/env python3
"""Read the published values of PMC3098087 out of the paper and its supplements.

  extract_published.py DOWNLOADS OUT.json

- Figs 1-6 (paper PDF, vector): every plotted marker, mapped to data through the axis ticks.
- Additional files 4, 5, 8, 10, 11 and 12 (vector PDFs): the vertices of every coloured polyline
  (the lines join the plotted means), mapped through the axis ticks and their printed labels.
- Additional files 1, 3, 13 and 14: the printed tables (means and SDs) from the PDF text.

The paper's figure text is outlined, so its tick values are given below, read from the printed
tick labels; the supplements' tick labels are text and are read from the PDF.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vector_points as vp  # noqa: E402

NINE = ["1-NN", "3-NN", "5-NN", "DLDA", "DQDA", "RF", "SVM", "PAM", "PLR"]
K19 = [round(0.05 * i, 2) for i in range(1, 20)]
RED, BLUE, MAGENTA, PURPLE, ORANGE, BLACK = (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 1.0), \
    (0.816, 0.125, 0.565), (1.0, 0.647, 0.0), (0.0, 0.0, 0.0)
PA_SERIES = {(RED, True): "PA", (PURPLE, False): "PA1", (BLUE, False): "PA2"}
P_SERIES = {RED: 40, BLUE: 1000, MAGENTA: 10000}
K_SERIES = {RED: 0.5, BLUE: 0.6, ORANGE: 0.7, BLACK: 0.8, MAGENTA: 0.9}
PAPER = "PMC3098087.1.pdf"


def snap(x, grid, tol=0.004):
    g = min(grid, key=lambda v: abs(v - x))
    if abs(g - x) > tol:
        raise ValueError(f"x = {x:.4f} is not on the grid")
    return g


def records_from_markers(fig, panels, panel_meta, series_of, xgrid, xfix=None):
    out = []
    for k, p in enumerate(panels):
        meta = panel_meta(k)
        groups = {}
        skipped = 0
        for pt in p["points"]:
            key = series_of(pt)
            if key is None:
                raise ValueError(f"{fig} panel {k}: unknown marker {pt['colour']} filled={pt['filled']}")
            x = xfix(pt["x"]) if xfix else pt["x"]
            try:
                gx = snap(x, xgrid)
            except ValueError:  # a legend marker drawn at the data size, off the grid
                skipped += 1
                continue
            groups.setdefault(tuple(sorted(key.items())), []).append([gx, round(pt["y"], 5)])
        for key, pts in groups.items():
            pts.sort()
            xs = [a for a, _ in pts]
            if len(set(xs)) != len(xs):
                raise ValueError(f"{fig} panel {k} series {key}: two points at one x")
            out.append(dict(figure=fig, **meta, **dict(key), points=pts, legend_markers_skipped=skipped,
                            box=p["box"], map=[round(v, 8) for v in p["map"]],
                            x_residual=p["x_residual"], y_residual=p["y_residual"]))
    return out


def main_figures(pdf):
    doc = pymupdf.open(pdf)
    recs = []
    t01 = [0, .2, .4, .6, .8, 1]
    k9 = [round(.1 * i, 1) for i in range(1, 10)]
    # Fig. 1 (page 4): null, p = 40, G = p, test imbalance as training (20 samples).
    p = vp.read_page(doc[3], k9, t01)
    recs += records_from_markers("fig1", p, lambda k: {"classifier": NINE[k]},
                                 lambda m: {"metric": PA_SERIES.get((m["colour"], m["filled"]))}
                                 if (m["colour"], m["filled"]) in PA_SERIES else None, K19)
    # Fig. 2 (page 5): null, G = 40, PA1, p = 40 / 1000 / 10000.
    p = vp.read_page(doc[4], t01, t01)
    recs += records_from_markers("fig2", p, lambda k: {"classifier": NINE[k], "metric": "PA1"},
                                 lambda m: {"p": P_SERIES[m["colour"]]} if m["colour"] in P_SERIES else None, K19)
    # Fig. 3 (page 6): alternative, mu2 = 1, PA1; left pDE = 20, right pDE = p (x axis broken at 0.5).
    p = vp.read_page(doc[5], lambda k: t01 if k % 2 == 0 else [0, .1, .2, .3, .4, .5, .6], t01)
    rows = ["1-NN", "DLDA", "PLR"]
    for k, panel in enumerate(p):
        right = k % 2 == 1
        recs += records_from_markers(
            "fig3", [panel], lambda _k, k=k, right=right: {"classifier": rows[k // 2], "metric": "PA1",
                                                         "p_de": "p" if right else 20},
            lambda m: {"p": P_SERIES[m["colour"]]} if m["colour"] in P_SERIES else None,
            K19 if not right else [round(.05 * i, 2) for i in range(1, 11)] + [0.95],
            xfix=(lambda x: 0.95 if x > 0.55 else x) if right else None)
    # Fig. 4 (page 8): PA against mu2, k1train 0.5-0.9; left samples, right variables centred.
    mu = [0.0] + [round(.1 * i, 1) for i in range(1, 21)] + [3.0]
    p = vp.read_page(doc[7], [0, .5, 1, 1.5, 2, 2.5, 3], [.4, .6, .8, 1])
    for k, panel in enumerate(p):
        recs += records_from_markers(
            "fig4", [panel], lambda _k, k=k: {"classifier": rows[k // 2], "metric": "PA",
                                            "center": "samples" if k % 2 == 0 else "variables"},
            lambda m: {"k1train": K_SERIES[m["colour"]]} if m["colour"] in K_SERIES else None, mu)
    # Fig. 5 (page 9): corrections, p = 1000; rows 3-NN, DLDA, PLR; columns none, over, down, MultDS.
    p = vp.read_page(doc[8], k9, t01)
    corr = ["none", "over", "down", "multds"]
    rows5 = ["3-NN", "DLDA", "PLR"]
    recs += records_from_markers("fig5", p, lambda k: {"classifier": rows5[k // 4], "correction": corr[k % 4]},
                                 lambda m: {"metric": PA_SERIES[(m["colour"], m["filled"])]}
                                 if (m["colour"], m["filled"]) in PA_SERIES else None, K19)
    recs += fig6(doc[9])
    return recs


def fig6(page):
    """Fig. 6: class-specific PA (%) with 95% prediction intervals, two stacked sub-panels per box."""
    out = []
    lines = vp._black_lines(page)
    rows = ["3-NN", "DLDA", "PLR"]
    allx = [50 + 5 * i for i in range(10)]
    for k, box in enumerate(vp.panels(page)):
        xt, yt = vp.ticks(box, lines)
        ax, bx, rx = vp._fit(list(zip(xt, allx)))
        lower, upper = yt[:11], yt[11:]  # bottom sub-panel first (yt runs bottom to top)
        maps = {10: vp._fit(list(zip(lower, range(0, 101, 10)))), 5: vp._fit(list(zip(upper, range(0, 101, 10))))}
        split = (lower[-1] + upper[0]) / 2
        draws = page.get_drawings()
        gl = vp.glyphs(page)
        segs = []
        for d in draws:
            if d["type"] == "s" and d.get("dashes") in (None, "[] 0") and box.contains(d["rect"]):
                col = vp._rgb(d.get("color"))
                for it in d["items"]:
                    if it[0] == "l" and abs(it[1].x - it[2].x) < 0.05 and abs(it[1].y - it[2].y) > 0.3:
                        segs.append((col, it[1].x, min(it[1].y, it[2].y), max(it[1].y, it[2].y)))
        for m in vp.markers(page, box, gl):
            sub = 5 if m["cy"] < split else 10
            ay, by, ry = maps[sub]
            col = m["colour"]
            if col not in (RED, BLACK):
                continue
            top, bottom = (box.y0, split) if sub == 5 else (split, box.y1)
            mine = [s for s in segs if s[0] == col and abs(s[1] - m["cx"]) < 0.3 and s[2] >= top - 0.5 and s[3] <= bottom + 0.5]
            lo_px = max(s[3] for s in mine) if mine else None
            hi_px = min(s[2] for s in mine) if mine else None
            out.append({"figure": "fig6", "classifier": rows[k // 2], "center": "samples" if k % 2 == 0 else "variables",
                        "n_neg": sub, "correction": "multds" if col == RED else "none",
                        "metric": "PA_ER+" if not m["filled"] else "PA_ER-",
                        "x_pos": round(ax + bx * m["cx"], 2),
                        "value": round(ay + by * m["cy"], 3),
                        "lo": round(ay + by * lo_px, 3) if lo_px else None,
                        "hi": round(ay + by * hi_px, 3) if hi_px else None,
                        "y_residual": ry, "x_residual": rx, "box": [round(v, 3) for v in box],
                        "map": [round(v, 8) for v in (ax, bx, ay, by)]})
    # Each point's ER+ count: points are drawn in order of ER+ share; map positions to settings.
    shares = {5: [5, 10, 20, 30, 45], 10: [10, 20, 30, 45]}
    for r in out:
        n_pos = shares[r["n_neg"]]
        nominal = [100 * a / (a + r["n_neg"]) for a in n_pos]
        r["n_pos"] = n_pos[min(range(len(nominal)), key=lambda i: abs(nominal[i] - r["x_pos"]))]
    return out


# ---- supplements: polylines and text tick labels ----

def supp_axis(page, box, lines, words, xfix=None):
    xt, yt = vp.ticks(box, lines)
    xl, yl = [], []
    for w in words:
        x0, y0, x1, y1, t = w[:5]
        if not re.match(r"^-?\d+(\.\d+)?$", t):
            continue
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        if y0 >= box.y1 and y0 - box.y1 < 16 and xt and min(abs(v - cx) for v in xt) < 3:
            xl.append((min(xt, key=lambda v: abs(v - cx)), float(t)))
        if x1 <= box.x0 and box.x0 - x1 < 16 and yt and min(abs(v - cy) for v in yt) < 3:
            yl.append((min(yt, key=lambda v: abs(v - cy)), float(t)))
    xl = sorted(set(xl))
    if xfix:
        xl = xfix(xl)
    return vp._fit(xl), vp._fit(sorted(set(yl)))


def polylines(page, box):
    """Coloured stroked paths inside a box: list of (colour, [(x, y), ...])."""
    out = []
    for d in page.get_drawings():
        col = vp._rgb(d.get("color"))
        if d["type"] != "s" or col in (None, BLACK) or col[0] == col[1] == col[2]:
            continue
        if not box.contains(d["rect"]):
            continue
        pts = []
        for it in d["items"]:
            if it[0] != "l":
                break
            if not pts:
                pts.append((it[1].x, it[1].y))
            pts.append((it[2].x, it[2].y))
        if len(pts) >= 3:
            out.append((col, pts))
    return out


SUPP_COLOURS = {RED: "PA", PURPLE: "PA1", BLUE: "PA2"}


def near_colour(col, table, tol=0.02):
    for c, v in table.items():
        if col and all(abs(a - b) <= tol for a, b in zip(col, c)):
            return v
    return None


def glyph_markers(page, box):
    """ZapfDingbats marker characters inside a box: (colour, centre x, centre y)."""
    out = []
    for b in page.get_text("rawdict")["blocks"]:
        for ln in b.get("lines", []):
            for sp in ln["spans"]:
                if sp["font"] != "ZapfDingbats":
                    continue
                c = sp["color"]
                col = (round(((c >> 16) & 255) / 255, 3), round(((c >> 8) & 255) / 255, 3), round((c & 255) / 255, 3))
                for ch in sp["chars"]:
                    if ch["c"].strip() == "":
                        continue
                    x0, y0, x1, y1 = ch["bbox"]
                    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                    if box.x0 <= cx <= box.x1 and box.y0 <= cy <= box.y1:
                        out.append((col, cx, cy))
    return out


def glyph_offset(page, boxes, table=None, lined=("PA1", "PA2")):
    """The glyph box centre is not the plotted point: the offset is the median distance between the
    glyphs of the series that have lines and the vertices of their own polylines."""
    table = table or SUPP_COLOURS
    dx, dy = [], []
    for box in boxes:
        verts = {}
        for col, pts in polylines(page, box):
            verts.setdefault(near_colour(col, table), []).extend(pts)
        for col, cx, cy in glyph_markers(page, box):
            m = near_colour(col, table)
            if m in lined and verts.get(m):
                vx, vy = min(verts[m], key=lambda v: (v[0] - cx) ** 2 + (v[1] - cy) ** 2)
                if abs(vx - cx) < 2 and abs(vy - cy) < 3:
                    dx.append(cx - vx)
                    dy.append(cy - vy)
    dx.sort()
    dy.sort()
    return dx[len(dx) // 2], dy[len(dy) // 2], len(dx)


def supplements(supp):
    recs = af12(pymupdf.open(supp / "1471-2105-11-523-S12.PDF")[0])
    k_grid = K19
    # Additional file 4 (Fig. 3 left, all nine) and 5 (Fig. 3 right): PA1 by p.
    for af, p_de in ((4, 20), (5, "p")):
        page = pymupdf.open(supp / f"1471-2105-11-523-S{af}.PDF")[0]
        lines, words = vp._black_lines(page), page.get_text("words")
        for box in vp.panels(page):
            name = vp.titles(page, box, 40).split()[-1].replace("−", "-")
            fix = None
            if af == 5:
                fix = lambda xl: [(px, v) for px, v in xl if v <= 0.5]  # noqa: E731
            (ax, bx, rx), (ay, by, ry) = supp_axis(page, box, lines, words, fix)
            grid = k_grid if af == 4 else [round(.05 * i, 2) for i in range(1, 11)] + [0.95]
            for col, pts in polylines(page, box):
                if col not in P_SERIES:
                    continue
                xy = [[snap(0.95 if (ax + bx * x) > 0.55 else ax + bx * x, grid), round(ay + by * y, 5)] for x, y in pts]
                recs.append({"figure": f"af{af}", "classifier": name, "metric": "PA1", "p_de": p_de,
                             "p": P_SERIES[col], "points": xy, "x_residual": rx, "y_residual": ry,
                             "box": [round(v, 3) for v in box], "map": [round(v, 8) for v in (ax, bx, ay, by)]})
    # Additional file 7 (Fig. 4, all nine): PA against mu2 for k1train 0.5-0.9; the lines join the means.
    mu = [0.0] + [round(.1 * i, 1) for i in range(1, 21)] + [3.0]
    page = pymupdf.open(supp / "1471-2105-11-523-S7.PDF")[0]
    lines, words = vp._black_lines(page), page.get_text("words")
    off7 = glyph_offset(page, vp.panels(page), K_SERIES, (0.6, 0.7, 0.8, 0.9))
    for k, box in enumerate(vp.panels(page)):
        row, col = divmod(k, 6)
        name = NINE[3 * row + col % 3]
        center = "samples" if col < 3 else "variables"
        (ax, bx, rx), (ay, by, ry) = supp_axis(page, box, lines, words)
        verts = {}
        for d in page.get_drawings():
            c = vp._rgb(d.get("color"))
            if d["type"] != "s" or c not in K_SERIES or not box.contains(d["rect"]):
                continue
            for it in d["items"]:
                if it[0] == "l":
                    for pt in (it[1], it[2]):
                        x = ax + bx * pt.x
                        if min(abs(x - g) for g in mu) < 0.01:
                            verts.setdefault(c, {})[snap(x, mu, 0.01)] = round(ay + by * pt.y, 5)
        # k1train = 0.5 (red) has markers but no line: read its marker glyphs.
        if RED not in verts:
            for col, cx, cy in glyph_markers(page, box):
                if near_colour(col, {RED: 1}) and min(abs(ax + bx * (cx - off7[0]) - g) for g in mu) < 0.012:
                    verts.setdefault(RED, {})[snap(ax + bx * (cx - off7[0]), mu, 0.012)] = round(ay + by * (cy - off7[1]), 5)
        for c, pts in verts.items():
            recs.append({"figure": "af7", "classifier": name, "center": center, "k1train": K_SERIES[c], "metric": "PA",
                         "points": sorted([x, y] for x, y in pts.items()), "x_residual": rx, "y_residual": ry,
                         "box": [round(v, 3) for v in box], "map": [round(v, 8) for v in (ax, bx, ay, by)]})
    # Additional file 9 (page 2): over-sampling with centred variables; columns k1test = 0.5 and
    # k1test = k1train for each classifier, four panels to a row. PA1 and PA2 are polylines; PA, drawn
    # dotted, is not read.
    page = pymupdf.open(supp / "1471-2105-11-523-S9.PDF")[1]
    lines = vp._black_lines(page)
    k9 = [round(.1 * i, 1) for i in range(1, 10)]
    for k, box in enumerate(vp.panels(page, 20)):
        name = NINE[k // 2]
        test = "bal20" if k % 2 == 0 else "match20"
        xt, yt = vp.ticks(box, lines)
        (ax, bx, rx), (ay, by, ry) = vp._fit(list(zip(xt, k9))), vp._fit(list(zip(yt, [0, .2, .4, .6, .8, 1])))
        verts = {}
        for d in page.get_drawings():
            c = near_colour(vp._rgb(d.get("color")), SUPP_COLOURS)
            if d["type"] != "s" or c is None or not box.contains(d["rect"]):
                continue
            for it in d["items"]:
                if it[0] == "l":
                    for pt in (it[1], it[2]):
                        x = ax + bx * pt.x
                        if min(abs(x - g) for g in K19) < 0.006:
                            verts.setdefault(c, {})[snap(x, K19, 0.006)] = round(ay + by * pt.y, 5)
        for c, pts in verts.items():
            if c == "PA":  # PA is drawn dotted and only partly recoverable; PA1 and PA2 are complete
                continue
            recs.append({"figure": "af9", "classifier": name, "test": test, "metric": c,
                         "points": sorted([x, y] for x, y in pts.items()), "x_residual": rx, "y_residual": ry,
                         "box": [round(v, 3) for v in box], "map": [round(v, 8) for v in (ax, bx, ay, by)], "page": 1})
    # Additional file 6 (no variable selection, Fig. 5 first column, all nine), 8 (Fig. 5, all nine),
    # 10 (ntest = 500, DLDA, RF, PLR) and 11 (RF/PLR-THR).
    for af in (6, 8, 10, 11):
        page = pymupdf.open(supp / f"1471-2105-11-523-S{af}.PDF")[0]
        lines, words = vp._black_lines(page), page.get_text("words")
        boxes = vp.panels(page)
        ncol = 4 if af in (8, 10) else 2
        off = glyph_offset(page, boxes) if af != 10 else None
        for k, box in enumerate(boxes):
            name = vp.titles(page, box, 40).split()[-1].replace("−", "-")
            if af == 8 and k < 4:
                name = "1-NN"
            if af == 10 and k < 4:
                name = "3-NN"
            if af == 11:
                name = name + "-THR"
            corr = ["none", "over", "down", "multds"][k % 4] if ncol == 4 else "none"
            (ax, bx, rx), (ay, by, ry) = supp_axis(page, box, lines, words)
            if af == 10:
                recs += pi_bars(page, box, lines, name, corr, (ax, bx, rx), (ay, by, ry))
                continue
            # PA has no line: its points are the red marker glyphs, shifted by the calibrated offset.
            pa = sorted((ax + bx * (cx - off[0]), ay + by * (cy - off[1]))
                        for col, cx, cy in glyph_markers(page, box) if near_colour(col, SUPP_COLOURS) == "PA")
            pa = [[snap(x, k_grid, 0.006), round(y, 5)] for x, y in pa if min(abs(x - g) for g in k_grid) < 0.006]
            if pa:
                recs.append({"figure": f"af{af}", "classifier": name, "correction": corr, "metric": "PA",
                             "points": pa, "x_residual": rx, "y_residual": ry, "from": "marker glyphs",
                             "box": [round(v, 3) for v in box], "map": [round(v, 8) for v in (ax, bx, ay, by)],
                             "glyph_offset_pt": [round(off[0], 3), round(off[1], 3)]})
            for col, pts in polylines(page, box):
                metric = near_colour(col, SUPP_COLOURS)
                if metric is None:
                    continue
                xy = [[snap(ax + bx * x, k_grid), round(ay + by * y, 5)] for x, y in pts]
                recs.append({"figure": f"af{af}", "classifier": name, "correction": corr,
                             "metric": metric, "points": xy, "x_residual": rx, "y_residual": ry,
                             "box": [round(v, 3) for v in box], "map": [round(v, 8) for v in (ax, bx, ay, by)]})
    return recs


def pi_bars(page, box, lines, name, corr, xmap, ymap):
    """Additional file 10: a black vertical bar per k1train, from the 2.5th to the 97.5th percentile."""
    (ax, bx, rx), (ay, by, ry) = xmap, ymap
    bars = {}
    for x0, y0, x1, y1 in lines:
        if abs(x0 - x1) < 0.05 and abs(y1 - y0) > 0.05 and box.x0 + 1 < x0 < box.x1 - 1 and box.y0 - 0.5 <= min(y0, y1) and max(y0, y1) <= box.y1 + 0.5:
            x = ax + bx * x0
            if min(abs(x - g) for g in K19) < 0.006:
                g = snap(x, K19, 0.006)
                lo, hi = ay + by * max(y0, y1), ay + by * min(y0, y1)
                b = bars.setdefault(g, [lo, hi])
                b[0], b[1] = min(b[0], lo), max(b[1], hi)
    pts = [[g, round(v[0], 5), round(v[1], 5)] for g, v in sorted(bars.items())]
    return [{"figure": "af10", "classifier": name, "correction": corr, "metric": "PA_PI",
             "points": pts, "x_residual": rx, "y_residual": ry, "box": [round(v, 3) for v in box],
             "map": [round(v, 8) for v in (ax, bx, ay, by)]}] if pts else []


def af12(page):
    """Additional file 12: Fig. 6 for all nine classifiers. Only the prediction-interval bars are read
    (the means are printed in Additional files 13 and 14). Bars come in pairs at each design, ER+
    (left) then ER-; black is no correction, red MultDS. Panels: three rows of six, the first three
    columns centred samples, the last three centred variables."""
    out = []
    lines = vp._black_lines(page)
    words = page.get_text("words")
    allx = [50 + 5 * i for i in range(10)]
    for k, box in enumerate(vp.panels(page)):
        row, col = divmod(k, 6)
        cl = NINE[3 * row + col % 3]
        center = "samples" if col < 3 else "variables"
        xt, yt = vp.ticks(box, lines)
        ax, bx, rx = vp._fit(list(zip(xt, allx)))
        lower, upper = yt[:11], yt[11:]
        maps = {10: vp._fit(list(zip(lower, range(0, 101, 10)))), 5: vp._fit(list(zip(upper, range(0, 101, 10))))}
        split = (lower[-1] + upper[0]) / 2
        bars = {}
        for d in page.get_drawings():
            col_ = vp._rgb(d.get("color"))
            if d["type"] != "s" or col_ not in (RED, BLACK) or d.get("dashes") not in (None, "[] 0") or not box.contains(d["rect"]):
                continue
            for it in d["items"]:
                if it[0] == "l" and abs(it[1].x - it[2].x) < 0.05 and abs(it[1].y - it[2].y) > 0.3 and box.x0 + 1 < it[1].x < box.x1 - 1:
                    y0, y1 = sorted((it[1].y, it[2].y))
                    sub = 5 if y1 <= split + 0.5 else 10
                    b = bars.setdefault((col_, sub, round(it[1].x, 1)), [y0, y1])
                    b[0], b[1] = min(b[0], y0), max(b[1], y1)
        for (col_, sub) in {(c, s_) for c, s_, _ in bars}:
            xs = sorted(x for c, s_, x in bars if c == col_ and s_ == sub)
            ay, by, ry = maps[sub]
            pairs = []
            i = 0
            while i < len(xs) - 1:
                if xs[i + 1] - xs[i] < 3.0:
                    pairs.append((xs[i], xs[i + 1]))
                    i += 2
                else:
                    i += 1
            shares = {5: [5, 10, 20, 30, 45], 10: [10, 20, 30, 45]}[sub]
            nominal = [100 * a / (a + sub) for a in shares]
            for xa, xb in pairs:
                xpos = ax + bx * (xa + xb) / 2
                n_pos = shares[min(range(len(nominal)), key=lambda j: abs(nominal[j] - xpos))]
                for x_, metric in ((xa, "PA_ER+"), (xb, "PA_ER-")):
                    y0, y1 = bars[(col_, sub, x_)]
                    out.append({"figure": "af12", "classifier": cl, "center": center, "n_neg": sub, "n_pos": n_pos,
                                "correction": "multds" if col_ == RED else "none", "metric": metric,
                                "lo": round(ay + by * y1, 3), "hi": round(ay + by * y0, 3), "x_pos": round(xpos, 2),
                                "box": [round(v, 3) for v in box], "map": [round(v, 8) for v in (ax, bx, ay, by)],
                                "y_residual": ry, "x_residual": rx})
    return out


# ---- tables ----

NUMTOK = re.compile(r"^\(?(-?\d+(\.\d+)?|NA|NaN)\)?$")


def table_lines(pdf):
    """Lines of the table as printed (pdftotext -layout; the pages are rotated, so PyMuPDF's
    word order does not follow the rows)."""
    txt = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], check=True, capture_output=True,
                         text=True).stdout
    return [ln.split() for ln in txt.splitlines()]


def parse_sim_table(pdf, af):
    """Additional files 1 and 3: k1train, ntest, then PA, PA1, PA2, PV1, PV2, AUC for three classifiers."""
    metrics = ["PA", "PA1", "PA2", "PV1", "PV2", "AUC"]
    cells, block, k1 = [], -1, None
    last = None
    for toks in table_lines(pdf):
        if any(t.replace("−", "-") in NINE for t in toks):
            block += 1
            continue
        if not toks or not all(NUMTOK.match(t) for t in toks):
            continue
        if toks[0].startswith("("):
            if last is None or len(toks) != 18:
                continue
            for j, t in enumerate(toks):
                last[j]["sd"] = t.strip("()")
            last = None
            continue
        if len(toks) == 20:
            k1, ntest, vals = toks[0], toks[1], toks[2:]
        elif len(toks) == 19:
            ntest, vals = toks[0], toks[1:]
        else:
            continue
        row = []
        for j, v in enumerate(vals):
            c = {"table": f"af{af}", "classifier": NINE[3 * block + j // 6], "k1train": float(k1),
                 "ntest": int(ntest), "metric": metrics[j % 6], "value": v}
            row.append(c)
        cells += row
        last = row
    return cells


def parse_er_table(pdf, af):
    """Additional files 13 and 14: nER+, nER-, kER+, then PA, PA_ER+, PA_ER-, PV_ER+, PV_ER-, AUC x 3."""
    metrics = ["PA", "PA_ER+", "PA_ER-", "PV_ER+", "PV_ER-", "AUC"]
    cells, block, n_neg = [], -1, None
    last = None
    for toks in table_lines(pdf):
        if any(t.replace("−", "-") in NINE for t in toks):
            block += 1
            continue
        if not toks or not all(NUMTOK.match(t) for t in toks):
            continue
        if toks[0].startswith("("):
            if last is not None and len(toks) == 18:
                for j, t in enumerate(toks):
                    last[j]["sd"] = t.strip("()")
            last = None
            continue
        if len(toks) == 21:
            n_pos, n_neg, kpos, vals = toks[0], toks[1], toks[2], toks[3:]
        elif len(toks) == 20:
            n_pos, kpos, vals = toks[0], toks[1], toks[2:]
        else:
            continue
        row = [{"table": f"af{af}", "classifier": NINE[3 * block + j // 6], "n_pos": int(n_pos),
                "n_neg": int(n_neg), "k_pos": kpos, "metric": metrics[j % 6], "value": v}
               for j, v in enumerate(vals)]
        cells += row
        last = row
    return cells


def main():
    dl, out = Path(sys.argv[1]), Path(sys.argv[2])
    figs = main_figures(dl / PAPER)
    figs += supplements(dl)
    tables = []
    for af in (1, 3):
        tables += parse_sim_table(dl / f"1471-2105-11-523-S{af}.PDF", af)
    for af in (13, 14):
        tables += parse_er_table(dl / f"1471-2105-11-523-S{af}.PDF", af)
    res = {"note": "Published values of PMC3098087 read by extract_published.py.",
           "figures": figs, "tables": tables}
    out.write_text(json.dumps(res, indent=1) + "\n")
    from collections import Counter
    print(Counter(r["figure"] for r in figs))
    print(Counter(c["table"] for c in tables))


if __name__ == "__main__":
    main()

"""Read the plotted numbers of Figs 2, 3 and 4 from the vector drawing in the article PDF, and the
cell colours of Fig. 1 from its raster.

Usage: read_figures.py PAPER.pdf OUT.json [SUPP_DIR]

With SUPP_DIR, also Additional files 15 (laid out as Fig. 2), 20 (as Fig. 3, ranked by accuracy) and 23 (as
Fig. 4, ranked by accuracy), and the kappa heat maps of Additional files 4, 10 and 12.

Figs 2-4 are vector graphics in the PMC copy of the article (pages 7, 11 and 13). Each panel's value
axis is calibrated from its own tick marks and printed tick labels (a least-squares line; the fit
residual is recorded); bar tops, error-bar ends and line vertices are then converted to data values.
Nothing inside a plot is fitted. Positions are PDF points (1/72 inch), y down from the page top.
"""
import json
import logging
import re
import sys
from collections import defaultdict

import numpy as np
import pdfplumber

logging.disable(logging.CRITICAL)

PRED = ["CHASM (breast)", "CHASM (lung)", "CHASM (melanoma)", "FATHMM (cancer)", "FATHMM (missense)",
        "Mutation Assessor", "MutationTaster", "PolyPhen-2", "PROVEAN", "SIFT", "VEST",
        "CanDrA (breast)", "CanDrA (lung)", "CanDrA (melanoma)", "Condel"]
SINGLE = PRED[:11]
GRID = [["accuracy", "composite"], ["sensitivity", "specificity"], ["ppv", "npv"]]
BLUE, ORANGE, RED = (0.26667, 0.29804, 0.66274), (0.97255, 0.64314, 0), (0.92157, 0.27451, 0.25098)


def close(a, b, tol=0.6):
    return abs(a - b) <= tol


def axes_of(page, lw=None):
    """Value axes: a vertical spine with at least three horizontal tick marks ending on it, each tick
    matched to the number printed beside it. Returns [{x, top, bottom, ticks: [(y, value)], a, b, rms}],
    value = a + b * y."""
    lines = [l for l in page.lines if lw is None or close(l["linewidth"], lw, 0.01)]
    vert = [l for l in lines if close(l["x0"], l["x1"], 0.01) and l["bottom"] - l["top"] > 20]
    horiz = [l for l in lines if close(l["top"], l["bottom"], 0.01) and 0.5 < l["x1"] - l["x0"] < 6]
    words = page.extract_words(extra_attrs=["upright"])
    nums = [w for w in words if re.fullmatch(r"-?\d+(\.\d+)?", w["text"])]
    out = []
    for v in vert:
        ticks = [h for h in horiz if close(h["x1"], v["x0"]) and v["top"] - 0.6 <= h["top"] <= v["bottom"] + 0.6]
        if len(ticks) < 3:
            continue
        pairs = []
        for t in ticks:
            y = t["top"]
            cands = [w for w in nums if w["x1"] <= t["x0"] + 0.5 and t["x0"] - w["x1"] < 8
                     and w["top"] - 1 <= y <= w["bottom"] + 1]
            if len(cands) == 1:
                pairs.append((y, float(cands[0]["text"])))
        if len(pairs) < 3:
            continue
        ys, vals = np.array([p[0] for p in pairs]), np.array([p[1] for p in pairs])
        b, a = np.polyfit(ys, vals, 1)
        rms = float(np.sqrt(np.mean((a + b * ys - vals) ** 2)))
        out.append({"x": v["x0"], "top": v["top"], "bottom": v["bottom"], "ticks": pairs,
                    "a": float(a), "b": float(b), "rms": rms})
    return sorted(out, key=lambda d: (round(d["top"]), d["x"]))


def grid_of(axes):
    """Group axes into rows (by top) and columns (by x)."""
    rows = defaultdict(list)
    for ax in axes:
        key = next((k for k in rows if close(k, ax["top"], 3)), ax["top"])
        rows[key].append(ax)
    return [sorted(rows[k], key=lambda d: d["x"]) for k in sorted(rows)]


def bars_of(page, ax, right):
    """Filled bars of one axes (between its spine and `right`), left to right, with the error bar on
    each: {x0, x1, top, bottom, colour, value, low, high}."""
    val = lambda y: ax["a"] + ax["b"] * y
    rects = [r for r in page.rects if r["fill"] and r["x0"] > ax["x"] and r["x1"] < right
             and ax["top"] - 1 <= r["top"] and r["bottom"] <= ax["bottom"] + 1 and r["x1"] - r["x0"] > 1]
    rects.sort(key=lambda r: r["x0"])
    whisk = [l for l in page.lines if close(l["x0"], l["x1"], 0.01) and ax["x"] < l["x0"] < right
             and l["linewidth"] > 0.4 and ax["top"] - 3 <= l["top"] and l["bottom"] <= ax["bottom"] + 1]
    out = []
    for r in rects:
        cx = (r["x0"] + r["x1"]) / 2
        w = [l for l in whisk if close(l["x0"], cx, 0.3)]
        rec = {"x0": r["x0"], "x1": r["x1"], "top": r["top"], "bottom": r["bottom"],
               "colour": [round(c, 3) for c in r["non_stroking_color"]], "value": val(r["top"]),
               "base": val(r["bottom"])}
        if w:
            rec["low"] = val(max(l["bottom"] for l in w))
            rec["high"] = val(min(l["top"] for l in w))
            rec["whisker_top"] = min(l["top"] for l in w)
            rec["whisker_bottom"] = max(l["bottom"] for l in w)
        out.append(rec)
    return out


def to_slots(bars, ax, offsets):
    """Put the bars into the template's slots (bar left edges relative to the spine). A slot with no
    bar is a bar of height zero: it is drawn as nothing, so its value is the axis base."""
    val = lambda y: ax["a"] + ax["b"] * y
    out = []
    for off in offsets:
        hit = [b for b in bars if close(b["x0"] - ax["x"], off, 0.5)]
        if hit:
            out.append(hit[0])
        else:
            out.append({"x0": ax["x"] + off, "x1": None, "top": ax["bottom"], "bottom": ax["bottom"],
                        "colour": None, "value": val(ax["bottom"]), "base": val(ax["bottom"]), "absent": True})
    if len(out) != len(bars) + sum(1 for b in out if b.get("absent")):
        raise ValueError("a bar does not sit in any slot")
    return out


def panels_with_slots(page, rows, n):
    """Bars of every axes in the grid, each put into the slots of a full axes (one with n bars)."""
    found = {}
    for ri, row in enumerate(rows):
        for ci, ax in enumerate(row):
            right = row[ci + 1]["x"] if ci + 1 < len(row) else page.width
            found[(ri, ci)] = (ax, bars_of(page, ax, right))
    full = [b for ax, b in found.values() if len(b) == n]
    if not full:
        raise ValueError(f"no axes with {n} bars")
    ax0 = next(ax for ax, b in found.values() if len(b) == n)
    offsets = [b["x0"] - ax0["x"] for b in full[0]]
    return {k: (ax, to_slots(b, ax, offsets)) for k, (ax, b) in found.items()}


def axes_record(ax, page_no):
    return {"page": page_no, "spine_x": ax["x"], "top": ax["top"], "bottom": ax["bottom"],
            "value_at_top": ax["a"] + ax["b"] * ax["top"], "value_at_bottom": ax["a"] + ax["b"] * ax["bottom"],
            "ticks": [[round(y, 3), v] for y, v in ax["ticks"]], "fit_rms": ax["rms"]}


def fig2(pdf, page_index=6, page_no=7):
    """Fig. 2 (and Additional file 15, laid out the same way): two panels, each a 3 x 2 grid of bar
    charts of the 15 predictors."""
    page = pdf.pages[page_index]
    rows = grid_of(axes_of(page))
    if len(rows) != 3 or any(len(r) != 4 for r in rows):
        raise ValueError(f"Fig. 2: axes grid {[len(r) for r in rows]}")
    out = {}
    slots = panels_with_slots(page, rows, 15)
    for (ri, ci), (ax, bars) in slots.items():
            panel = "a" if ci < 2 else "b"
            stat = GRID[ri][ci % 2]
            out.setdefault(panel, {})[stat] = {"axes": axes_record(ax, page_no),
                                               "bars": [dict(b, name=n) for b, n in zip(bars, PRED)]}
    return out


def fig3(pdf, page_index=10, page_no=11, marked="composite"):
    """Four panels (A-D), each a 3 x 2 grid of bar charts of seven bars: the top five combinations, the
    best single predictor, the best meta-predictor. Combination names come from the legend under each
    panel ('#1: At least ...')."""
    page = pdf.pages[page_index]
    rows = grid_of(axes_of(page))
    if len(rows) != 6 or any(len(r) != 4 for r in rows):
        raise ValueError(f"Fig. 3: axes grid {[len(r) for r in rows]}")
    legend, legend_box = legends_fig3(page)
    out = {}
    slots = panels_with_slots(page, rows, 7)
    for (ri, ci), (ax, bars) in slots.items():
            panel = "abcd"[(ri // 3) * 2 + ci // 2]
            stat = GRID[ri % 3][ci % 2]
            rec = {"axes": axes_record(ax, page_no), "bars": bars}
            if stat in (marked, "npv"):
                rec["markers"] = markers_of(page, ax, bars)
            out.setdefault(panel, {"combinations": legend[panel], "legend_box": legend_box[panel]})[stat] = rec
    return out


MARKER_COLOURS = {"vs best single": (0.267, 0.259, 0.643), "vs best meta": (0.996, 0.710, 0.227)}


def to_rgb(col):
    """A fill colour as RGB 0-1 (the article uses RGB, the supplement PDFs CMYK)."""
    col = tuple(col or ())
    if len(col) == 4:
        c, m, y, k = col
        return ((1 - c) * (1 - k), (1 - m) * (1 - k), (1 - y) * (1 - k))
    return col


def markers_of(page, ax, bars):
    """Significance marks above the bars of Fig. 3 (stars on the composite panels, triangles on the NPV
    panels): blue = significantly better than the best single predictor, orange = than the best
    meta-predictor. Returns, per bar, which marks it has, and the marks' rows (top, pt)."""
    found = []
    for c in page.curves:
        col = to_rgb(c.get("non_stroking_color"))
        # Blue marks are (0.267, 0.259, 0.643); orange ones (0.988, 0.745, 0.071) or (0.996, 0.710, 0.227).
        kind = None
        if len(col) == 3 and max(col) - min(col) > 0.3:
            kind = "vs best single" if col[2] > col[0] else "vs best meta"
        if kind and c["fill"] and ax["top"] - 22 * page.width / 595.276 < c["bottom"] <= ax["top"] + 0.5:
            found.append((kind, (c["x0"] + c["x1"]) / 2, c["top"], c["bottom"], len(c["pts"])))
    per_bar = []
    for b in bars:
        x0 = b["x0"]
        x1 = b["x1"] if b["x1"] else x0 + 4.83
        per_bar.append({k: any(f[0] == k and x0 <= f[1] <= x1 for f in found) for k in MARKER_COLOURS})
    rows = {k: sorted({round(f[2], 2) for f in found if f[0] == k}) for k in MARKER_COLOURS}
    return {"per_bar": per_bar, "rows_top": rows, "size": [round(found[0][3] - found[0][2], 2)] if found else [],
            "shape": "star" if any(f[4] > 6 for f in found) else "triangle"}


def legends_fig3(page):
    """The '#k: At least ...' lines under each panel, assigned to the panel by position."""
    text_lines = defaultdict(list)
    small = max((w["size"] for w in page.extract_words(extra_attrs=["size", "upright"])
                 if w["upright"] and re.fullmatch(r"#\d:", w["text"])), default=4)
    for w in page.extract_words(extra_attrs=["upright", "size"]):
        if w["upright"] and w["size"] <= small + 0.01:
            text_lines[(round(w["top"], 1), w["x0"] > page.width / 2)].append(w)
    entries = []
    for (top, right), ws in text_lines.items():
        s = " ".join(w["text"] for w in sorted(ws, key=lambda w: w["x0"]))
        for m in re.finditer(r"#(\d):\s*(At least \d+ of .*?)(?=\s*#\d:|$)", s):
            entries.append((top, right, int(m.group(1)), m.group(2).strip().replace("Mutation Taster", "MutationTaster")))
    tops = sorted({e[0] for e in entries})
    mid = (tops[0] + tops[-1]) / 2 if tops else 0
    out = {k: {} for k in "abcd"}
    box = {k: [1e9, 1e9, -1e9, -1e9] for k in "abcd"}
    for top, right, k, name in entries:
        panel = ("ab" if top < mid else "cd")[1 if right else 0]
        out[panel][k] = name
        ws = text_lines[(top, right)]
        b = box[panel]
        b[0] = min(b[0], min(w["x0"] for w in ws))
        b[1] = min(b[1], min(w["top"] for w in ws))
        b[2] = max(b[2], max(w["x1"] for w in ws))
        b[3] = max(b[3], max(w["bottom"] for w in ws))
    return {p: [v[k] for k in sorted(v)] for p, v in out.items()}, box


LEGEND4 = [["CHASM (breast)", "CHASM (lung)", "CHASM (melanoma)"],
           ["FATHMM (cancer)", "FATHMM (missense)", "Mutation Assessor"],
           ["MutationTaster", "PolyPhen-2", "PROVEAN"], ["SIFT", "VEST"]]
TOPS = [10, 20, 50, 100]


def fig4(pdf, page_index=12, page_no=13):
    """Two panels (A all SNVs, B non-COSMIC), each subset 1 and subset 2: the share of the top 10, 20,
    50 and 100 combinations that include each predictor. The y axis labels are rotated, so the axes
    are calibrated from the tick marks with the printed sequence 0, 20, ..., 100 (read bottom to top)."""
    page = pdf.pages[page_index]
    lines = page.lines
    # Legend: small filled squares in four columns, three rows, in the lower part of the page; the names
    # are printed beside them.
    sq = sorted([r for r in page.rects if r["fill"] and 3 < r["x1"] - r["x0"] < 10 and 3 < r["bottom"] - r["top"] < 10
                 and r["top"] > 0.6 * page.height], key=lambda r: (r["x0"], r["top"]))
    cols = sorted({round(r["x0"], 1) for r in sq})
    colour = {}
    for r in sq:
        ci = cols.index(round(r["x0"], 1))
        ri = sorted({round(q["top"], 1) for q in sq if round(q["x0"], 1) == round(r["x0"], 1)}).index(round(r["top"], 1))
        colour[tuple(round(c, 3) for c in r["non_stroking_color"])] = LEGEND4[ci][ri]
    if len(colour) != 11:
        raise ValueError(f"Fig. 4 legend: {len(colour)} colours")
    spines = [l for l in lines if close(l["x0"], l["x1"], 0.01) and l["bottom"] - l["top"] > 100]
    out = {}
    for sp in sorted(spines, key=lambda l: (round(l["top"]), l["x0"])):
        ticks = sorted(h["top"] for h in lines if close(h["top"], h["bottom"], 0.01) and close(h["x1"], sp["x0"])
                       and 0.5 < h["x1"] - h["x0"] < 10 and sp["top"] - 0.5 <= h["top"] <= sp["bottom"] + 0.5)
        if len(ticks) != 6:
            raise ValueError(f"Fig. 4: {len(ticks)} ticks")
        ys = np.array(ticks[::-1])
        vals = np.array([0, 20, 40, 60, 80, 100], dtype=float)
        b, a = np.polyfit(ys, vals, 1)
        rms = float(np.sqrt(np.mean((a + b * ys - vals) ** 2)))
        frame = [r for r in page.rects if not r["fill"] and close(r["x0"], sp["x0"], 8) and r["x1"] - r["x0"] > 50
                 and r["top"] < sp["top"] + 1 and r["bottom"] > sp["bottom"] - 1]
        if not frame:
            raise ValueError("Fig. 4: no plot frame")
        frame = frame[0]
        xt = sorted(l["x0"] for l in lines if close(l["x0"], l["x1"], 0.01) and sp["x0"] < l["x0"] <= frame["x1"]
                    and 3 < l["bottom"] - l["top"] < 10 and sp["bottom"] < l["top"] < sp["bottom"] + 20)
        if len(xt) != 4:
            raise ValueError(f"Fig. 4: {len(xt)} category ticks")
        segs = defaultdict(list)
        for c in page.curves:
            col = tuple(round(v, 3) for v in (c["stroking_color"] or ()))
            if col in colour and sp["x0"] < c["x0"] and c["x1"] <= xt[-1] + 1 and sp["top"] - 1 <= c["top"] and c["bottom"] <= sp["bottom"] + 1:
                pts = c["pts"]
                segs[colour[col]] += list(zip(pts[:-1], pts[1:]))
        for l in lines:
            col = tuple(round(v, 3) for v in (l["stroking_color"] or ()))
            if col in colour and sp["x0"] < l["x0"] and l["x1"] <= xt[-1] + 1 and sp["top"] - 1 <= l["top"] and l["bottom"] <= sp["bottom"] + 1:
                segs[colour[col]].append(((l["x0"], l["top"]), (l["x1"], l["bottom"])))
        series = {}
        for name in SINGLE:
            v = []
            for x in xt:
                y = None
                for (x0, y0), (x1, y1) in segs.get(name, []):
                    lo, hi = min(x0, x1), max(x0, x1)
                    if lo - 0.05 <= x <= hi + 0.05:
                        y = y0 if hi - lo < 1e-6 else y0 + (y1 - y0) * (x - x0) / (x1 - x0)
                        break
                v.append(None if y is None else float(a + b * y))
            series[name] = v
        tops = sorted({round(q["top"]) for q in spines})
        lefts = sorted({round(q["x0"]) for q in spines})
        panel = "a" if round(sp["top"]) == tops[0] else "b"
        sub = "subset1" if round(sp["x0"]) == lefts[0] else "subset2"
        out.setdefault(panel, {})[sub] = {
            "axes": {"page": page_no, "spine_x": sp["x0"], "top": sp["top"], "bottom": sp["bottom"], "fit_rms": rms,
                     "value_at_top": float(a + b * sp["top"]), "value_at_bottom": float(a + b * sp["bottom"]),
                     "category_x": xt, "categories": [f"Top {t}" for t in TOPS],
                     "frame": [frame["x0"], frame["top"], frame["x1"], frame["bottom"]]},
            "series": series, "colours": {v: list(k) for k, v in colour.items()}}
    return out


# Fig. 1: the embedded raster (page 5) holds the gene-class bar, the call heat maps (A, C) and the kappa
# heat maps (B, D); the dendrograms, labels and colour keys are vector graphics on top.
FIG1_KAPPA_KEY = {  # colour key, from the vector legend squares (RGB 0-1)
    "negative": (1, 0.984, 0.875), "0.01-0.2": (0.969, 0.898, 0.2), "0.21-0.4": (0.976, 0.847, 0),
    "0.41-0.6": (0.965, 0.624, 0), "0.61-0.8": (0.925, 0.345, 0.008), "0.81-1": (0.878, 0.18, 0.071)}
FIG1_CALL_KEY = {"neutral": (0.973, 0.643, 0), "non-neutral": (0.267, 0.298, 0.663), "no call": (0.925, 0.925, 0.925)}
FIG1_BOXES = {  # pixel boxes in the embedded image (x0, x1, y0, y1, inclusive), measured from its white gaps
    "a": (0, 1028, 18, 364), "c": (0, 1028, 494, 838), "b": (1242, 1616, 18, 364), "d": (1242, 1616, 494, 838)}


def fig1_image(pdf):
    import io

    from PIL import Image
    page = pdf.pages[4]
    im = page.images[0]
    img = Image.open(io.BytesIO(im["stream"].get_rawdata())).convert("RGB")
    return img, {"x0": im["x0"], "x1": im["x1"], "top": im["top"], "bottom": im["bottom"], "size": list(img.size)}


def fig1(pdf):
    """Kappa heat maps (B, D): the colour of each of the 15 x 15 cells, matched to the nearest colour of
    the key (median of the 9 x 9 pixels at the cell centre). Call heat maps (A, C): the share of each
    row that is non-neutral (blue), neutral (orange) or no call (grey), by unmixing the row's mean colour
    into the three key colours (the 3,591 or 1,699 columns are resampled into 1,029 pixels, so single
    pixels are blends)."""
    img, place = fig1_image(pdf)
    a = np.asarray(img).astype(float) / 255
    out = {"image": place, "boxes": FIG1_BOXES}
    keys = list(FIG1_KAPPA_KEY)
    K = np.array([FIG1_KAPPA_KEY[k] for k in keys])
    for panel in "bd":
        x0, x1, y0, y1 = FIG1_BOXES[panel]
        w, h = (x1 - x0 + 1) / 15, (y1 - y0 + 1) / 15
        cells = []
        for j in range(15):
            row = []
            for i in range(15):
                cx, cy = int(x0 + w * (i + 0.5)), int(y0 + h * (j + 0.5))
                c = np.median(a[cy - 4:cy + 5, cx - 4:cx + 5].reshape(-1, 3), axis=0)
                d = np.sqrt(((K - c) ** 2).sum(1))
                row.append({"bin": keys[int(d.argmin())], "distance": float(d.min())})
            cells.append(row)
        out[panel] = {"cells": cells, "cell_px": [w, h]}
    C = np.array([FIG1_CALL_KEY[k] for k in FIG1_CALL_KEY]).T
    A = np.vstack([C, np.ones(3)])
    for panel in "ac":
        x0, x1, y0, y1 = FIG1_BOXES[panel]
        h = (y1 - y0 + 1) / 15
        rows = []
        for j in range(15):
            r0, r1 = int(y0 + h * j + 4), int(y0 + h * (j + 1) - 4)
            mean = a[r0:r1 + 1, x0:x1 + 1].reshape(-1, 3).mean(0)
            f, *_ = np.linalg.lstsq(A, np.append(mean, 1.0), rcond=None)
            rows.append(dict(zip(FIG1_CALL_KEY, (float(v) for v in f))))
        out[panel] = {"rows": rows}
    # Dendrograms (vector, 0.33 pt lines left of the raster): each join is drawn at x = its height, the
    # root furthest left and the leaves at the right end. Relative height = (leaf x - x) / (leaf x - root x).
    page = pdf.pages[4]
    objs = [o for o in page.lines + page.curves if o["x1"] < place["x0"] and close(o.get("linewidth", 0), 0.33, 0.01)]
    mid = (place["top"] + place["bottom"]) / 2
    for panel, sel in (("a", lambda o: o["top"] < mid), ("c", lambda o: o["top"] >= mid)):
        ob = [o for o in objs if sel(o)]
        xr, xl = min(o["x0"] for o in ob), max(o["x1"] for o in ob)
        nodes = sorted({round(min(x for x, _ in o["pts"]), 3) for o in ob})
        out[panel]["dendrogram"] = {"root_x": xr, "leaf_x": xl, "join_x": nodes, "top": min(o["top"] for o in ob),
                                    "bottom": max(o["bottom"] for o in ob),
                                    "relative_heights": sorted((xl - x) / (xl - xr) for x in nodes)}
    return out


def boxplots(pdf):
    """Additional files 24 and 26: box plots of the combinations' mean accuracy in subset 1, one panel
    per value of one parameter (printed above the panel as 'n=' or 'p='), one box per value of the other
    (printed under it). Each panel's value axis is calibrated from its tick marks; the tick labels are
    printed rotated (read as reversed digits). A box gives the lower and upper hinge (a box of one
    combination has no height and reads as its median), the thick line the median."""
    page = pdf.pages[0]
    frames = sorted([r for r in page.rects if r["stroke"] and r["x1"] - r["x0"] > 200], key=lambda r: (round(r["top"]), r["x0"]))
    words = page.extract_words(extra_attrs=["upright"])
    out = []
    for f in frames:
        ticks = sorted(l["top"] for l in page.lines if close(l["top"], l["bottom"], 0.01) and close(l["x1"], f["x0"], 0.6)
                       and l["x1"] - l["x0"] < 10 and f["top"] - 0.5 <= l["top"] <= f["bottom"] + 0.5)
        labels = []
        for y in ticks:
            w = [w for w in words if not w["upright"] and w["x1"] <= f["x0"] and f["x0"] - w["x1"] < 12 and w["top"] - 1 <= y <= w["bottom"] + 1]
            labels.append(float(w[0]["text"][::-1]) if len(w) == 1 else None)
        pairs = [(y, v) for y, v in zip(ticks, labels) if v is not None]
        ys, vs = np.array([p[0] for p in pairs]), np.array([p[1] for p in pairs])
        b, a = np.polyfit(ys, vs, 1)
        val = lambda y: float(a + b * y)
        title = sorted([w for w in words if w["upright"] and f["x0"] < w["x0"] < f["x1"] and f["top"] - 30 < w["bottom"] <= f["top"]],
                       key=lambda w: w["x0"])
        ttext = "".join(w["text"] for w in title)
        m = re.match(r"([np])=(\d+)", ttext)
        xt = sorted(l["x0"] for l in page.lines if close(l["x0"], l["x1"], 0.01) and f["x0"] < l["x0"] < f["x1"]
                    and f["bottom"] - 0.5 <= l["top"] < f["bottom"] + 10)
        xl = {}
        for w in words:
            if w["upright"] and f["bottom"] < w["top"] < f["bottom"] + 20 and re.fullmatch(r"\d+", w["text"]):
                xl[round((w["x0"] + w["x1"]) / 2, 1)] = int(w["text"])
        if not xt:  # a panel with a single combination: its median line only
            xt = [(l["x0"] + l["x1"]) / 2 for l in page.lines if l["linewidth"] > 2 and f["x0"] < l["x0"] < f["x1"] and f["top"] < l["top"] < f["bottom"]]
        groups = []
        for x in xt:
            lab = min(xl.items(), key=lambda kv: abs(kv[0] - x))[1] if xl else None
            box = [r for r in page.rects + page.curves if r["stroke"] and r["x0"] < x < r["x1"] and 5 < r["x1"] - r["x0"] < 0.6 * (f["x1"] - f["x0"])
                   and f["top"] < r["top"] and r["bottom"] < f["bottom"] and r["bottom"] - r["top"] > 0.05
                   and (r.get("object_type") == "rect" or len({round(px, 1) for px, _ in r["pts"]}) == 2)]
            med = [l for l in page.lines if l["linewidth"] > 2 and l["x0"] < x < l["x1"] and f["top"] < l["top"] < f["bottom"]]
            g = {"x": x, "label": lab, "median": val(med[0]["top"]) if med else None}
            if box:
                g["upper"], g["lower"] = val(box[0]["top"]), val(box[0]["bottom"])
                g["box"] = [box[0]["x0"], box[0]["top"], box[0]["x1"], box[0]["bottom"]]
            elif med:
                g["upper"] = g["lower"] = g["median"]
            groups.append(g)
        out.append({"title": [m.group(1), int(m.group(2))] if m else ttext, "frame": [f["x0"], f["top"], f["x1"], f["bottom"]],
                    "axis": {"top": f["top"], "bottom": f["bottom"], "value_at_top": val(f["top"]), "value_at_bottom": val(f["bottom"]),
                             "fit_rms": float(np.sqrt(np.mean((a + b * ys - vs) ** 2)))}, "groups": groups})
    return out


AF29_SERIES = ["all", "non_cosmic", "excluding_training"]


def af29(pdf):
    """Additional file 29: for six predictors, accuracy, sensitivity, specificity, PPV and NPV (left
    axis, 0-1) and the composite score (right axis, 0-4) on all 989 labelled SNVs (red), the 297 not in
    COSMIC (blue) and the 989 without the predictor's own training-set SNVs (orange), with error bars.
    The predictor of each panel is read from its rotated axis title."""
    page = pdf.pages[0]
    words = page.extract_words(extra_attrs=["upright"])
    lines = page.lines
    out = {}
    for ax in axes_of(page):
        right = [l for l in lines if close(l["x0"], l["x1"], 0.01) and l["x0"] > ax["x"] + 50 and close(l["top"], ax["top"], 1)
                 and close(l["bottom"], ax["bottom"], 1)]
        right = min(right, key=lambda l: l["x0"])
        rt = sorted(h["top"] for h in lines if close(h["top"], h["bottom"], 0.01) and close(h["x0"], right["x0"], 0.6) and 0.5 < h["x1"] - h["x0"] < 10
                    and right["top"] - 0.5 <= h["top"] <= right["bottom"] + 0.5)
        rl = []
        for y in rt:
            w = [w for w in words if w["upright"] and w["x0"] >= right["x0"] and w["x0"] - right["x0"] < 15 and w["top"] - 1 <= y <= w["bottom"] + 1]
            rl.append(float(w[0]["text"]) if len(w) == 1 else None)
        pr = [(y, v) for y, v in zip(rt, rl) if v is not None]
        b2, a2 = np.polyfit([q[0] for q in pr], [q[1] for q in pr], 1)
        title = sorted([w for w in words if not w["upright"] and ax["x"] - 45 < w["x0"] and w["x1"] < ax["x"] - 20 and ax["top"] <= w["top"] <= ax["bottom"]],
                       key=lambda w: -w["top"])
        name = " ".join(w["text"][::-1] for w in title).replace("Polyphen-2", "PolyPhen-2")
        bars = bars_of(page, ax, right["x0"])
        if len(bars) != 18:
            raise ValueError(f"AF29 {name}: {len(bars)} bars")
        rec = {}
        for j, st in enumerate(STATS6):
            cal = (lambda y: float(a2 + b2 * y)) if st == "composite" else (lambda y: ax["a"] + ax["b"] * y)
            for k, series in enumerate(AF29_SERIES):
                b = bars[3 * j + k]
                r = {"value": cal(b["top"]), "box": [b["x0"], b["top"], b["x1"], b["bottom"]], "colour": b["colour"]}
                if "whisker_top" in b:
                    r["low"], r["high"] = cal(b["whisker_bottom"]), cal(b["whisker_top"])
                rec.setdefault(series, {})[st] = r
        out[name] = {"bars": rec, "left_axis": axes_record(ax, 1),
                     "right_axis": {"x": right["x0"], "top": right["top"], "bottom": right["bottom"],
                                    "value_at_top": float(a2 + b2 * right["top"]), "value_at_bottom": float(a2 + b2 * right["bottom"])}}
    return out


STATS6 = ["accuracy", "sensitivity", "specificity", "ppv", "npv", "composite"]
KAPPA_BINS = ["negative", "0.01-0.2", "0.21-0.4", "0.41-0.6", "0.61-0.8", "0.81-1"]


def kappa_grids(pdf):
    """Additional files 4, 10 and 12: vector kappa heat maps (two 15 x 15 grids of filled rectangles,
    the upper for the first SNV set, the lower for the second), with a six-colour key and the predictor
    names to the right of each row. Returns, per grid, the row names (top to bottom; the columns are in
    the same order) and each cell's key bin (its colour equals a key colour)."""
    page = pdf.pages[0]
    from collections import Counter
    sizes = Counter((round(r["x1"] - r["x0"], 1), round(r["bottom"] - r["top"], 1)) for r in page.rects if r["fill"])
    cell = next(k for k, v in sizes.items() if v == 450)
    cells = [r for r in page.rects if r["fill"] and (round(r["x1"] - r["x0"], 1), round(r["bottom"] - r["top"], 1)) == cell]
    top_cells = min(r["top"] for r in cells)
    cand = [r for r in page.rects if r["fill"] and r["top"] < top_cells and r["x1"] - r["x0"] < 20 and r["x0"] > page.width / 2]
    groups = {}
    for r in cand:
        groups.setdefault(round(r["x0"]), []).append(r)
    # The kappa key is the right-most column of six squares (the call key, with as many, is to its left).
    keys = sorted(groups[max(k for k, v in groups.items() if len(v) == 6)], key=lambda r: r["top"])
    mid = (min(r["top"] for r in cells) + max(r["bottom"] for r in cells)) / 2
    words = page.extract_words(keep_blank_chars=True, extra_attrs=["upright"])
    out = {}
    for name, sel in (("first", lambda r: r["top"] < mid), ("second", lambda r: r["top"] >= mid)):
        g = sorted([r for r in cells if sel(r)], key=lambda r: (round(r["top"], 1), r["x0"]))
        rows = [g[i * 15:(i + 1) * 15] for i in range(15)]
        right = max(r["x1"] for r in g)
        names = []
        for row in rows:
            y0, y1 = row[0]["top"], row[0]["bottom"]
            ws = sorted([w for w in words if w["upright"] and w["x0"] > right and y0 <= (w["top"] + w["bottom"]) / 2 <= y1],
                        key=lambda w: w["x0"])
            names.append(" ".join(w["text"] for w in ws).replace("−", "-").replace("Polyphen-2", "PolyPhen-2").strip())
        K = [(np.array(to_rgb(r["non_stroking_color"])), b) for r, b in zip(keys, KAPPA_BINS)]
        near = lambda col: min(K, key=lambda kb: float(np.sum((kb[0] - np.array(to_rgb(col))) ** 2)))
        bins = [[near(r["non_stroking_color"])[1] for r in row] for row in rows]
        dist = max(float(np.sqrt(np.sum((near(r["non_stroking_color"])[0] - np.array(to_rgb(r["non_stroking_color"]))) ** 2)))
                   for row in rows for r in row)
        out[name] = {"rows": names, "bins": bins, "max_colour_distance": dist,
                     "boxes": [[[r["x0"], r["top"], r["x1"], r["bottom"]] for r in row] for row in rows]}
    return out


def main():
    pdf_path, out = sys.argv[1:3]
    supp = sys.argv[3] if len(sys.argv) > 3 else None
    pdf = pdfplumber.open(pdf_path)
    res = {"fig1": fig1(pdf), "fig2": fig2(pdf), "fig3": fig3(pdf), "fig4": fig4(pdf)}
    if supp:
        res["af15"] = fig2(pdfplumber.open(f"{supp}/13059_2014_484_MOESM15_ESM.pdf"), 0, 1)
        res["af20"] = fig3(pdfplumber.open(f"{supp}/13059_2014_484_MOESM20_ESM.pdf"), 0, 1, marked="accuracy")
        res["af23"] = fig4(pdfplumber.open(f"{supp}/13059_2014_484_MOESM23_ESM.pdf"), 0, 1)
        res["af29"] = af29(pdfplumber.open(f"{supp}/13059_2014_484_MOESM29_ESM.pdf"))
        for n in (24, 26):
            res[f"af{n}"] = boxplots(pdfplumber.open(f"{supp}/13059_2014_484_MOESM{n}_ESM.pdf"))
        for n in (4, 10, 12):
            res[f"af{n}"] = kappa_grids(pdfplumber.open(f"{supp}/13059_2014_484_MOESM{n}_ESM.pdf"))
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
        f.write("\n")


if __name__ == "__main__":
    main()

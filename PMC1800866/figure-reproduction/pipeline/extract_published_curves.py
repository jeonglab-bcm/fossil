#!/usr/bin/env python3
"""Read the recall-precision curves of Figs 3-6 out of the paper's PDF.

The four figures are gnuplot vector drawings in the PDF. Each panel is a stroked rectangle (the
axes box); each series is a run of stroked line segments drawn in one style (line width and
dash pattern), with the legend sample drawn first. The pixel-to-data map comes from the axes box
and the printed tick labels only; nothing inside the box is fitted.

Usage: extract_published_curves.py PAPER_PDF OUT_JSON
"""
import json
import math
import sys

import pymupdf

# Page index (0-based), the panel labels left to right, and the series names in legend order.
FIGURES = {
    "fig3": (5, 540, 680, {"a": ["Local", "Gated"], "b": ["Local", "Gated"], "c": ["Local", "Gated"]}),
    "fig4": (6, 90, 230, {"a": ["Local", "Gated"], "b": ["Local", "Gated"], "c": ["Local", "Gated"]}),
    "fig5": (6, 525, 670, {"a": ["All"], "b": ["Zn4", "Zn3", "Zn2", "Zn1"], "c": ["CH Zn3", "CHDE Zn3"]}),
    "fig6": (7, 90, 230, {"a": ["All"], "b": ["Zn4", "Zn3", "Zn2", "Zn1"], "c": ["CH Zn3", "CHDE Zn3"]}),
}


def number(s):
    try:
        return float(s)
    except ValueError:
        return None


def axes_boxes(drawings, y0, y1):
    boxes = []
    for d in drawings:
        r = d["rect"]
        if d["type"] == "s" and d["items"][0][0] == "re" and y0 < r.y0 < y1 and r.width > 80 and r.height > 80:
            if not any(abs(r.x0 - b.x0) < 1 and abs(r.y0 - b.y0) < 1 for b in boxes):
                boxes.append(r)
    return sorted(boxes, key=lambda r: r.x0)


def tick_map(words, box):
    """Linear maps from page coordinates to data, from the tick labels left of and below the box."""
    ys = [(number(w[4]), (w[1] + w[3]) / 2) for w in words
          if number(w[4]) is not None and box.x0 - 20 < w[2] < box.x0 + 1 and box.y0 - 6 < (w[1] + w[3]) / 2 < box.y1 + 6]
    xs = [(number(w[4]), (w[0] + w[2]) / 2) for w in words
          if number(w[4]) is not None and box.y1 < w[1] < box.y1 + 8 and box.x0 - 8 < (w[0] + w[2]) / 2 < box.x1 + 8]
    ylo, yhi = min(v for v, _ in ys), max(v for v, _ in ys)
    xlo, xhi = min(v for v, _ in xs), max(v for v, _ in xs)
    fx = lambda px: xlo + (px - box.x0) / (box.x1 - box.x0) * (xhi - xlo)
    fy = lambda py: ylo + (box.y1 - py) / (box.y1 - box.y0) * (yhi - ylo)
    # Residual of the label centres against the map (labels sit centred on their ticks).
    rx = max(abs(fx(c) - v) for v, c in xs)
    ry = max(abs(fy(c) - v) for v, c in ys)
    return fx, fy, {"x": [xlo, xhi], "y": [ylo, yhi], "label_residual_x": round(rx, 4), "label_residual_y": round(ry, 4)}


def series_in_box(drawings, box):
    """Stroked line runs inside the box, grouped by style in drawing order, split into chains."""
    styles, order = {}, []
    for d in drawings:
        if d["type"] != "s" or not d["items"] or any(it[0] != "l" for it in d["items"]):
            continue
        r = d["rect"]
        if r.x0 < box.x0 - 0.5 or r.x1 > box.x1 + 0.5 or r.y0 < box.y0 - 0.5 or r.y1 > box.y1 + 0.5:
            continue
        key = (round(d.get("width") or 0, 3), str(d.get("dashes")))
        if d.get("dashes") == "[ .233 .466 ] 0":
            continue  # grid
        if len(d["items"]) <= 2 and all(abs(a.x - b.x) < 0.01 or abs(a.y - b.y) < 0.01 for _, a, b in d["items"]):
            continue  # axes and ticks (a legend sample alone is dropped too; the curve follows)
        if key not in styles:
            styles[key] = []
            order.append(key)
        for it in d["items"]:
            styles[key].append((it[1], it[2]))
    out = []
    for key in order:
        chains, cur = [], []
        for p, q in styles[key]:
            if cur and math.dist(cur[-1], (p.x, p.y)) > 0.05:
                chains.append(cur)
                cur = []
            if not cur:
                cur.append((p.x, p.y))
            cur.append((q.x, q.y))
        chains.append(cur)
        out.append((key, chains))
    return out


def main(pdf, out_json):
    doc = pymupdf.open(pdf)
    result = {}
    for fig, (page, y0, y1, panels) in FIGURES.items():
        p = doc[page]
        drawings = p.get_drawings()
        words = p.get_text("words")
        boxes = axes_boxes(drawings, y0, y1)
        assert len(boxes) == len(panels), (fig, boxes)
        for box, (panel, names) in zip(boxes, panels.items()):
            fx, fy, axes = tick_map(words, box)
            groups = series_in_box(drawings, box)
            assert len(groups) == len(names), (fig, panel, [g[0] for g in groups])
            series = {}
            for name, (style, chains) in zip(names, groups):
                # The legend sample is a short horizontal chain; the curve is the longest chain.
                curve = max(chains, key=len)
                series[name] = {
                    "style": {"width": style[0], "dashes": style[1]},
                    "points": [[round(fx(x), 5), round(fy(y), 5)] for x, y in curve],
                    "legend_chains_dropped": len(chains) - 1,
                }
            result[f"{fig}.{panel}"] = {"page": page + 1, "box": [round(v, 2) for v in box], "axes": axes, "series": series}
    json.dump(result, open(out_json, "w"), indent=1)
    for k, v in result.items():
        print(k, v["axes"], {n: len(s["points"]) for n, s in v["series"].items()})


if __name__ == "__main__":
    main(*sys.argv[1:3])

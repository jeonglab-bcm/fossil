"""Read the plotted data out of the paper's vector figures.

usage: extract_published.py PAPER_PDF OUT_JSON

For each calibrated panel (params/panels.json): the fitted curves (coloured filled outlines; the
curve is the median height of the outline per x bin), the data markers (circles drawn as four
Bezier segments: their centres) and, for Fig. 5, the coloured dots. Coordinates are converted to
data units with the panel's axis calibration. Also reads the bar lengths of Fig. 6 (left).
"""
import json
import sys
from pathlib import Path

import numpy as np
import pymupdf

HERE = Path(__file__).resolve().parent
DARK = (0.14, 0.12, 0.13)


def to_data(panel, x, y):
    x0, y0, x1, y1 = panel["frame"]
    xa, xb = panel["xlim"]
    ya, yb = panel["ylim"]
    return xa + (np.asarray(x) - x0) / (x1 - x0) * (xb - xa), ya + (y1 - np.asarray(y)) / (y1 - y0) * (yb - ya)


def rounded(c):
    return tuple(round(t, 2) for t in c) if c else None


def circles(items):
    out = []
    i = 0
    while i < len(items):
        if i + 3 < len(items) and all(items[i + j][0] == "c" for j in range(4)):
            pts = np.array([[q.x, q.y] for j in range(4) for q in (items[i + j][1], items[i + j][4])])
            c = pts.mean(0)
            out.append((c[0], c[1], np.abs(pts - c).max()))
            i += 4
        else:
            i += 1
    return out


def main(pdf, out):
    doc = pymupdf.open(pdf)
    panels = json.loads((HERE / "params" / "panels.json").read_text())["panels"]
    res = {}
    for name, pn in panels.items():
        page = doc[pn["page"] - 1]
        R = pymupdf.Rect(*pn["frame"]) + (-1, -1, 1, 1)
        curves, marks, dots = {}, [], []
        for d in page.get_drawings():
            c = (d["rect"].tl + d["rect"].br) / 2
            if not R.contains(c) or d.get("fill") is None:
                continue
            col = rounded(d["fill"])
            if col == (1.0, 1.0, 1.0):
                continue
            if name.startswith("fig5") or name == "fig7.b":
                for cx, cy, r in circles(d["items"]):
                    dots.append((cx, cy, col))
                continue
            if col == DARK:
                for cx, cy, r in circles(d["items"]):
                    if r > 0.5:
                        marks.append((cx, cy, r))
                continue
            pts = [(q.x, q.y) for it in d["items"] for q in it[1:] if isinstance(q, pymupdf.Point)]
            if pts:
                curves.setdefault(col, []).extend(pts)
        entry = {}
        if marks:
            m = np.array(marks)
            rmax = m[:, 2].max()
            m = m[m[:, 2] > rmax - 0.2]  # outer ring of each marker
            x, y = to_data(pn, m[:, 0], m[:, 1])
            entry["points"] = np.column_stack([x, y]).round(3).tolist()
        if dots:
            x, y = to_data(pn, [d[0] for d in dots], [d[1] for d in dots])
            entry["dots"] = [[float(a), float(b), list(c)] for a, b, (c) in zip(x.round(3), y.round(3), [d[2] for d in dots])]
        entry["curves"] = {}
        for col, pts in curves.items():
            p = np.array(pts)
            x, y = to_data(pn, p[:, 0], p[:, 1])
            xa, xb = pn["xlim"]
            edges = np.linspace(min(x), max(x), 151)
            k = np.clip(np.digitize(x, edges) - 1, 0, 149)
            cx, cy = [], []
            for b in range(150):
                s = k == b
                if s.sum():
                    cx.append(float((edges[b] + edges[b + 1]) / 2))
                    cy.append(float(np.median(y[s])))
            entry["curves"][",".join(map(str, col))] = np.column_stack([cx, cy]).round(3).tolist()
        res[name] = entry
    # Fig. 6 (left): score bars, grey filled rectangles, in units of the 0-1 axis
    page = doc[4]
    bars = []
    for d in page.get_drawings():
        r = d["rect"]
        if d.get("fill") and rounded(d["fill"]) == (0.88, 0.83, 0.84) and \
                320 < r.x0 < 460 and 60 < r.y0 < 170 and 3 < r.height < 10:
            bars.append((r.x0, r.y0, r.x1, r.y1))
    res["fig6.bars"] = sorted(set(tuple(round(v, 2) for v in b) for b in bars))
    Path(out).write_text(json.dumps(res, indent=0))
    for k, v in res.items():
        if isinstance(v, dict):
            print(k, len(v.get("points", [])), len(v.get("dots", [])), {c: len(p) for c, p in v["curves"].items()})
    print("fig6 bars", res["fig6.bars"])


if __name__ == "__main__":
    main(*sys.argv[1:3])

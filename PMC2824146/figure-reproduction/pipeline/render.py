"""Draw our Figures 1 to 8 on the published figures' own axes, and overlay them on the published ones.

The published figure is the vector drawing in the article PDF, rasterised here at 2x (144 dpi).
Each panel's data-to-point map comes from its tick marks (extract_published.py), so our points land
where the paper's would for the same values.

  fig<N>_ours.png     the published figure with its plotted data taken out and ours drawn in: axes,
                      labels, titles and key are the paper's own, only the data are ours
  fig<N>_overlay.png  the published figure in grey with our series in magenta on top
  fig<N>_published.png the published figure, rasterised on the same grid (for the results page)

    python3 render.py PMC2824146.1.pdf published_values.json summary.json targets.json OUT_DIR
"""

import json
import math
import sys
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image, ImageDraw

import extract_published as X

SCALE = 2.0
PAGES = {1: 2, 2: 6, 3: 8, 4: 9, 5: 10, 6: 11, 7: 12, 8: 13}
QTY = {2: "estimate", 3: "se", 4: "coverage", 5: "p_mean", 7: "estimate", 8: "coverage"}
LEVELS = [5, 10, 25, 50, 75]
MAGENTA = (220, 0, 160)
NAMES = {"CC": "CC", "SI": "SI", "AREG": "MI aregImpute", "MICE": "MI MICE", "MICE_PMM": "MI MICE-PMM",
         "MICE_PMM_notrans": "MI MICE-PMM no transformations", "MIX_notrunc": "MI MIX no truncating"}


def figure_clip(page, fig):
    """The figure frame's interior, above the 'Figure N' caption."""
    frame = None
    for d in page.get_drawings():
        r = d["rect"]
        if r.width > 400 and 0.1 < r.height < 1.5:
            frame = r
            break
    cap = None
    for b in page.get_text("dict")["blocks"]:
        t = "".join(s["text"] for ln in b.get("lines", []) for s in ln["spans"])
        if t.startswith(f"Figure {fig}") and (cap is None or b["bbox"][1] > cap):
            cap = b["bbox"][1]
    top = frame.y1 + 2 if frame else 90
    return pymupdf.Rect(58, top, 537, cap - 2)


class Canvas:
    def __init__(self, clip, img):
        self.clip = clip
        self.img = img
        self.d = ImageDraw.Draw(img)

    def px(self, x, y):
        return ((x - self.clip.x0) * SCALE, (y - self.clip.y0) * SCALE)

    def line(self, pts, col, width=2, dash=None):
        q = [self.px(*p) for p in pts]
        if dash:
            for a, b in zip(q, q[1:]):
                n = max(int(math.dist(a, b) / dash), 1)
                for k in range(0, n, 2):
                    t0, t1 = k / n, min((k + 1) / n, 1)
                    self.d.line([(a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0),
                                 (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)], fill=col, width=width)
        else:
            self.d.line(q, fill=col, width=width)

    def marker(self, x, y, kind, col, r=5):
        cx, cy = self.px(x, y)
        d = self.d
        if kind == "circle":
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=2)
        elif kind == "x":
            d.line([cx - r, cy - r, cx + r, cy + r], fill=col, width=2)
            d.line([cx - r, cy + r, cx + r, cy - r], fill=col, width=2)
        elif kind == "plus":
            d.line([cx - r, cy, cx + r, cy], fill=col, width=2)
            d.line([cx, cy - r, cx, cy + r], fill=col, width=2)
        elif kind == "star":
            self.marker(x, y, "x", col, r)
            self.marker(x, y, "plus", col, r)
        elif kind == "square":
            d.rectangle([cx - r, cy - r, cx + r, cy + r], outline=col, width=2)
            self.marker(x, y, "x", col, r)
        elif kind == "tri_up":
            d.polygon([(cx, cy - r), (cx + r, cy + r * 0.7), (cx - r, cy + r * 0.7)], outline=col, width=2)
        elif kind == "tri_down":
            d.polygon([(cx, cy + r), (cx + r, cy - r * 0.7), (cx - r, cy - r * 0.7)], outline=col, width=2)

    def text(self, x, y, s, col=(0, 0, 0)):
        self.d.text(self.px(x, y), s, fill=col)


def to_pt(mp, v):
    a, b = mp
    return (v - a) / b


class Ours:
    def __init__(self, s):
        self.idx = {(r["mechanism"], r["method"], round(100 * r["level"]), r["variable"], r["quantity"]): r["value"]
                    for r in s["summary"]}
        self.truth = s["truth"]["mean"]
        self.se = s["truth"]["empirical_se"]

    def series(self, mech, method, var, qty):
        pts = []
        if method in ("CC", "SI"):
            v = self.idx.get(("NONE", "FULL", 0, var, qty))
            if v is not None:
                pts.append((0, v))
        for lev in LEVELS:
            v = self.idx.get((mech, method, lev, var, qty))
            if v is not None:
                pts.append((lev, v))
        return pts


def published_raster(page, clip):
    pm = page.get_pixmap(matrix=pymupdf.Matrix(SCALE, SCALE), clip=clip)
    return Image.frombytes("RGB", (pm.width, pm.height), pm.samples)


def lighten(img, keep=0.35):
    a = np.asarray(img.convert("L")).astype(float)
    a = 255 - (255 - a) * keep
    return Image.fromarray(a.astype(np.uint8)).convert("RGB")


# ---------------------------------------------------------------- our figure on the paper's own page

LW = 0.454          # the published series line width (pt)
DASH = "[1.9 1.77] 0"  # the published reference-line dash pattern (pt)


def data_drawings(page, fig, pub):
    """Indices of the page's drawings that carry plotted data: series lines and markers, dashed
    reference lines, histogram bars. Everything else (axes, ticks, labels, titles, legend) stays."""
    drs = page.get_drawings()
    segs = X.segments(page)
    F = pub["figures"][f"fig{fig}"]
    erase = set()
    for name, p in F["panels"].items():
        ax = p["axes"]
        ytk, xtk = ax["y_ticks"], ax["x_ticks"]
        x0, x1 = ax["y_axis_x"] + 0.5, max(xtk) + 12
        y0, y1 = min(ytk) - 30, ax["x_axis_y"] - 0.5

        def inside(x, y):
            return x0 <= x <= x1 and y0 <= y <= y1
        if fig == 1:
            base = max(ytk)
            for (a, b, h) in p["bars"]:
                xa, xb, yh = to_pt(p["x_map"], a), to_pt(p["x_map"], b), to_pt(p["y_map"], h)
                for sg in segs:
                    if not X.is_black(sg["col"]):
                        continue
                    if abs(sg["x0"] - sg["x1"]) < X.EPS and min(abs(sg["x0"] - xa), abs(sg["x0"] - xb)) < 0.3 \
                            and abs(max(sg["y0"], sg["y1"]) - base) < 0.6:
                        erase.add(sg["order"])
                    if abs(sg["y0"] - sg["y1"]) < X.EPS and abs(sg["y0"] - yh) < 0.3 \
                            and min(sg["x0"], sg["x1"]) > xa - 0.3 and max(sg["x0"], sg["x1"]) < xb + 0.3:
                        erase.add(sg["order"])
            continue
        grid = [to_pt(p["x_map"], v) for v in X.DATA_X]
        on_grid = lambda x: min(abs(x - g) for g in grid) < 0.6
        dashes = {}
        for sg in segs:
            mx, my = (sg["x0"] + sg["x1"]) / 2, (sg["y0"] + sg["y1"]) / 2
            if sg["col"] is None or not inside(mx, my):
                continue
            if not X.is_black(sg["col"]):
                erase.add(sg["order"])
            elif X.length(sg) >= 5 and on_grid(sg["x0"]) and on_grid(sg["x1"]):
                erase.add(sg["order"])
            elif abs(sg["y0"] - sg["y1"]) < X.EPS and X.length(sg) < 12:
                dashes.setdefault("all", []).append((sg["y0"], sg["order"]))
        # dashed lines: clusters of short horizontal segments at one height (within 0.3 pt)
        cluster, last = [], None
        for y, o in sorted(dashes.get("all", [])) + [(1e9, None)]:
            if last is not None and y - last > 0.3:
                if len(cluster) >= 8:
                    erase.update(cluster)
                cluster = []
            cluster.append(o)
            last = y
        cc = [(to_pt(p["x_map"], x), to_pt(p["y_map"], y)) for x, y in p["series"].get("CC", [])]
        for i, d in enumerate(drs):
            r = d["rect"]
            cx, cy = (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2
            if not inside(cx, cy) or r.width > 9 or r.height > 9:
                continue
            col = d.get("color") or d.get("fill")
            kinds = {it[0] for it in d["items"]}
            if col is not None and not X.is_black(tuple(round(c, 2) for c in col)):
                erase.add(i)          # coloured markers
            elif "c" in kinds and any(abs(cx - a) < 3 and abs(cy - b) < 3 for a, b in cc):
                erase.add(i)          # CC's circles
    return erase


def white_out(shape, d, extra=0.9):
    """Paint one drawing over in white, slightly wider than drawn."""
    w = (d.get("width") or 0.3) + extra
    for it in d["items"]:
        if it[0] == "l":
            shape.draw_line(it[1], it[2])
        elif it[0] == "c":
            shape.draw_bezier(it[1], it[2], it[3], it[4])
        elif it[0] == "re":
            shape.draw_rect(it[1])
        elif it[0] == "qu":
            shape.draw_quad(it[1])
    filled = d["type"] in ("f", "fs")
    shape.finish(color=(1, 1, 1), fill=(1, 1, 1) if filled else None, width=w, closePath=False, lineCap=1)


def redraw(shape, d):
    """Draw one of the page's drawings again with its own style."""
    for it in d["items"]:
        if it[0] == "l":
            shape.draw_line(it[1], it[2])
        elif it[0] == "c":
            shape.draw_bezier(it[1], it[2], it[3], it[4])
        elif it[0] == "re":
            shape.draw_rect(it[1])
        elif it[0] == "qu":
            shape.draw_quad(it[1])
    filled = d["type"] in ("f", "fs")
    stroked = d["type"] in ("s", "fs")
    shape.finish(color=d.get("color") if stroked else None, fill=d.get("fill") if filled else None,
                 width=d.get("width") or 0, closePath=d.get("closePath", False))


def vector_marker(shape, x, y, kind, col):
    P = pymupdf.Point
    if kind == "circle":
        shape.draw_circle(P(x, y), 1.15)
    elif kind in ("x", "star", "square"):
        shape.draw_line(P(x - 1.35, y - 1.35), P(x + 1.35, y + 1.35))
        shape.draw_line(P(x - 1.35, y + 1.35), P(x + 1.35, y - 1.35))
    if kind in ("plus", "star"):
        shape.draw_line(P(x - 1.82, y), P(x + 1.82, y))
        shape.draw_line(P(x, y - 1.82), P(x, y + 1.82))
    if kind == "square":
        shape.draw_rect(pymupdf.Rect(x - 1.35, y - 1.35, x + 1.35, y + 1.35))
    if kind == "tri_up":
        shape.draw_polyline([P(x, y - 1.55), P(x + 1.82, y + 1.0), P(x - 1.82, y + 1.0), P(x, y - 1.55)])
    if kind == "tri_down":
        shape.draw_polyline([P(x, y + 1.55), P(x + 1.82, y - 1.0), P(x - 1.82, y - 1.0), P(x, y + 1.55)])
    shape.finish(color=col, width=LW, closePath=False)


def ours_on_published(doc, fig, pub, ours, targets):
    """The paper's page with its plotted data taken out and ours drawn in, rasterised like the paper."""
    src = doc[PAGES[fig]]
    erase = data_drawings(src, fig, pub)
    drs = src.get_drawings()
    nd = pymupdf.open()
    pg = nd.new_page(width=src.rect.width, height=src.rect.height)
    pg.show_pdf_page(pg.rect, doc, PAGES[fig])
    sh = pg.new_shape()
    for i in sorted(erase):
        white_out(sh, drs[i])
    sh.commit()
    # put back the plot boxes and axis lines the white-out may have nicked
    sh = pg.new_shape()
    for i, d in enumerate(drs):
        r = d["rect"]
        col = d.get("color") or d.get("fill")
        if i in erase or col is None or not X.is_black(tuple(round(c, 2) for c in col)):
            continue
        if max(r.width, r.height) > 15 and (d["type"] in ("s", "fs") or min(r.width, r.height) < 1.5):
            redraw(sh, d)
    sh.commit()
    sh = pg.new_shape()
    P = pymupdf.Point
    F = pub["figures"][f"fig{fig}"]
    if fig == 1:
        for name, p in F["panels"].items():
            h = targets["histograms"][name]
            base = to_pt(p["y_map"], 0)
            for a, b, n in zip(h["breaks"], h["breaks"][1:], h["counts"]):
                if n == 0:
                    continue
                xa, xb, yh = to_pt(p["x_map"], a), to_pt(p["x_map"], b), to_pt(p["y_map"], n)
                sh.draw_polyline([P(xa, base), P(xa, yh), P(xb, yh), P(xb, base)])
                sh.finish(color=(0, 0, 0), width=LW, closePath=False)
    else:
        legend = {e["label"]: e for e in F["legend"]}
        for name, p in F["panels"].items():
            xs = (to_pt(p["x_map"], -3.0), to_pt(p["x_map"], 78.0))
            for r in reference_lines(fig, name, ours):
                y = to_pt(p["y_map"], r)
                sh.draw_line(P(xs[0], y), P(xs[1], y))
                sh.finish(color=(0, 0, 0), width=LW, dashes=DASH)
            for label, e in legend.items():
                mech, method = label.split(":") if ":" in label else ("MAR", label)
                var, qty = ("model", name) if fig == 6 else (name, QTY[fig])
                pts = ours.series(mech, method, var, qty)
                if not pts:
                    continue
                q = [P(to_pt(p["x_map"], x), to_pt(p["y_map"], v)) for x, v in pts]
                col = tuple(e["col"])
                sh.draw_polyline(q)
                sh.finish(color=col, width=LW, closePath=False)
                for pt in q:
                    vector_marker(sh, pt.x, pt.y, e["marker"], col)
    sh.commit()
    return published_raster(pg, figure_clip(src, fig))


def reference_lines(fig, name, ours):
    if fig in (2, 7):
        t, se = ours.truth[name], ours.se[name]
        return [t - 0.5 * se, t, t + 0.5 * se]
    if fig == 3:
        return [ours.se[name]]
    if fig in (4, 8):
        return [80, 90, 95]
    if fig == 5:
        return [0.05]
    return []


def render_lines(fig, page, pub, ours, out):
    F = pub["figures"][f"fig{fig}"]
    clip = figure_clip(page, fig)
    pubimg = published_raster(page, clip)
    legend = {e["label"]: e for e in F["legend"]}
    over = Canvas(clip, lighten(pubimg))
    for name, p in F["panels"].items():
        xs = (min(p["axes"]["x_ticks"]) - 4, max(p["axes"]["x_ticks"]) + 4)
        # our reference lines
        if fig in (2, 7):
            t, se = ours.truth[name], ours.se[name]
            refs = [t - 0.5 * se, t, t + 0.5 * se]
        elif fig == 3:
            refs = [ours.se[name]]
        elif fig in (4, 8):
            refs = [80, 90, 95]
        elif fig == 5:
            refs = [0.05]
        else:
            refs = []
        for r in refs:
            y = to_pt(p["y_map"], r)
            over.line([(xs[0], y), (xs[1], y)], MAGENTA, 1, dash=4)
        for label, e in legend.items():
            mech, method = label.split(":") if ":" in label else ("MAR", label)
            var, qty = ("model", name) if fig == 6 else (name, QTY[fig])
            pts = ours.series(mech, method, var, qty)
            if not pts:
                continue
            q = [(to_pt(p["x_map"], x), to_pt(p["y_map"], v)) for x, v in pts]
            over.line(q, MAGENTA, 2)
            for (x, y) in q:
                over.marker(x, y, e["marker"], MAGENTA, 4)
    pubimg.save(out / f"fig{fig}_published.png", optimize=True)
    over.img.save(out / f"fig{fig}_overlay.png", optimize=True)


def render_hist(page, pub, t, out):
    F = pub["figures"]["fig1"]
    clip = figure_clip(page, 1)
    pubimg = published_raster(page, clip)
    over = Canvas(clip, lighten(pubimg))
    for name, p in F["panels"].items():
        h = t["histograms"][name]
        base = to_pt(p["y_map"], 0)
        for a, b, n in zip(h["breaks"], h["breaks"][1:], h["counts"]):
            if n == 0:
                continue
            x0, x1 = to_pt(p["x_map"], a), to_pt(p["x_map"], b)
            y = to_pt(p["y_map"], n)
            box = [(x0, base), (x0, y), (x1, y), (x1, base)]
            over.line(box, MAGENTA, 2)
    pubimg.save(out / "fig1_published.png", optimize=True)
    over.img.save(out / "fig1_overlay.png", optimize=True)


def main():
    pdf, pubf, sumf, tf, out = sys.argv[1:6]
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(pdf)
    pub = json.load(open(pubf))
    ours = Ours(json.load(open(sumf)))
    targets = json.load(open(tf))
    render_hist(doc[PAGES[1]], pub, targets, out)
    for fig in range(2, 9):
        render_lines(fig, doc[PAGES[fig]], pub, ours, out)
    # our figures on the paper's own pages
    for fig in range(1, 9):
        ours_on_published(doc, fig, pub, ours, targets).save(out / f"fig{fig}_ours.png", optimize=True)


if __name__ == "__main__":
    main()

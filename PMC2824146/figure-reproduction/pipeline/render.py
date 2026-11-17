"""Draw our Figures 1 to 8 on the published figures' own axes, and overlay them on the published ones.

The published figure is the vector drawing in the article PDF, rasterised here at 2x (144 dpi).
Each panel's data-to-point map comes from its tick marks (extract_published.py), so our points land
where the paper's would for the same values.

  fig<N>_ours.png     our series, reference lines and bars on the published axes (white background)
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


def draw_axes(c, p):
    ax = p["axes"]
    x = ax["y_axis_x"]
    c.line([(x, min(ax["y_ticks"])), (x, max(ax["y_ticks"]))], (0, 0, 0), 1)
    for t in ax["y_ticks"]:
        c.line([(x - 3.6, t), (x, t)], (0, 0, 0), 1)
    y = ax["x_axis_y"]
    c.line([(min(ax["x_ticks"]), y), (max(ax["x_ticks"]), y)], (0, 0, 0), 1)
    for t in ax["x_ticks"]:
        c.line([(t, y), (t, y + 3.6)], (0, 0, 0), 1)
    for t, v in zip(ax["y_ticks"], tick_labels(p["y_map"], ax["y_ticks"])):
        c.text(x - 30, t - 4, v)
    for t, v in zip(ax["x_ticks"], tick_labels(p["x_map"], ax["x_ticks"])):
        c.text(t - 4, y + 5, v)


def tick_labels(mp, ticks):
    """The printed tick values: the fitted map rounded to the tick step."""
    a, b = mp
    vals = [a + b * t for t in ticks]
    step = float(f"{abs(vals[1] - vals[0]):.2g}")
    return [f"{round(v / step) * step:.6g}" for v in vals]


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


def render_lines(fig, page, pub, ours, out):
    F = pub["figures"][f"fig{fig}"]
    clip = figure_clip(page, fig)
    pubimg = published_raster(page, clip)
    legend = {e["label"]: e for e in F["legend"]}
    mine = Canvas(clip, Image.new("RGB", pubimg.size, "white"))
    over = Canvas(clip, lighten(pubimg))
    for name, p in F["panels"].items():
        draw_axes(mine, p)
        mine.text(p["axes"]["y_axis_x"] + 8, min(p["axes"]["y_ticks"]) - 2, name)
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
            for cv, col in ((mine, (0, 0, 0)), (over, MAGENTA)):
                cv.line([(xs[0], y), (xs[1], y)], col, 1, dash=4)
        for label, e in legend.items():
            mech, method = label.split(":") if ":" in label else ("MAR", label)
            var, qty = ("model", name) if fig == 6 else (name, QTY[fig])
            pts = ours.series(mech, method, var, qty)
            if not pts:
                continue
            q = [(to_pt(p["x_map"], x), to_pt(p["y_map"], v)) for x, v in pts]
            col = tuple(int(255 * c) for c in e["col"])
            mine.line(q, col, 2)
            over.line(q, MAGENTA, 2)
            for (x, y) in q:
                mine.marker(x, y, e["marker"], col)
                over.marker(x, y, e["marker"], MAGENTA, 4)
    pubimg.save(out / f"fig{fig}_published.png", optimize=True)
    # legend under the panels
    bottom = max(p["axes"]["x_axis_y"] for p in F["panels"].values()) + 34
    left = min(p["axes"]["y_axis_x"] for p in F["panels"].values())
    for k, (label, e) in enumerate(legend.items()):
        x0 = left + 190 * (k // 4)
        y0 = bottom + 14 * (k % 4)
        col = tuple(int(255 * c) for c in e["col"])
        mine.line([(x0, y0), (x0 + 30, y0)], col, 2)
        mine.marker(x0 + 15, y0, e["marker"], col)
        mech, _, meth = label.rpartition(":")
        mine.text(x0 + 36, y0 - 5, (f"{mech} - " if mech else "") + NAMES.get(meth, meth) + " (our run)")
    mine.img.save(out / f"fig{fig}_ours.png", optimize=True)
    over.img.save(out / f"fig{fig}_overlay.png", optimize=True)


def render_hist(page, pub, t, out):
    F = pub["figures"]["fig1"]
    clip = figure_clip(page, 1)
    pubimg = published_raster(page, clip)
    mine = Canvas(clip, Image.new("RGB", pubimg.size, "white"))
    over = Canvas(clip, lighten(pubimg))
    for name, p in F["panels"].items():
        draw_axes(mine, p)
        mine.text(p["axes"]["y_axis_x"] + 8, min(p["axes"]["y_ticks"]) - 14, name)
        h = t["histograms"][name]
        base = to_pt(p["y_map"], 0)
        for a, b, n in zip(h["breaks"], h["breaks"][1:], h["counts"]):
            if n == 0:
                continue
            x0, x1 = to_pt(p["x_map"], a), to_pt(p["x_map"], b)
            y = to_pt(p["y_map"], n)
            box = [(x0, base), (x0, y), (x1, y), (x1, base)]
            mine.line(box, (0, 0, 0), 2)
            over.line(box, MAGENTA, 2)
    pubimg.save(out / "fig1_published.png", optimize=True)
    mine.img.save(out / "fig1_ours.png", optimize=True)
    over.img.save(out / "fig1_overlay.png", optimize=True)


def main():
    pdf, pubf, sumf, tf, out = sys.argv[1:6]
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(pdf)
    pub = json.load(open(pubf))
    ours = Ours(json.load(open(sumf)))
    render_hist(doc[PAGES[1]], pub, json.load(open(tf)), out)
    for fig in range(2, 9):
        render_lines(fig, doc[PAGES[fig]], pub, ours, out)


if __name__ == "__main__":
    main()

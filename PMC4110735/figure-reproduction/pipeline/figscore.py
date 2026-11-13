"""Pixel scoring of a redrawn figure on the published figure's own pixel grid (figure-scoring.md).

The pixel-to-data map of a panel comes from its axes alone: the box (the frame lines) and the tick marks on
the bottom and left edges, fitted to the printed tick labels. Nothing inside the box is fitted.
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

TOL = 2  # px, at the published 1200-px width


def load_rgb(path):
    return np.asarray(Image.open(path).convert("RGB")).astype(int)


def frame_box(img, dark=100, frac=0.5):
    """Outer frame of the axes: the long dark rows and columns. Returns (x0, x1, y0, y1) at line centres."""
    g = img.mean(2) < dark
    rows = np.where(g.sum(1) > frac * img.shape[1])[0]
    cols = np.where(g.sum(0) > frac * img.shape[0])[0]

    def ends(v):
        groups = np.split(v, np.where(np.diff(v) > 1)[0] + 1)
        return float(np.mean(groups[0])), float(np.mean(groups[-1]))

    x0, x1 = ends(cols)
    y0, y1 = ends(rows)
    return x0, x1, y0, y1


def tick_groups(img, box, edge, dark=100, depth=22, minrun=7):
    """Centres of tick-like dark runs along one edge of the box: 'bottom', 'top', 'left' or 'right'."""
    x0, x1, y0, y1 = [int(round(v)) for v in box]
    g = img.mean(2) < dark
    if edge in ("bottom", "top"):
        band = g[y1 - depth: y1 - 2, :] if edge == "bottom" else g[y0 + 3: y0 + depth, :]
        run, lo, hi = band.sum(0), x0 + 4, x1 - 4
    else:
        band = g[:, x0 + 3: x0 + depth] if edge == "left" else g[:, x1 - depth: x1 - 2]
        run, lo, hi = band.sum(1), y0 + 4, y1 - 4
    idx = np.where(run >= minrun)[0]
    idx = idx[(idx > lo) & (idx < hi)]
    if not len(idx):
        return []
    return [float(np.mean(gp)) for gp in np.split(idx, np.where(np.diff(idx) > 1)[0] + 1)]


def match_ticks(img, box, axis, values, lim, search=6):
    """Pixel positions of the expected ticks: the detected tick nearest each position predicted from the box.

    Ticks on both edges of the axis are searched; a tick counts when it is found within `search` px.
    Returns [(value, pixel)]."""
    x0, x1, y0, y1 = box
    if axis == "x":
        found = tick_groups(img, box, "bottom") + tick_groups(img, box, "top")
        pred = lambda v: x0 + (v - lim[0]) / (lim[1] - lim[0]) * (x1 - x0)
    else:
        found = tick_groups(img, box, "left") + tick_groups(img, box, "right")
        pred = lambda v: y1 - (v - lim[0]) / (lim[1] - lim[0]) * (y1 - y0)
    out = []
    for v in values:
        p = pred(v)
        near = [f for f in found if abs(f - p) <= search]
        if near and lim[0] < v < lim[1]:
            out.append((v, min(near, key=lambda f: abs(f - p))))
    return out


def fit_axis(pixels, values):
    """Least-squares line value -> pixel; returns (slope, intercept, max residual in px)."""
    p, v = np.asarray(pixels, float), np.asarray(values, float)
    A = np.c_[v, np.ones_like(v)]
    (a, b), *_ = np.linalg.lstsq(A, p, rcond=None)
    res = float(np.max(np.abs(A @ [a, b] - p))) if len(p) > 2 else 0.0
    return float(a), float(b), res


class Mapping:
    """Data -> pixel for one panel, from the frame box (at the axis limits) and the tick marks."""

    def __init__(self, img, xlim, ylim, xticks=None, yticks=None):
        self.box = frame_box(img)
        x0, x1, y0, y1 = self.box
        xp, xv = [x0, x1], list(xlim)
        yp, yv = [y1, y0], list(ylim)
        self.tick_check = {}
        for axis, vals in (("x", xticks), ("y", yticks)):
            if vals is None:
                continue
            lim = xlim if axis == "x" else ylim
            inner = [v for v in vals if lim[0] < v < lim[1]]
            got = match_ticks(img, self.box, axis, inner, lim)
            self.tick_check[axis] = {"matched": len(got), "expected": len(inner)}
            if axis == "x":
                xv += [v for v, _ in got]
                xp += [p for _, p in got]
            else:
                yv += [v for v, _ in got]
                yp += [p for _, p in got]
        self.ax, self.bx, self.rx = fit_axis(xp, xv)
        self.ay, self.by, self.ry = fit_axis(yp, yv)

    def __call__(self, x, y):
        return self.ax * np.asarray(x, float) + self.bx, self.ay * np.asarray(y, float) + self.by

    def info(self):
        return {"box": [round(v, 1) for v in self.box], "x_fit_residual_px": round(self.rx, 2),
                "y_fit_residual_px": round(self.ry, 2), "ticks": self.tick_check}


def draw_series(shape, pts, width=3, marker=None, msize=10, mwidth=2, canvas=None, colour=0):
    """Draw a polyline (and markers) into a greyscale canvas; returns the canvas (0 = ink)."""
    if canvas is None:
        canvas = Image.new("L", (shape[1], shape[0]), 255)
    d = ImageDraw.Draw(canvas)
    xy = [tuple(p) for p in pts]
    if width:
        d.line(xy, fill=colour, width=width, joint="curve")
    for x, y in xy:
        r = msize / 2
        if marker == "o":
            d.ellipse([x - r, y - r, x + r, y + r], outline=colour, width=mwidth)
        elif marker == "*":
            for ang in (0, 45, 90, 135):
                dx, dy = r * np.cos(np.radians(ang)), r * np.sin(np.radians(ang))
                d.line([(x - dx, y - dy), (x + dx, y + dy)], fill=colour, width=mwidth)
        elif marker == "d":
            d.polygon([(x, y - r), (x + r, y), (x, y + r), (x - r, y)], outline=colour, width=mwidth)
    return canvas


def two_way(pub_mask, our_mask, tol=TOL):
    """(share of published trace pixels within tol of ours, share of ours within tol of published)."""
    if not pub_mask.any() or not our_mask.any():
        return 0.0, 0.0
    d_our = ndimage.distance_transform_edt(~our_mask)
    d_pub = ndimage.distance_transform_edt(~pub_mask)
    return float((d_our[pub_mask] <= tol).mean()), float((d_pub[our_mask] <= tol).mean())


def score(pub_mask, our_mask, tol=TOL):
    a, b = two_way(pub_mask, our_mask, tol)
    return {"published_near_ours": round(a, 4), "ours_near_published": round(b, 4), "score": round(min(a, b), 4)}


def save_ours(img, pub_mask, our_masks_colours, path):
    """Published figure with the published traces removed and ours drawn in their colours."""
    out = img.copy()
    out[pub_mask] = 255
    for m, col in our_masks_colours:
        out[m] = col
    Image.fromarray(out.astype(np.uint8)).save(path)


def save_overlay(img, pub_mask, our_mask, path):
    """Published (grey) with ours on top: red = ours only, cyan = published only, black = both."""
    g = img.mean(2)
    out = np.stack([g, g, g], 2) * 0.35 + 255 * 0.65
    both = pub_mask & our_mask
    out[pub_mask & ~our_mask] = (0, 170, 200)
    out[our_mask & ~pub_mask] = (220, 30, 30)
    out[both] = (0, 0, 0)
    Image.fromarray(out.astype(np.uint8)).save(path)

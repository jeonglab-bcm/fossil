"""Draw our series on the published figures' own pixel grid and score them against the
published traces.

The main figures are Excel 2007 charts (white plot area, grey gridlines at every y tick, coloured
smoothed lines with markers); the supplementary figures S1-S3 are Matlab plots (black box, one
dot per protein pair). Each panel's pixel-to-data map comes from its gridlines (Excel) or its box
(Matlab) and the printed axis limits; nothing inside the plot is fitted.

Scoring: a published series is the set of pixels of its colour, opened with a 3 x 3 square so that
thin annotation arrows and anti-aliasing fringes drop out; markers (blobs that survive an opening
wider than the line) are masked in both images, and so is the legend. Our series is drawn at the
measured published line width. Two shares are computed with a pixel tolerance: published pixels
within tolerance of ours, and our pixels within tolerance of the published figure (any series,
because later Excel series hide earlier ones). The score is the smaller share, pooled over the
series of a panel.
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

TOL_PX = 2


def load(path):
    return np.asarray(Image.open(path).convert("RGB")).astype(np.int16)


def grey_mask(a, level=134, tol=12):
    return (np.abs(a - level) <= tol).all(axis=2)


def runs(idx):
    """Centres of runs of consecutive integers."""
    if len(idx) == 0:
        return []
    groups = np.split(idx, np.flatnonzero(np.diff(idx) > 1) + 1)
    return [float(g.mean()) for g in groups]


def longest_run(row):
    """(start, end) of the longest run of True in a boolean row."""
    idx = np.flatnonzero(row)
    groups = np.split(idx, np.flatnonzero(np.diff(idx) > 1) + 1)
    g = max(groups, key=len)
    return int(g[0]), int(g[-1])


def excel_axes(a, box, yticks, xlim, grey=134, tol=40, frac=0.3):
    """Pixel map of an Excel plot area inside box (x0, y0, x1, y1). Horizontal gridlines are the
    rows of the box that are mostly gridline grey (adjacent rows of an anti-aliased line merge);
    they are matched to yticks (bottom to top) and fitted with a line. The plot area spans from
    the vertical axis line to the gridlines' right end, which are xlim[0] and xlim[1]."""
    x0, y0, x1, y1 = box
    sub = grey_mask(a[y0:y1, x0:x1], grey, tol) & (a[y0:y1, x0:x1].max(axis=2) - a[y0:y1, x0:x1].min(axis=2) < 10)
    rows = np.flatnonzero(sub.sum(axis=1) > frac * (x1 - x0))
    centres = runs(rows)
    if len(centres) != len(yticks):
        raise ValueError(f"found {len(centres)} gridlines, expected {len(yticks)}")
    ys = np.array(sorted(yticks, reverse=True), dtype=float)
    py = np.array(centres) + y0
    A = np.vstack([ys, np.ones_like(ys)]).T
    (ay, by), *_ = np.linalg.lstsq(A, py, rcond=None)
    resid = float(np.abs(A @ np.array([ay, by]) - py).max())
    top, bottom = int(py.min()), int(py.max())
    span = sub[top - y0:bottom - y0 + 1]
    cols = np.flatnonzero(span.sum(axis=0) > 0.6 * span.shape[0])
    spans = [longest_run(sub[int(round(r)) - y0]) for r in py]  # the gridline itself, not labels
    right = float(max(e for _, e in spans) + x0)
    # x = xlim[0] is the vertical axis line: of the columns that are mostly grey over the
    # gridlines' height, the one nearest to where the gridlines start
    start = float(np.median([b for b, _ in spans]) + x0)
    cand = [c + x0 for c in runs(cols)]
    left = min(cand, key=lambda c: abs(c - start)) if cand else start
    ax = (right - left) / (xlim[1] - xlim[0])
    bx = left - ax * xlim[0]
    return {"ax": ax, "bx": bx, "ay": ay, "by": by, "residual_px": resid, "left": left,
            "right": right, "top": top, "bottom": bottom}


def matlab_axes(a, box, xlim, ylim):
    """Pixel map of a Matlab axes box: its black frame is the axis limits."""
    x0, y0, x1, y1 = box
    blk = (a[y0:y1, x0:x1] < 60).all(axis=2)
    rows = np.flatnonzero(blk.sum(axis=1) > 0.6 * (x1 - x0))
    cols = np.flatnonzero(blk.sum(axis=0) > 0.6 * (y1 - y0))
    top, bottom = runs(rows)[0] + y0, runs(rows)[-1] + y0
    left, right = runs(cols)[0] + x0, runs(cols)[-1] + x0
    ax = (right - left) / (xlim[1] - xlim[0])
    ay = (top - bottom) / (ylim[1] - ylim[0])
    return {"ax": ax, "bx": left - ax * xlim[0], "ay": ay, "by": bottom - ay * ylim[0],
            "residual_px": 0.0, "left": left, "right": right, "top": top, "bottom": bottom}


def to_px(cal, x, y):
    return cal["ax"] * np.asarray(x, float) + cal["bx"], cal["ay"] * np.asarray(y, float) + cal["by"]


def colour_mask(a, rgb, tol=60):
    d = np.sqrt(((a - np.array(rgb)) ** 2).sum(axis=2))
    sat = a.max(axis=2) - a.min(axis=2)
    return (d <= tol) & (sat >= 40)


def series_mask(a, rgb, region, tol=60, open_px=3):
    m = colour_mask(a, rgb, tol) & region
    if open_px > 1:
        m = ndimage.binary_opening(m, np.ones((open_px, open_px), bool))
    return m


def line_width(mask):
    """Median vertical run length of a trace in columns where it crosses once (flat parts)."""
    lengths = []
    for c in range(mask.shape[1]):
        col = np.flatnonzero(mask[:, c])
        if col.size and np.all(np.diff(col) == 1):
            lengths.append(col.size)
    return float(np.median(lengths)) if lengths else 3.0


def marker_mask(mask, width, pad=3):
    """Blobs wider than the line: markers."""
    k = int(round(width)) + 3
    blobs = ndimage.binary_opening(mask, np.ones((k, k), bool))
    return ndimage.binary_dilation(blobs, iterations=pad)


def catmull_rom(px, py, n=24):
    """Excel's smoothed line: a Catmull-Rom (Bezier, tension 1/6) curve through the points."""
    P = np.c_[px, py]
    if len(P) < 3:
        return P
    keep = np.r_[True, np.any(np.diff(P, axis=0) != 0, axis=1)]
    P = P[keep]  # repeated points make the spline overshoot
    if len(P) < 3:
        return P
    P = np.vstack([P[0], P, P[-1]])
    out = []
    t = np.linspace(0, 1, n, endpoint=False)[:, None]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        c1 = p1 + (p2 - p0) / 6
        c2 = p2 - (p3 - p1) / 6
        out.append((1 - t) ** 3 * p1 + 3 * (1 - t) ** 2 * t * c1 + 3 * (1 - t) * t ** 2 * c2 + t ** 3 * p2)
    out.append(P[-2][None, :])
    return np.vstack(out)


def draw_series(shape, cal, x, y, width, smooth=True, clip=None, dots=False):
    """Boolean mask of a series drawn at the given width (a polyline, or dots for Matlab '.')."""
    im = Image.new("L", (shape[1], shape[0]), 0)
    dr = ImageDraw.Draw(im)
    px, py = to_px(cal, x, y)
    if clip is not None:
        py = np.clip(py, clip[0], clip[1])
    if dots:
        r = width / 2
        for a, b in zip(px, py):
            dr.ellipse([a - r, b - r, a + r, b + r], fill=255)
    else:
        pts = catmull_rom(px, py) if smooth else np.c_[px, py]
        dr.line([tuple(p) for p in pts], fill=255, width=max(1, int(round(width))), joint="curve")
        r = width / 2
        for p in (pts[0], pts[-1]):
            dr.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=255)
    return np.asarray(im) > 127


def draw_markers(shape, cal, x, y, size):
    im = Image.new("L", (shape[1], shape[0]), 0)
    dr = ImageDraw.Draw(im)
    px, py = to_px(cal, x, y)
    r = size / 2
    for a, b in zip(px, py):
        dr.ellipse([a - r, b - r, a + r, b + r], fill=255)
    return np.asarray(im) > 127


def shares(pub, ours, pub_any, exclude, tol=TOL_PX):
    """(published within tol of ours, ours within tol of the published figure), as fractions and
    pixel counts, outside the excluded pixels."""
    p = pub & ~exclude
    o = ours & ~exclude
    if not p.any() or not o.any():
        return 0.0, 0.0, int(p.sum()), int(o.sum())
    d_ours = ndimage.distance_transform_edt(~ours)
    d_pub = ndimage.distance_transform_edt(~pub_any)
    a = float((d_ours[p] <= tol).mean())
    b = float((d_pub[o] <= tol).mean())
    return a, b, int(p.sum()), int(o.sum())


def pooled_score(parts):
    """Pool per-series (share_a, share_b, n_pub, n_ours) into the panel's two shares."""
    na = sum(p[2] for p in parts)
    nb = sum(p[3] for p in parts)
    a = sum(p[0] * p[2] for p in parts) / na if na else 0.0
    b = sum(p[1] * p[3] for p in parts) / nb if nb else 0.0
    return a, b


def render(published, masks_pub, masks_ours, colours, path_ours, path_overlay):
    """fig*_ours.png: the published figure with its traces erased and ours drawn in the published
    colours. fig*_overlay.png: red channel published traces, green and blue channels ours (cyan =
    only in the paper, red = only ours, black = both)."""
    img = published.copy().astype(np.uint8)
    erase = np.zeros(published.shape[:2], bool)
    for m in masks_pub:
        erase |= ndimage.binary_dilation(m, iterations=2)
    img[erase] = 255
    for m, c in zip(masks_ours, colours):
        img[m] = c
    Image.fromarray(img).save(path_ours, optimize=True)
    pub = np.zeros(published.shape[:2], bool)
    for m in masks_pub:
        pub |= m
    ours = np.zeros(published.shape[:2], bool)
    for m in masks_ours:
        ours |= m
    grey = published.mean(axis=2)
    base = np.where(grey < 200, 200, 255).astype(np.uint8)  # axes and text in light grey
    ov = np.stack([base, base, base], axis=2)
    ov[pub, 0] = 0
    ov[ours, 1] = 0
    ov[ours, 2] = 0
    ov[pub & ~ours] = (0, 200, 200)
    ov[ours & ~pub] = (220, 0, 0)
    ov[pub & ours] = (0, 0, 0)
    Image.fromarray(ov).save(path_overlay, optimize=True)

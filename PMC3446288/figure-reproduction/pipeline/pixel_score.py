"""Draw our curves on a published panel's pixel grid and score them both ways.

Each panel config gives the axis calibration (data -> pixel), the panel box, regions to mask (legend,
labels) and, per series, the published colour and our data. The published trace of a series is the
set of pixels within a colour distance of its colour inside the panel; ours is our polyline drawn
at the published line width. Score = min(share of published pixels within TOL px of ours, share of
ours within TOL px of the published).
"""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

TOL = 3  # px on the 1200-px-wide published figures (about 0.15 mm at the printed size)


def load(path):
    return np.asarray(Image.open(path).convert("RGB")).astype(np.int16)


def colour_mask(img, rgb, dist, box, exclude=()):
    x0, y0, x1, y1 = box
    d = np.sqrt(((img - np.array(rgb)) ** 2).sum(axis=2))
    m = d < dist
    out = np.zeros(m.shape, bool)
    out[y0:y1, x0:x1] = m[y0:y1, x0:x1]
    for ex0, ey0, ex1, ey1 in exclude:
        out[ey0:ey1, ex0:ex1] = False
    return out


def polyline_mask(shape, pieces, width, box):
    """pieces: list of [(px, py), ...] polylines; drawn clipped to the panel box."""
    im = Image.new("L", (shape[1], shape[0]), 0)
    dr = ImageDraw.Draw(im)
    for pts in pieces:
        pts = [(float(x), float(y)) for x, y in pts if np.isfinite(x) and np.isfinite(y)]
        if len(pts) >= 2:
            dr.line(pts, fill=255, width=int(width), joint="curve")
    m = np.asarray(im) > 0
    x0, y0, x1, y1 = box
    clip = np.zeros_like(m)
    clip[y0:y1, x0:x1] = m[y0:y1, x0:x1]
    return clip


def two_way(pub, ours, tol=TOL):
    if pub.sum() == 0 or ours.sum() == 0:
        return 0.0, 0.0
    d_ours = ndimage.distance_transform_edt(~ours)
    d_pub = ndimage.distance_transform_edt(~pub)
    return float((d_ours[pub] <= tol).mean()), float((d_pub[ours] <= tol).mean())


def score(pub_masks: dict, our_masks: dict, tol=TOL):
    """Union over series of each series' pixels scored against the same series."""
    a_hits = a_n = b_hits = b_n = 0
    for k in pub_masks:
        p, o = pub_masks[k], our_masks[k]
        if p.sum() == 0 or o.sum() == 0:
            a_n += int(p.sum())
            b_n += int(o.sum())
            continue
        d_o = ndimage.distance_transform_edt(~o)
        d_p = ndimage.distance_transform_edt(~p)
        a_hits += int((d_o[p] <= tol).sum())
        a_n += int(p.sum())
        b_hits += int((d_p[o] <= tol).sum())
        b_n += int(o.sum())
    return (a_hits / a_n if a_n else 0.0), (b_hits / b_n if b_n else 0.0)


def render(img, pub_masks, our_masks, colours, out_ours, out_overlay):
    """Ours: our curves in the published colours on the panel with the published traces erased.
    Overlay: red channel = published, green and blue = ours (cyan only in the paper's... see README)."""
    base = img.astype(np.uint8).copy()
    erase = np.zeros(base.shape[:2], bool)
    for m in pub_masks.values():
        erase |= ndimage.binary_dilation(m, iterations=1)
    base[erase] = 255
    for k, m in our_masks.items():
        base[m] = colours[k]
    Image.fromarray(base).save(out_ours)
    g = img.mean(axis=2)
    pub_any = np.zeros(g.shape, bool)
    ours_any = np.zeros(g.shape, bool)
    for m in pub_masks.values():
        pub_any |= m
    for m in our_masks.values():
        ours_any |= m
    ov = np.full(img.shape, 255, np.uint8)
    light = (g < 200) & ~pub_any
    ov[light] = 200  # the rest of the published figure in grey
    ov[pub_any, 1:] = 0  # published only: red
    ov[pub_any, 0] = 255
    ov[ours_any & ~pub_any] = (0, 170, 255)  # ours only: blue-cyan
    ov[ours_any & pub_any] = (0, 0, 0)  # both: black
    Image.fromarray(ov).save(out_overlay)


def side_by_side(published_png, ours_png, out_png, height=None):
    """For panels compared by values: the published panel and ours next to each other."""
    a = Image.open(published_png).convert("RGB")
    b = Image.open(ours_png).convert("RGB")
    h = height or max(a.height, b.height)
    a = a.resize((int(a.width * h / a.height), h))
    b = b.resize((int(b.width * h / b.height), h))
    out = Image.new("RGB", (a.width + b.width + 20, h), "white")
    out.paste(a, (0, 0))
    out.paste(b, (a.width + 20, 0))
    out.save(out_png)

"""Shared pixel tools: masks, two-way tolerance scores, line rasterising, overlays."""
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt

TOL_PX = 2


def within(a, b, tol=TOL_PX):
    """Share of the True pixels of mask ``a`` within ``tol`` px of a True pixel of mask ``b``."""
    if not a.any():
        return float("nan")
    if not b.any():
        return 0.0
    d = distance_transform_edt(~b)
    return float((d[a] <= tol).mean())


def two_way(pub, ours, tol=TOL_PX):
    return {"published_near_ours": within(pub, ours, tol), "ours_near_published": within(ours, pub, tol)}


def score(pub, ours, tol=TOL_PX):
    s = two_way(pub, ours, tol)
    return min(s.values()), s


def line_mask(shape, xy_px, width=2):
    """Rasterise a polyline (list of (x, y) pixel coordinates) into a boolean mask."""
    im = Image.new("L", (shape[1], shape[0]), 0)
    if len(xy_px) >= 2:
        ImageDraw.Draw(im).line([tuple(map(float, p)) for p in xy_px], fill=255, width=width)
    return np.array(im) > 0


def overlay(published_gray, ours_mask, color=(220, 0, 0)):
    """Published image in grey with our trace on top in a contrasting colour."""
    base = np.stack([published_gray] * 3, axis=-1).astype(np.uint8)
    base[ours_mask] = color
    return Image.fromarray(base)


def draw_on(base_rgb, masks_colors):
    arr = np.array(base_rgb.convert("RGB"))
    for m, c in masks_colors:
        arr[m] = c
    return Image.fromarray(arr)

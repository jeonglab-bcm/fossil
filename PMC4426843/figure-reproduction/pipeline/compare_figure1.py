#!/usr/bin/env python3
"""Compare a reproduced base-R figure with the published image, pixel by pixel.

compare_figure.py from the Paper2Repro skill finds the plot panel by its grey fill (ggplot).
Figure 1 has a white panel, so the reproduction is instead drawn on the published pixel grid:
figure1.R places the plot region from the measured axis ticks, on a canvas padded above the
published frame (the published JPEG is cropped at the top). This script first crops the render to
the frame (--crop X Y W H). This script measures
what is left: a global shift (searched in a small window, expected 0), the mean grey
difference, the share of pixels within +-24 grey levels, and the chamfer distance between ink
pixels per region, plus overlay/diff images as in compare_figure.py (red channel = published,
green/blue = reproduction: cyan = ink only in the paper, red = ink only in the reproduction).

Usage: compare_figure1.py PUBLISHED RENDER REGIONS.json OUT_DIR [--crop X Y W H]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

INK = 170


def load(p: Path) -> np.ndarray:
    return np.asarray(Image.open(p).convert("L"), dtype=float)


def chamfer(a, b, mask):
    A, B = (a < INK) & mask, (b < INK) & mask
    if not A.any() or not B.any():
        return None
    dA = ndimage.distance_transform_edt(~A)
    dB = ndimage.distance_transform_edt(~B)
    return round(float((dB[A].mean() + dA[B].mean()) / 2), 3)


def shifted(img, dx, dy):
    out = np.full_like(img, 255.0)
    h, w = img.shape
    ys, ye = max(0, dy), min(h, h + dy)
    xs, xe = max(0, dx), min(w, w + dx)
    out[ys:ye, xs:xe] = img[ys - dy:ye - dy, xs - dx:xe - dx]
    return out


def best_shift(pub, ren, box, window=4):
    x0, x1, y0, y1 = box
    m = np.zeros(pub.shape, bool)
    m[y0:y1 + 1, x0:x1 + 1] = True
    best = None
    for dy in range(-window, window + 1):
        for dx in range(-window, window + 1):
            c = chamfer(pub, shifted(ren, dx, dy), m)
            if c is not None and (best is None or c < best[0]):
                best = (c, dx, dy)
    return {"dx": best[1], "dy": best[2], "chamfer_at_best": best[0],
            "at_window_edge": max(abs(best[1]), abs(best[2])) == window}


def compare(pub_path: Path, ren_path: Path, regions: list[dict], out: Path, crop=None) -> dict:
    pub, ren = load(pub_path), load(ren_path)
    if crop:
        x, y, w, h = crop
        ren = ren[y:y + h, x:x + w]
    if pub.shape != ren.shape:
        raise SystemExit(f"size differs: published {pub.shape[::-1]}, render {ren.shape[::-1]}")
    d = np.abs(pub - ren)
    rep = {
        "published": pub_path.name, "size_px": list(pub.shape[::-1]),
        "mean_abs_grey_difference": round(float(d.mean()), 3),
        "pixels_within_24_pct": round(float((d <= 24).mean() * 100), 2),
        "chamfer_all_px": chamfer(pub, ren, np.ones(pub.shape, bool)),
        "global_shift": best_shift(pub, ren, (0, pub.shape[1] - 1, 0, pub.shape[0] - 1)),
        "regions": {},
    }
    for r in regions:
        x0, x1, y0, y1 = r["box"]
        m = np.zeros(pub.shape, bool)
        m[y0:y1 + 1, x0:x1 + 1] = True
        rep["regions"][r["name"]] = {"chamfer_px": chamfer(pub, ren, m),
                                     "mean_abs_grey_difference": round(float(d[m].mean()), 3),
                                     "best_shift": best_shift(pub, ren, r["box"])}
    out.mkdir(parents=True, exist_ok=True)
    Image.fromarray(ren.clip(0, 255).astype(np.uint8)).save(out / "aligned.png")
    rgb = np.stack([pub, ren, ren], -1).clip(0, 255).astype(np.uint8)
    Image.fromarray(rgb).save(out / "overlay.png")
    Image.fromarray((255 - np.minimum(255, d * 2)).astype(np.uint8)).save(out / "diff.png")
    (out / "report.json").write_text(json.dumps(rep, indent=1) + "\n")
    return rep


if __name__ == "__main__":
    pub, ren, regions, out = sys.argv[1:5]
    crop = [int(v) for v in sys.argv[6:10]] if len(sys.argv) > 5 and sys.argv[5] == "--crop" else None
    rep = compare(Path(pub), Path(ren), json.loads(Path(regions).read_text()), Path(out), crop)
    print(json.dumps({k: rep[k] for k in ("mean_abs_grey_difference", "pixels_within_24_pct",
                                          "chamfer_all_px", "global_shift")}))
    for k, v in rep["regions"].items():
        print(f"  {k:10s} chamfer {v['chamfer_px']}  shift {v['best_shift']['dx']},{v['best_shift']['dy']}")

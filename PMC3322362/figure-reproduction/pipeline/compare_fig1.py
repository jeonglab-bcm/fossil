"""Compare the ROC curves of Fig. 1 with the published figure, curve by curve.

The published curves are traced by colour inside the axes box (blue: RPI2241, red: RPI369;
the legend and the AUC labels are masked). Our curves are mapped onto the same pixel grid
with the published axes calibration (params/fig1.json) and sampled every 0.25 px.

Reported per colour: the share of published curve pixels within 2 px of one of our two curves
of that colour, and per curve the share of our curve's samples within 2 px of a published
pixel of its colour.

Usage: python compare_fig1.py PARAMS.json PUBLISHED.jpg OUT.json RF2241.csv SVM2241.csv RF369.csv SVM369.csv
"""

import json
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, __import__("os").path.dirname(__file__))
from fig1 import roc  # noqa: E402


def polyline_px(fpr, tpr, P):
    x0, y0, x1, y1 = P["axes_px"]
    pts = []
    for (a, b), (c, d) in zip(zip(fpr[:-1], tpr[:-1]), zip(fpr[1:], tpr[1:])):
        xa, ya = x0 + a * (x1 - x0), y1 - b * (y1 - y0)
        xc, yc = x0 + c * (x1 - x0), y1 - d * (y1 - y0)
        n = max(2, int(np.hypot(xc - xa, yc - ya) * 4))
        t = np.linspace(0, 1, n)
        pts.append(np.c_[xa + t * (xc - xa), ya + t * (yc - ya)])
    return np.vstack(pts)


def main(params, published, out, *csvs):
    P = json.load(open(params))
    a = np.asarray(Image.open(published).convert("RGB")).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    x0, y0, x1, y1 = P["axes_px"]
    inside = np.zeros(r.shape, bool)
    inside[y0 + 2 : y1 - 1, x0 + 2 : x1 - 1] = True
    lx, ly = P["legend_corner_px"]
    inside[ly - 82 : ly + 2, lx - 146 : lx + 2] = False  # legend frame, 144 x 80 px
    masks = {
        "blue": inside & (b - np.maximum(r, g) > 40),
        "red": inside & (r - np.maximum(g, b) > 40),
    }
    result = {}
    curves = {}
    for spec, path in zip(P["curves"], csvs):
        fpr, tpr, auc = roc(path)
        colour = "blue" if spec["color"] == "#0000ff" else "red"
        curves[spec["label"]] = (colour, polyline_px(fpr, tpr, P))
    for colour, mask in masks.items():
        dist_pub = ndimage.distance_transform_edt(~mask)
        ours = np.zeros(mask.shape, bool)
        for label, (c, pts) in curves.items():
            if c != colour:
                continue
            xi = np.clip(np.round(pts[:, 0]).astype(int), 0, mask.shape[1] - 1)
            yi = np.clip(np.round(pts[:, 1]).astype(int), 0, mask.shape[0] - 1)
            ok = inside[yi, xi]
            near = dist_pub[yi[ok], xi[ok]] <= 2
            result[label] = {"ours_within_2px": float(near.mean())}
            ours[yi[ok], xi[ok]] = True
        dist_ours = ndimage.distance_transform_edt(~ours)
        result[colour] = {
            "published_pixels": int(mask.sum()),
            "published_within_2px": float((dist_ours[mask] <= 2).mean()),
        }
    json.dump(result, open(out, "w"), indent=2)


if __name__ == "__main__":
    main(*sys.argv[1:4], *sys.argv[4:8])

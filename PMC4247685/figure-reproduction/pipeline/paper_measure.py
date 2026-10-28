"""Measure the published Figs 3-5: plot frame, axis ticks and Kaplan-Meier step levels, in pixels.

Usage: python3 paper_measure.py <published dir> <out.json>
"""
import json
import sys

import numpy as np
from PIL import Image


def dark(path, level=128):
    return np.asarray(Image.open(path).convert("L")) < level


def frame(path, frac=0.6, level=200):
    """Centres of the plot frame lines (grey, antialiased) on each side, in pixels.

    A frame line is a run of rows (columns) whose ink covers at least frac of the image; its centre
    is the ink-weighted mean over that run. The first run from each edge is taken.
    """
    a = np.asarray(Image.open(path).convert("L"), dtype=float)
    h, w = a.shape
    inkw = np.clip(255.0 - a, 0, None)
    box = {}
    for axis, n, names in ((1, w, ("top", "bottom")), (0, h, ("left", "right"))):
        long_ = np.where(((a < level).sum(axis=axis)) > frac * n)[0]
        if not len(long_):
            continue
        groups = np.split(long_, np.where(np.diff(long_) > 1)[0] + 1)
        prof = inkw.sum(axis=axis)
        for name, g in ((names[0], groups[0]), (names[1], groups[-1])):
            lo, hi = max(0, g.min() - 1), g.max() + 2
            idx = np.arange(lo, hi)
            box[name] = round(float((prof[idx] * idx).sum() / prof[idx].sum()) + 0.5, 2)
    return box


def runs(mask):
    """Centres of consecutive True runs."""
    idx = np.where(mask)[0]
    if not len(idx):
        return []
    groups = np.split(idx, np.where(np.diff(idx) > 1)[0] + 1)
    return [float(g.mean()) for g in groups]


def ticks(d, box):
    """Tick marks: short dark runs just outside the left and bottom frame lines."""
    out = {}
    b, l = int(round(box["bottom"])), int(round(box["left"]))
    out["x"] = runs(d[b + 4: b + 14, :].sum(axis=0) >= 6)
    out["y"] = runs(d[:, max(0, l - 14): l - 4].sum(axis=1) >= 6)
    return out


def main():
    pub, out_path = sys.argv[1], sys.argv[2]
    res = {}
    for n in (3, 4, 5):
        img = f"{pub}/figure-{n}.png"
        box = frame(img)
        res[f"fig{n}"] = {"size": list(Image.open(img).size), "frame": box,
                          "ticks": ticks(dark(img, 200), box)}
    with open(out_path, "w") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()

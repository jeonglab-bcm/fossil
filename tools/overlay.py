"""Overlay each published figure with this run's render of it, for the PR comment.

A render (output/fig<N>_ours.png) sits on the published figure's pixel grid, so the two overlay
directly. Ink is any pixel darker than INK. Where the paper's ink and ours lie within 2 px of each
other the overlay is grey; ink only in the paper is drawn dark, ink only in this run green. The
overlay is shrunk to at most WIDTH px wide, keeping a thin line visible.

Usage: python3 tools/overlay.py <published dir> <run output dir> <out dir>
Writes <out dir>/fig<N>.png for every figure with a render, and <out dir>/overlays.json with each
figure's share of the paper's ink within 2 px of ours, and of ours within 2 px of the paper's.
"""
import glob
import json
import os
import re
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

INK = 150
WIDTH = 760
GREY, PAPER_ONLY, OURS_ONLY = (196, 201, 198), (22, 46, 40), (0, 150, 95)


def load(path):
    im = Image.open(path)
    if im.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", im.size, "white")
        bg.paste(im.convert("RGBA"), mask=im.convert("RGBA").split()[3])
        im = bg
    return np.asarray(im.convert("L"))


def place(pub, ours):
    """Our render's rows and columns inside the published grid. Most renders have the same size;
    a render cut from the published figure (a strip of panels) is found by sliding it down."""
    if pub.shape == ours.shape:
        return 0, 0
    h, w = ours.shape
    if h > pub.shape[0] or w > pub.shape[1]:
        return None
    sig_o = ours[:, :w].astype(float).mean(axis=1)
    best = min(range(pub.shape[0] - h + 1),
               key=lambda dy: float(np.abs(pub[dy:dy + h, :w].astype(float).mean(axis=1) - sig_o).mean()))
    return best, 0


def shrink(classes, f):
    """Block maximum by priority (paper only > ours only > the same > nothing), so thin lines survive."""
    if f <= 1:
        return classes
    h, w = classes.shape
    H, W = -(-h // f), -(-w // f)
    pad = np.zeros((H * f, W * f), classes.dtype)
    pad[:h, :w] = classes
    return pad.reshape(H, f, W, f).max(axis=(1, 3))


def main(pub_dir, run_out, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    manifest = []
    def order(p):
        m = re.fullmatch(r"fig(\d+)_ours\.png", os.path.basename(p))
        return int(m.group(1)) if m else 99

    for r in sorted(glob.glob(os.path.join(run_out, "fig*_ours.png")), key=order):
        m = re.fullmatch(r"fig(\d+)_ours\.png", os.path.basename(r))
        if not m:
            continue
        n = m.group(1)
        pubs = [p for p in glob.glob(os.path.join(pub_dir, f"figure-{n}.*")) if p.lower().endswith((".png", ".jpg", ".jpeg"))]
        if not pubs:
            continue
        pub, ours = load(pubs[0]), load(r)
        at = place(pub, ours)
        if at is None:
            continue
        dy, dx = at
        pub = pub[dy:dy + ours.shape[0], dx:dx + ours.shape[1]]
        P, O = pub < INK, ours < INK
        near_o = ndimage.binary_dilation(O, iterations=2)
        near_p = ndimage.binary_dilation(P, iterations=2)
        classes = np.zeros(P.shape, np.uint8)
        classes[(P & near_o) | (O & near_p)] = 1
        classes[O & ~near_p] = 2
        classes[P & ~near_o] = 3
        small = shrink(classes, -(-P.shape[1] // WIDTH))
        rgb = np.full(small.shape + (3,), 255, np.uint8)
        for k, c in ((1, GREY), (2, OURS_ONLY), (3, PAPER_ONLY)):
            rgb[small == k] = c
        name = f"fig{n}.png"
        Image.fromarray(rgb).convert("P", palette=Image.Palette.ADAPTIVE, colors=8).save(os.path.join(out_dir, name), optimize=True)
        manifest.append({
            "figure": f"Fig. {n}", "file": name,
            "paper_within_2px": round(float((P & near_o).sum() / max(P.sum(), 1)), 4),
            "ours_within_2px": round(float((O & near_p).sum() / max(O.sum(), 1)), 4),
        })
    with open(os.path.join(out_dir, "overlays.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    print(json.dumps(manifest))


if __name__ == "__main__":
    main(*sys.argv[1:4])

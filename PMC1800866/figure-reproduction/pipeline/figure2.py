#!/usr/bin/env python3
"""Fig. 2: our site and chain coverage counts drawn as bars, and marked on the published figure.

The counts are compared as values (the published bars carry printed labels). Here they are drawn:
fig2_ours.png re-plots them in the published layout; fig2_overlay.png marks our bar tops (red:
covered, blue: total) on the published image. The y map comes from the tick labels and the bar
baseline of the 600 x 211 JPEG: (a) 0 at row 188 and 500 at row 40; (b) 0 at row 189 and 350 at
row 38.5. The bars sit at a 51 px pitch, 29 px wide, from x 42 (a) and 348 (b).

Usage: figure2.py PUBLISHED_JPG TABLES_JSON OUT_DIR
"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw

ORDER = ["Overall", "Zn4", "Zn3", "Zn2", "Zn1"]
CAL = {"sites": (188.0, 40.0, 500.0, 42), "chains": (189.0, 38.5, 350.0, 348)}  # y0 row, top row, top value, first bar x


def row(kind, v):
    y0, yt, vt, _ = CAL[kind]
    return y0 - v / vt * (y0 - yt)


def main(pub, tables, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    fig2 = json.load(open(tables))["fig2"]
    im = Image.open(pub).convert("RGB")
    dr = ImageDraw.Draw(im)
    for kind in ("sites", "chains"):
        x0 = CAL[kind][3]
        for i, k in enumerate(ORDER):
            c = fig2[kind][k]
            xa, xb = x0 + 51 * i, x0 + 51 * i + 29
            for v, col in ((c["covered"], (220, 0, 0)), (c["covered"] + c["not_covered"], (0, 90, 220))):
                y = row(kind, v)
                dr.line([(xa - 3, y), (xb + 3, y)], fill=col, width=2)
    im.save(out / "fig2_overlay.png")

    w, h = 600, 211
    f, axes = plt.subplots(1, 2, figsize=(w / 100, h / 100), dpi=100)
    for ax, kind, title, top in ((axes[0], "sites", "Site coverage", 500), (axes[1], "chains", "Chain coverage", 350)):
        cov = [fig2[kind][k]["covered"] for k in ORDER]
        nc = [fig2[kind][k]["not_covered"] for k in ORDER]
        x = np.arange(len(ORDER))
        ax.bar(x, cov, 0.57, color="#555555", edgecolor="black", linewidth=0.5, label="Covered")
        ax.bar(x, nc, 0.57, bottom=cov, color="#eeeeee", edgecolor="black", linewidth=0.5, label="Not covered")
        for xi, a, b in zip(x, cov, nc):
            if a:
                ax.text(xi, a / 2, str(a), ha="center", va="center", fontsize=5, color="white")
            if b:
                ax.text(xi, a + b / 2, str(b), ha="center", va="center", fontsize=5)
        ax.set_xticks(x, ORDER, fontsize=5)
        ax.set_ylim(0, top)
        ax.tick_params(axis="y", labelsize=5)
        ax.set_title(title, fontsize=6)
        ax.legend(fontsize=4.5, loc="upper right", frameon=True)
    f.text(0.27, 0.97, "(a)", fontsize=6, ha="center", va="top")
    f.text(0.76, 0.97, "(b)", fontsize=6, ha="center", va="top")
    f.subplots_adjust(left=0.06, right=0.99, bottom=0.11, top=0.84, wspace=0.18)
    f.savefig(out / "fig2_ours.png", dpi=100)
    print(json.dumps(fig2))


if __name__ == "__main__":
    main(*sys.argv[1:4])

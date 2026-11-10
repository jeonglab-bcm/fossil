#!/usr/bin/env python3
"""The published figures for comparison: the JPEGs of Figs 1, 2, 7, 8 and 9 as PMC serves them,
and Figs 3-6 rendered at 600 dpi from the vector drawings in the paper's PDF.

Usage: published.py DOWNLOADS_DIR OUT_DIR
"""
import shutil
import sys
from pathlib import Path

import pymupdf

# Page (1-based) and clip rectangle in PDF points of each vector figure.
VECTOR = {3: (6, (45, 525, 560, 680)), 4: (7, (45, 78, 560, 232)), 5: (7, (45, 515, 560, 672)), 6: (8, (45, 78, 560, 232))}


def main(dl, out):
    dl, out = Path(dl), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for i in (1, 2, 7, 8, 9):
        shutil.copyfile(dl / f"1471-2105-8-39-{i}.jpg", out / f"figure-{i}.jpg")
    doc = pymupdf.open(dl / "PMC1800866.1.pdf")
    for fig, (page, rect) in VECTOR.items():
        doc[page - 1].get_pixmap(dpi=600, clip=pymupdf.Rect(*rect)).save(out / f"figure-{fig}.png")


if __name__ == "__main__":
    main(*sys.argv[1:3])

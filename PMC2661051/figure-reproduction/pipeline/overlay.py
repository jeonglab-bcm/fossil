#!/usr/bin/env python3
"""Overlay each published figure with our render: red channel = published, green and blue = ours,
so cyan is ink only in the paper, red is ink only in ours and black is both. Both images are the
same pixel size (our renders are drawn at the published size).

Usage: overlay.py PUBLISHED_DIR RENDER_DIR OUTDIR
"""
import sys
from pathlib import Path

from PIL import Image

pub, ren, out = map(Path, sys.argv[1:4])
for n in (2, 3, 4):
    a = Image.open(pub / f"Fig{n}.png").convert("L")
    b = Image.open(ren / f"fig{n}_ours.png").convert("L").resize(a.size)
    Image.merge("RGB", (a, b, b)).save(out / f"fig{n}_overlay.png", optimize=True)

"""Write Fig. 1 as published (the image embedded in the article PDF, 1949 x 1444 px at 300 dpi) as a PNG, and check
it equals the committed copy pixel for pixel.

Usage: published_figure.py ARTICLE_PDF OUT_PNG [--check COMMITTED_PNG]   (needs pdfimages from poppler-utils)
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

args = sys.argv[1:]
check = None
if "--check" in args:
    i = args.index("--check"); check = args[i + 1]; del args[i:i + 2]
pdf, out = args
with tempfile.TemporaryDirectory() as d:
    subprocess.run(["pdfimages", "-j", "-f", "4", "-l", "4", pdf, str(Path(d) / "fig")], check=True)
    jpgs = sorted(Path(d).glob("fig-*.jpg"))
    if len(jpgs) != 1:
        sys.exit(f"expected one image on page 4 of {pdf}, found {len(jpgs)}")
    im = Image.open(jpgs[0]).convert("RGB")
if im.size != (1949, 1444):
    sys.exit(f"Fig. 1 is {im.size}, expected 1949 x 1444")
im.save(out)
if check:
    same = np.array_equal(np.asarray(im), np.asarray(Image.open(check).convert("RGB")))
    if not same:
        sys.exit(f"{out} differs from {check}")
    print(f"{out}: same pixels as {check}", file=sys.stderr)

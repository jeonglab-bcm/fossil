"""Render the published figures from the article PDF (PMC copy) at 300 dpi, once.

Usage: render_published.py PAPER.pdf SUPP_DIR OUT_DIR

Writes figure-1.png ... figure-4.png, additional-file-4.png, -10, -12, -15, -20, -23, -24, -26 and -29.png
(whole pages of those supplement PDFs, at 72 to 200 dpi; see the list below) and frames.json (each crop's box in PDF points). The renders are
committed under published/ and the pipeline draws on copies of them, so a rerun does not depend on the
poppler version (anti-aliasing differs between versions). Figs 2-4 are vector drawings in the PDF and
Fig. 1 a raster heat map (1617 x 839 px) under vector dendrograms and labels; 300 dpi keeps the raster
at its own resolution (1617 px over 388 pt is 300 dpi).
"""
import json
import subprocess
import sys
from pathlib import Path

DPI = 300
# (page, left, top, right, bottom) in PDF points, y down: the figure frame down to the caption.
CROPS = {1: (5, 57, 90, 538.6, 354), 2: (7, 57, 90, 538.6, 466), 3: (11, 57, 90, 538.6, 695), 4: (13, 57, 90, 538.6, 570)}

pdf, supp, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
out.mkdir(parents=True, exist_ok=True)
frames = {}
for n, (page, x0, y0, x1, y1) in CROPS.items():
    s = DPI / 72
    X, Y, W, H = round(x0 * s), round(y0 * s), round((x1 - x0) * s), round((y1 - y0) * s)
    stem = out / f"figure-{n}"
    subprocess.run(["pdftoppm", "-r", str(DPI), "-f", str(page), "-l", str(page), "-x", str(X), "-y", str(Y),
                    "-W", str(W), "-H", str(H), "-png", "-singlefile", pdf, str(stem)], check=True)
    frames[f"fig{n}"] = {"page": page, "dpi": DPI, "origin_pt": [X / s, Y / s], "size_px": [W, H]}
for n, dpi in ((4, 72), (10, 72), (12, 72), (15, 100), (20, 100), (23, 200), (24, 72), (26, 72), (29, 100)):
    src = f"{supp}/13059_2014_484_MOESM{n}_ESM.pdf"
    stem = out / f"additional-file-{n}"
    subprocess.run(["pdftoppm", "-r", str(dpi), "-png", "-singlefile", src, str(stem)], check=True)
    frames[f"af{n}"] = {"page": 1, "dpi": dpi, "origin_pt": [0, 0]}
(out / "frames.json").write_text(json.dumps(frames, indent=1) + "\n")

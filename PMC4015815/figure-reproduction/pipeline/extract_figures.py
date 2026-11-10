"""Check that published/figure-{3,4,5}.png are the images embedded in the paper's PDF.

usage: extract_figures.py PDF PUBLISHED_DIR OUT_JSON

The PMC open-access PDF embeds Figures 3, 4 and 5 as lossless PNG images 1,200 px wide (the web
JPEGs are 600 px). We extract them and compare decoded pixels with the committed copies.
"""
import io
import json
import sys

import numpy as np
import pymupdf
from PIL import Image

# (page index, image xref) of each figure in PMC4015815.1.pdf
FIGURES = {"figure-3.png": (5, 122), "figure-4.png": (6, 145), "figure-5.png": (7, 152)}


def main(pdf, pub_dir, out):
    doc = pymupdf.open(pdf)
    res = {}
    for name, (page, xref) in FIGURES.items():
        info = doc.extract_image(xref)
        a = np.asarray(Image.open(io.BytesIO(info["image"])).convert("RGB"))
        b = np.asarray(Image.open(f"{pub_dir}/{name}").convert("RGB"))
        res[name] = {"page": page + 1, "size": [info["width"], info["height"]],
                     "format": info["ext"], "identical": bool(a.shape == b.shape and (a == b).all())}
    json.dump(res, open(out, "w"), indent=1)
    print(res)
    if not all(r["identical"] for r in res.values()):
        sys.exit(1)


if __name__ == "__main__":
    main(*sys.argv[1:4])

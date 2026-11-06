"""Render the paper's figures from its vector PDF at 600 dpi.

usage: published.py PAPER_PDF OUTDIR

The figures in PMC4765871.1.pdf are vector drawings, so a 600 dpi render is sharper than the
640 px JPEGs PMC serves. The clip boxes (PDF points) are the union of the drawings and short
text blocks above each caption, padded by 2 pt.
"""
import json
import sys
from pathlib import Path

import pymupdf

HERE = Path(__file__).resolve().parent
DPI = 600


def main(pdf, outdir):
    boxes = json.loads((HERE / "params" / "figure_boxes.json").read_text())
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(pdf)
    for name, b in boxes["figures"].items():
        page = doc[b["page"] - 1]
        clip = pymupdf.Rect(*b["clip"]) + (-2, -2, 2, 2)
        pix = page.get_pixmap(dpi=DPI, clip=clip, alpha=False)
        pix.save(out / f"figure-{name[3:]}.png")
        print(name, pix.width, pix.height)


if __name__ == "__main__":
    main(*sys.argv[1:3])

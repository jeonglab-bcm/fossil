"""Cut the published figures out of the paper and supplement PDFs at 300 dpi.

    make_published.py PAPER.pdf SUPPLEMENT.pdf OUT_DIR

Run once by hand (needs Ghostscript); its PNGs and crops.json are committed in published/ so the
pipeline does not need Ghostscript. Each crop is a box in PDF points on one page; crops.json keeps
the box so render.py can place our values on the published pixels with the axis calibrations of
read_published.py.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

DPI = 300
# name: (pdf, page index, page height in points, x0, top, x1, bottom) in PDF points from the page's top-left
CROPS = {
    "fig2a": ("paper", 3, 1032, 100.0, 195.0, 335.0, 420.0),
    "fig2b": ("paper", 3, 1032, 100.0, 425.0, 335.0, 650.0),
    "fig3": ("paper", 4, 1032, 100.0, 190.0, 345.0, 400.0),
    "fig4a": ("paper", 4, 1032, 375.0, 190.0, 620.0, 366.0),
    "fig4b": ("paper", 4, 1032, 375.0, 362.0, 620.0, 546.0),
    "figS1": ("supplement", 6, 792, 150.0, 205.0, 462.0, 518.0),
    "figS2": ("supplement", 7, 792, 76.0, 155.0, 536.0, 502.0),
}


def main(argv):
    pdfs = {"paper": argv[1], "supplement": argv[2]}
    out = Path(argv[3])
    out.mkdir(parents=True, exist_ok=True)
    s = DPI / 72
    meta = {"dpi": DPI, "crops": {}}
    with tempfile.TemporaryDirectory() as tmp:
        pages = {}
        for name, (doc, page, height, x0, top, x1, bottom) in CROPS.items():
            key = (doc, page)
            if key not in pages:
                png = Path(tmp) / f"{doc}_{page}.png"
                subprocess.run(["gs", "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=png16m", f"-r{DPI}",
                                "-dTextAlphaBits=4", "-dGraphicsAlphaBits=4",
                                f"-dFirstPage={page + 1}", f"-dLastPage={page + 1}", f"-sOutputFile={png}", pdfs[doc]], check=True)
                pages[key] = Image.open(png).convert("RGB")
            im = pages[key].crop((round(x0 * s), round(top * s), round(x1 * s), round(bottom * s)))
            im.save(out / f"{name}.png", optimize=True)
            meta["crops"][name] = {"document": doc, "page_index": page, "page_height": height,
                                   "box_points": [x0, top, x1, bottom], "size_px": list(im.size)}
    (out / "crops.json").write_text(json.dumps(meta, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

"""Check that the committed published figures (published/*.png) are the downloaded originals, pixel for pixel.

Usage: verify_published.py DOWNLOADS_DIR PUBLISHED_DIR [--write]

The paper is CC BY; the originals (Fig. 2 as JPEG, Figs S1-S12 as 2.7 MB TIFFs) are kept as lossless PNGs.
--write makes the PNGs from the downloads (once); without it, any pixel difference fails.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

FILES = {"fig2.png": "pone.0025491.g002.jpg"} | {f"figS{k}.png": f"pone.0025491.s{k:03d}.tif" for k in range(1, 13)}


def main():
    dl, pub = Path(sys.argv[1]), Path(sys.argv[2])
    write = "--write" in sys.argv
    bad = []
    for png, orig in FILES.items():
        a = Image.open(dl / orig).convert("RGB")
        if write:
            a.save(pub / png, optimize=True)
            continue
        b = Image.open(pub / png).convert("RGB")
        if a.size != b.size or not np.array_equal(np.asarray(a), np.asarray(b)):
            bad.append(png)
    if bad:
        # Fig. 2: the AWS fallback is a smaller copy; say so instead of failing on a mirror switch.
        print(f"published figures differ from the downloads: {bad}", file=sys.stderr)
        sys.exit(1)
    print(f"{len(FILES)} published figures {'written' if write else 'match the downloads'}", file=sys.stderr)


if __name__ == "__main__":
    main()

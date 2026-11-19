"""Check that the committed published figures (published/*.png) are the downloaded originals, pixel for pixel.

Usage: verify_published.py DOWNLOADS_DIR PUBLISHED_DIR [--write]

The paper is CC BY; the originals (Fig. 2 as JPEG, Figs S1-S12 as 2.7 MB TIFFs) are kept as lossless PNGs.
--write makes the PNGs from the downloads (once); without it, any pixel difference fails.
"""
import hashlib
import sys
from pathlib import Path

import numpy as np
from PIL import Image

# Fig. 2 has a second pinned copy: when Europe PMC is down, fetch_inputs.sh takes PMC AWS's smaller rendition
# (SHA-256 below). Its pixels cannot equal the original's, so the committed PNG (the original, whose JPEG
# SHA-256 fetch_inputs.sh pins) is used as is, and the check says so.
FALLBACK_SHA = {"pone.0025491.g002.jpg": "c46f35e07f6ac19b0ad9168207eb5269284772c768bd8205583f40a942020a2e"}
FILES = {"fig2.png": "pone.0025491.g002.jpg"} | {f"figS{k}.png": f"pone.0025491.s{k:03d}.tif" for k in range(1, 13)}


def main():
    dl, pub = Path(sys.argv[1]), Path(sys.argv[2])
    write = "--write" in sys.argv
    bad = []
    for png, orig in FILES.items():
        if not write and hashlib.sha256((dl / orig).read_bytes()).hexdigest() == FALLBACK_SHA.get(orig):
            print(f"note: {orig} is the AWS fallback copy; {png} (the original) not compared", file=sys.stderr)
            continue
        a = Image.open(dl / orig).convert("RGB")
        if write:
            a.save(pub / png, optimize=True)
            continue
        b = Image.open(pub / png).convert("RGB")
        if a.size != b.size or not np.array_equal(np.asarray(a), np.asarray(b)):
            bad.append(png)
    if bad:
        print(f"published figures differ from the downloads: {bad}", file=sys.stderr)
        sys.exit(1)
    print(f"{len(FILES)} published figures {'written' if write else 'match the downloads'}", file=sys.stderr)


if __name__ == "__main__":
    main()

#!/usr/bin/env bash
# Download the paper's PDF from PMC's open-access copy on AWS, check its SHA-256, extract the
# embedded Figs 2 and 3 (2400 x 1200 px, the largest copies published) and check that they are the
# copies committed in published/ for the comparison (decoded pixels; PNG bytes depend on the
# poppler version).
#
# usage: fetch_inputs.sh OUTDIR [--sources DIR]   (--sources: use a local PMC2648748.1.pdf)
#
# Sources, in order: --sources; PMC's open-access bucket (SHA-256 checked); Europe PMC (figures
# checked). Fails if none works.
#
# Writes OUTDIR/fetch.json. The simulations need no input data.
set -euo pipefail
out=${1:-downloads}
shift || true
sources=""
if [[ "${1:-}" == "--sources" ]]; then sources=$2; fi
here=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$out"
PDF=PMC2648748.1.pdf
URL=https://pmc-oa-opendata.s3.amazonaws.com/PMC2648748.1/PMC2648748.1.pdf
SHA=f797d12c1962658158ec0225f0def0d5f5a096bfa118a90f7ccb62f5d9bc4e4f
# Fallback: Europe PMC's rendering of the same article. It is a different file (no SHA-256 to
# check), so it is accepted only if the figures extracted from it are pixel for pixel the committed
# ones (checked below). Not reachable from the session that wrote this script (HTTP 403 through its
# proxy), so untested there.
MIRROR="https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC2648748&blobtype=pdf"
status=downloaded
if [[ -n "$sources" && -f "$sources/$PDF" ]]; then
  cp "$sources/$PDF" "$out/$PDF"
  status=local
elif curl -sSL --fail --retry 3 --retry-delay 5 -o "$out/$PDF" "$URL"; then
  echo "$SHA  $out/$PDF" | sha256sum -c --quiet
elif curl -sSL --fail --retry 3 --retry-delay 5 -o "$out/$PDF" "$MIRROR"; then
  status=mirror
  URL=$MIRROR
  SHA=$(sha256sum "$out/$PDF" | cut -d' ' -f1)
else
  echo "the paper's PDF could not be downloaded from PMC ($URL) or Europe PMC; pass --sources DIR with $PDF" >&2
  exit 1
fi
[[ "$status" == local ]] && echo "$SHA  $out/$PDF" | sha256sum -c --quiet
pdfimages -png -f 5 -l 6 "$out/$PDF" "$out/fig"
python3 - "$out" "$status" "$URL" "$SHA" "$here/../published" <<'PY'
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
out, status, url, sha, pub = sys.argv[1:6]
rec = {"pdf": {"name": "PMC2648748.1.pdf", "url": url, "sha256": sha, "status": status}, "figures": []}
for n, f in ((2, "fig-000.png"), (3, "fig-001.png")):
    committed = np.asarray(Image.open(Path(pub) / f"figure-{n}.png").convert("RGB"))
    p = Path(out) / f
    if not p.exists():
        raise SystemExit(f"figure {n} was not found in the PDF")
    if True:
        got = np.asarray(Image.open(p).convert("RGB"))
        same = got.shape == committed.shape and bool((got == committed).all())
        if not same:
            raise SystemExit(f"figure {n} extracted from the PDF differs from published/figure-{n}.png")
    rec["figures"].append({"figure": n, "size": list(committed.shape[1::-1]), "same_as_committed": same})
Path(out, "fetch.json").write_text(json.dumps(rec, indent=1))
print(json.dumps(rec))
PY

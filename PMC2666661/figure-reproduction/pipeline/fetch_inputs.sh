#!/usr/bin/env bash
# Download the inputs of the reproduction and check their SHA-256.
#   fetch_inputs.sh OUTDIR [--sources DIR] [--port-check]
# Default: the six published figures (PMC open-access copy on AWS; fallback: Europe PMC's PMC render
# service is not scriptable, so the fallback is the repository's own published/ copies, which are
# the same files). --port-check also fetches Breiman and Cutler's Fortran Random Forests 5.1.
set -euo pipefail
out="$1"; shift
src=""; port=0
while [ $# -gt 0 ]; do
  case "$1" in
    --sources) src="$2"; shift 2 ;;
    --port-check) port=1; shift ;;
    *) echo "unknown option $1" >&2; exit 2 ;;
  esac
done
here="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$out"
base=https://pmc-oa-opendata.s3.amazonaws.com/PMC2666661.1
fetch() {  # name url sha256 [fallback-file]
  local name="$1" url="$2" sum="$3" fb="${4:-}"
  if [ -n "$src" ] && [ -f "$src/$name" ]; then
    cp "$src/$name" "$out/$name"
  elif ! curl -fsSL --retry 3 -o "$out/$name" "$url"; then
    if [ -n "$fb" ] && [ -f "$fb" ]; then echo "download failed, using $fb" >&2; cp "$fb" "$out/$name"; else exit 1; fi
  fi
  echo "$sum  $out/$name" | sha256sum -c --quiet -
}
fetch 1471-2105-10-78-1.jpg $base/1471-2105-10-78-1.jpg 7894cb05ecad9c9e958dbb6d08187589dd7d257c0c992321311625080ced3dd1 "$here/../published/figure-1.jpg"
fetch 1471-2105-10-78-2.jpg $base/1471-2105-10-78-2.jpg 4eeda617ad384b6f4a127b96d96dfe79f6b03e8ae2d59f4f47e0b02c41987e36 "$here/../published/figure-2.jpg"
fetch 1471-2105-10-78-3.jpg $base/1471-2105-10-78-3.jpg 806352f160a510cbc74cc0c09efb76ad4f617e9d82c67635dc73dc936241e8e7 "$here/../published/figure-3.jpg"
fetch 1471-2105-10-78-4.jpg $base/1471-2105-10-78-4.jpg cc4c6fe9aaffdb89fa7606a7b6a1d1d15a7a342521b9d74d91ffc3bbdba3ef41 "$here/../published/figure-4.jpg"
fetch 1471-2105-10-78-5.jpg $base/1471-2105-10-78-5.jpg b74cb7f34756a4f178b131d6d99ae6ce1bf669bb5164b203d8b3bd27f48417f4 "$here/../published/figure-5.jpg"
fetch 1471-2105-10-78-6.jpg $base/1471-2105-10-78-6.jpg 4437adb9ffc45f3c678aab797e6825a93ecc1b61f5a1e2f81b64e693c4666868 "$here/../published/figure-6.jpg"
if [ "$port" = 1 ]; then
  fetch prog.f https://www.stat.berkeley.edu/~breiman/RandomForests/cc_examples/prog.f a985f3a0bef2b4f270c6d3064039ff086bd45c613fde3c72e5d72a156f72f09b
fi
echo "inputs ok"

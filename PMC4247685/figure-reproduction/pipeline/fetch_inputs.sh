#!/usr/bin/env bash
# Download the inputs this reproduction reads and check their SHA-256. Run in an empty directory.
# Usage: fetch_inputs.sh [local dir with already downloaded copies]
set -euo pipefail
LOCAL=${1:-}

SPRINGER=https://static-content.springer.com/esm/art%3A10.1186%2Fs12859-014-0355-5/MediaObjects
XENA=https://tcga-xena-hub.s3.us-east-1.amazonaws.com/download

# name|url|sha256
FILES="
S1.txt|$SPRINGER/12859_2014_355_MOESM1_ESM.txt|f91e4234ae7c76ca7ebf4a852b95373012f82cc0206ceb07d4bf94552d73e1f7
S2.txt|$SPRINGER/12859_2014_355_MOESM2_ESM.txt|455ef8046c9a277932cf28ada42bb60b577dbed910d1863a742b21c75b90645f
S3.txt|$SPRINGER/12859_2014_355_MOESM3_ESM.txt|2668e166f9c3f29280de941590b057f3de2962f212f9e5ea0378cd5146161a0d
HumanMethylation27.gz|$XENA/TCGA.OV.sampleMap%2FHumanMethylation27.gz|990e83c1fe48e30ad4e9cde21030d8aa8718f79754eb1b650970ba19f3a7959d
OV_clinicalMatrix|$XENA/TCGA.OV.sampleMap%2FOV_clinicalMatrix|d3751e562dbbff52c961b5806f7cc8b1fc614009fcbb7b59ab7bcdf9a20e3789
OV_survival.txt|$XENA/survival%2FOV_survival.txt|e6ff76c96b983cb5c26011b191a838bb03380324f4372a209286403425580d70
"

sha() { if command -v sha256sum >/dev/null; then sha256sum "$1" | cut -d' ' -f1; else shasum -a 256 "$1" | cut -d' ' -f1; fi; }

for row in $FILES; do
  IFS='|' read -r name url want <<< "$row"
  got=""
  if [ -n "$LOCAL" ]; then
    for f in "$LOCAL"/*; do
      if [ -f "$f" ] && [ "$(sha "$f")" = "$want" ]; then cp "$f" "$name"; got=$want; break; fi
    done
  fi
  if [ -z "$got" ]; then
    curl -sSfL --retry 3 -A 'Mozilla/5.0' -o "$name" "$url"
    got=$(sha "$name")
  fi
  if [ "$got" != "$want" ]; then
    echo "SHA-256 mismatch for $name ($url): got $got, want $want" >&2
    exit 1
  fi
done

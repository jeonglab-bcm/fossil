#!/usr/bin/env bash
# Download the inputs of the PMC4765871 reproduction into DIR and check their SHA-256.
#   fetch_inputs.sh DIR [SOURCES]
# SOURCES: a folder with local copies (same file names); used instead of downloading when present.
set -euo pipefail
DIR=${1:-downloads}
SOURCES=${2:-}
mkdir -p "$DIR"

fetch() {  # name sha256 url [fallback-url]
  local name=$1 sha=$2 url=$3 alt=${4:-}
  if [ -n "$SOURCES" ] && [ -f "$SOURCES/$name" ]; then
    cp "$SOURCES/$name" "$DIR/$name"
  else
    curl -sSfL --retry 3 --retry-delay 5 -o "$DIR/$name" "$url" ||
      { [ -n "$alt" ] && curl -sSfL --retry 3 --retry-delay 5 -o "$DIR/$name" "$alt"; }
  fi
  echo "$sha  $DIR/$name" | sha256sum -c --quiet - || { echo "checksum failed: $name" >&2; exit 1; }
}

# The paper (CC BY-NC 4.0): its vector figures are rendered for comparison, never committed as PDF.
fetch PMC4765871.1.pdf 4121f42f340cdad602e8c6fc92c9daf8e0e22ed7d2c89e787a9f20b93b60ee83 \
  https://pmc-oa-opendata.s3.amazonaws.com/PMC4765871.1/PMC4765871.1.pdf
# Moignard et al. 2013, Supplementary Table 3: raw Ct values of 620 cells x 24 assays.
fetch moignard2013_s3.xlsx 55fca1314dda722aff9e5f9cc9d4f9dfa58f1eb4b3a70564263e048e6e299be0 \
  'https://static-content.springer.com/esm/art%3A10.1038%2Fncb2709/MediaObjects/41556_2013_BFncb2709_MOESM81_ESM.xlsx' \
  https://pmc-oa-opendata.s3.amazonaws.com/PMC3796878.1/NIHMS53736-supplement-9.xlsx
echo "inputs ok"

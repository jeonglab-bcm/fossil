#!/usr/bin/env bash
# Download the four data supplements of PMC3499255 (Datasets S1-S4) and check
# their SHA-256. The paper, Text S1 and the figures are NOT fetched here; only
# the data the pipeline runs on. The files are CC BY (PLoS) but are not
# redistributed in this repository.
#
#   fetch_inputs.sh DIR [--sources LOCALDIR]
#
# With --sources, copies the files from a local directory instead of downloading
# (for offline reruns). Primary source: Europe PMC supplementaryFiles zip;
# fallback: the PMC open-access package on AWS.
set -euo pipefail

DIR="${1:-downloads}"
SRC=""
if [ "${2:-}" = "--sources" ]; then SRC="${3:-}"; fi
mkdir -p "$DIR"

FILES=(pcbi.1002768.s001.fasta pcbi.1002768.s002.txt pcbi.1002768.s003.fasta pcbi.1002768.s004.txt)

# Expected SHA-256 of each dataset (filled in on first fetch; see checksums.sha256).
CHECKSUMS="$(dirname "$0")/checksums.sha256"

fetch_europepmc() {
  local zip="$DIR/supp.zip"
  curl -fsSL --retry 3 -o "$zip" \
    "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC3499255/supplementaryFiles"
  ( cd "$DIR" && unzip -o -q supp.zip "${FILES[@]}" ) || return 1
  rm -f "$zip"
}

if [ -n "$SRC" ]; then
  echo "Copying datasets from $SRC"
  for f in "${FILES[@]}"; do cp "$SRC/$f" "$DIR/"; done
else
  echo "Downloading datasets from Europe PMC"
  if ! fetch_europepmc; then
    echo "Europe PMC failed; trying PMC open-access package on AWS"
    for f in "${FILES[@]}"; do
      curl -fsSL --retry 3 -o "$DIR/$f" \
        "https://pmc-oa-opendata.s3.amazonaws.com/PMC3499255.1/$f"
    done
  fi
fi

if [ -f "$CHECKSUMS" ]; then
  echo "Verifying checksums"
  ( cd "$DIR" && sha256sum -c "$CHECKSUMS" )
else
  echo "No committed checksums; recording them"
  ( cd "$DIR" && sha256sum "${FILES[@]}" ) > "$CHECKSUMS"
  cat "$CHECKSUMS"
fi
echo "Datasets ready in $DIR"

#!/usr/bin/env bash
# Download every input of the PMC2909217 reproduction and check its SHA-256.
#
#   bash fetch_inputs.sh DIR [--sources LOCAL_DIR]
#
# All inputs come from SGD's public archive bucket on AWS S3 (BioGRID data as SGD imported it on
# 2009-12-19, two weeks before the paper was submitted, and SGD's processed expression sets).
# --sources reuses local copies (any file with the same name and checksum) before downloading.
set -euo pipefail
out=${1:?usage: fetch_inputs.sh DIR [--sources LOCAL_DIR]}
shift
src=""
while [ $# -gt 0 ]; do
  case "$1" in
    --sources) src=$2; shift 2 ;;
    *) echo "unknown option $1" >&2; exit 2 ;;
  esac
done
mkdir -p "$out"
primary=https://s3-us-west-2.amazonaws.com/sgd-archive.yeastgenome.org
mirror=https://sgd-archive.yeastgenome.org

# name | path in the archive | sha256
inputs=(
"interaction_data.tab.20091219.gz|curation/literature/archive/interaction_data.tab.20091219.gz|3ed60847be0c92eed33e9affc572ea0f34aad539f6cf89382211a8b11dcf7a6e"
"phenotype_data.tab.20091205.gz|curation/literature/archive/phenotype_data.tab.20091205.gz|a40fe22df68e0e39c83bac1c455f0a2cbe96c0f174f09679656a27332ba82bdd"
"SGD_features.tab.20091205.gz|curation/chromosomal_feature/archive/SGD_features.tab.20091205.gz|bbc81ae52d812db621d465ed628f998041e4a6a4dab521240f072b9472684b17"
"Cho_1998_PMID_9702192.zip|expression/microarray/Cho_1998_PMID_9702192/Cho_1998_PMID_9702192.zip|5e5666534fb558ab4c72df09f4735db103293896739600db5421b05b810a8fe9"
"Chu_1998_PMID_9784122.zip|expression/microarray/Chu_1998_PMID_9784122/Chu_1998_PMID_9784122.zip|f6d0013b1a3f3ac183adeb555a602384e84b14b1057f59772586965a7f880b5f"
"Spellman_1998_PMID_9843569.zip|expression/microarray/Spellman_1998_PMID_9843569/Spellman_1998_PMID_9843569.zip|7b46af23498289f2b9a9afeac0c5ec04d73d50ad1953bd5c5c585c6f09ca3687"
)

check() { echo "$2  $1" | sha256sum -c --quiet - >/dev/null 2>&1; }

for row in "${inputs[@]}"; do
  IFS='|' read -r name path sha <<< "$row"
  dest="$out/$name"
  if [ -n "$src" ]; then
    hit=$(find "$src" -name "$name" -type f 2>/dev/null | head -1 || true)
    if [ -n "$hit" ] && check "$hit" "$sha"; then cp "$hit" "$dest"; echo "local    $name"; continue; fi
  fi
  ok=0
  for base in "$primary" "$mirror"; do
    if curl -fsSL --retry 3 --retry-delay 5 -o "$dest" "$base/$path" && check "$dest" "$sha"; then ok=1; echo "fetched  $name"; break; fi
  done
  if [ $ok -ne 1 ]; then echo "FAILED   $name (download or SHA-256)" >&2; exit 1; fi
done

for z in "$out"/*.zip; do unzip -oq -d "$out" "$z"; done
echo "inputs in $out"

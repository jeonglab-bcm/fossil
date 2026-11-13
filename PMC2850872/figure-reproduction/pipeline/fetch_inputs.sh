#!/usr/bin/env bash
# Download the NHANES 1999-2004 public-use files the reproduction reads, and check their SHA-256.
# Usage: fetch_inputs.sh OUTDIR [SOURCES]
#   SOURCES  a folder with local copies of the .xpt files; they are copied instead of downloaded.
# NHANES public-use data are produced by the US National Center for Health Statistics and are in
# the public domain. They are not redistributed here.
set -euo pipefail
out=${1:-downloads}
src=${2:-}
here=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$out"
base=https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public
while read -r year file sha; do
  [[ -z "$year" || "$year" == \#* ]] && continue
  dest="$out/$file"
  if [[ -n "$src" && -f "$src/$file" ]]; then
    cp "$src/$file" "$dest"
  elif [[ ! -f "$dest" ]]; then
    curl -fsSL --retry 5 --retry-delay 5 --retry-all-errors -o "$dest" "$base/$year/DataFiles/$file"
  fi
  if [[ "$sha" != "-" ]]; then
    echo "$sha  $dest" | sha256sum -c --quiet - || { echo "checksum mismatch: $file" >&2; exit 1; }
  fi
done < "$here/inputs/nhanes_files.tsv"
echo "fetched $(ls "$out" | wc -l) files into $out"

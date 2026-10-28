#!/usr/bin/env bash
# Download Additional Files 1 to 4 of Mantini et al. 2007 (Springer), check each file's
# SHA-256 and unpack them into the working directory.
# Usage: fetch_inputs.sh [DIR]   (DIR: reuse local copies named S1.zip S2.zip S3.zip S4.xls)
set -euo pipefail
base="https://media.springernature.com/original/springer-static/esm/art%3A10.1186%2F1471-2105-8-101/MediaObjects/12859_2006_1473"
declare -A sha=(
  [S1.zip]=8d2f6c2423d683651a303d511091edb65547bda4026e19f9aa5de7ed57d9df33
  [S2.zip]=f4ded0e64ff76206988181bda17720ece8e8fb60c37a333a7c76c3e35bb4be60
  [S3.zip]=ab9992f305b4564a171e50d87caeed73ba41f36ff7aa11c793f5aaef11871b24
  [S4.xls]=425f21435302aef36e9139c5ff1fca5dd4cf52faadfb84feb87908a86704e21d
)
declare -A url=([S1.zip]=1_ESM.zip [S2.zip]=2_ESM.zip [S3.zip]=3_ESM.zip [S4.xls]=4_ESM.xls)
for f in S1.zip S2.zip S3.zip S4.xls; do
  if [ -n "${1:-}" ] && [ -f "$1/$f" ]; then
    cp "$1/$f" "$f"
  else
    curl -sfL "${base}_MOESM${url[$f]}" -o "$f"
  fi
  got=$(shasum -a 256 "$f" | cut -d' ' -f1)
  [ "$got" = "${sha[$f]}" ] || { echo "$f: SHA-256 $got, expected ${sha[$f]}" >&2; exit 1; }
done
# S2.zip fails its CRC check on SOL_5_TXT/SOL_calib_08e.txt (one damaged line, see limpic.read_txt).
unzip -oq S1.zip -d S1
rc=0; unzip -oq S2.zip -d S2 || rc=$?
[ "$rc" -le 2 ] || exit "$rc"
unzip -oq S3.zip -d S3

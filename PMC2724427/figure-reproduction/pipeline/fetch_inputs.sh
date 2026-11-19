#!/usr/bin/env bash
# Download the inputs of the PMC2724427 reproduction and check their SHA-256.
#   fetch_inputs.sh OUTDIR [--sources DIR]
# --sources DIR: copy a file from DIR when it is there instead of downloading it.
#
# The study simulates its own data, so nothing here feeds the numbers. Additional file 1 holds the
# R lines that simulate_population() runs; the three figure files are the published figures the
# renders are compared with, and must equal the copies committed in published/.
# Sources: PMC's open-access copy on AWS for Additional file 1 (fallback: Europe PMC's zip of the
# supplementary files); Springer's original-resolution figure files (no other copy at this size).
set -euo pipefail
out="$1"; shift
src=""
while [ $# -gt 0 ]; do
  case "$1" in
    --sources) src="$2"; shift 2 ;;
    *) echo "unknown option $1" >&2; exit 2 ;;
  esac
done
mkdir -p "$out"
fetch() {  # name sha256 url [fallback zip url]
  local name="$1" sum="$2" url="$3" alt="${4:-}"
  if [ -n "$src" ] && [ -f "$src/$name" ]; then
    cp "$src/$name" "$out/$name"
  elif ! curl -fsSL --retry 3 --retry-delay 5 -o "$out/$name" "$url"; then
    [ -n "$alt" ] || { echo "download failed: $url" >&2; exit 1; }
    curl -fsSL --retry 3 --retry-delay 5 -o "$out/alt.zip" "$alt"
    unzip -o -q -j "$out/alt.zip" "$name" -d "$out" && rm -f "$out/alt.zip"
  fi
  echo "$sum  $out/$name" | sha256sum -c --quiet -
}
u=https://pmc-oa-opendata.s3.amazonaws.com/PMC2724427.1
s=https://media.springernature.com/original/springer-static/image/art%3A10.1186%2F1471-2288-9-56/MediaObjects
fetch 1471-2288-9-56-S1.pdf 948a35a1e96881f1fcabccfb0eb4bb6018245a0e849d0c718f4daa710ec4abbc $u/1471-2288-9-56-S1.pdf https://www.ebi.ac.uk/europepmc/webservices/rest/PMC2724427/supplementaryFiles
fetch figure-1.jpg 327f6dab03be506b38bb147c6de6451ee2af493583fad50e8fecbe058d3f5e52 $s/12874_2009_Article_372_Fig1_HTML.jpg
fetch figure-2.jpg 39c7b942a027383e422e831543fc9032e9b74c5901e7df27c0f980f5db26b4a0 $s/12874_2009_Article_372_Fig2_HTML.jpg
fetch figure-3.jpg c26ee2154410d1162b349449172c68f7523a6fb2263cf3918959f7c7636c869f $s/12874_2009_Article_372_Fig3_HTML.jpg
echo "inputs ok"

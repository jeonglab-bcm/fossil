#!/usr/bin/env bash
# Download the inputs of the PMC507884 reproduction and check their SHA-256.
#
#   fetch_inputs.sh DIR [--sources LOCALDIR] [--published]
#
# --sources LOCALDIR: copy files from LOCALDIR when they are there (same names), download the rest.
# --published: also download the publisher's vector EPS files of Figs 1-3 (1.4, 1.0 and 0.8 MB)
#   and check that published/Fig{1,2,3}.png are their 300 dpi renders (needs Ghostscript).
#
# Szabo et al. (2004), Additional data file 1 (the breast cancer data) and the R graphics file of
# Fig. 3 that the publisher keeps among the article's supplementary files; Vandesompele et al.
# (2002), Additional data file 1 (Model 2's data). Springer's static-content server first, PMC's
# open access copy on AWS as the fallback.
set -euo pipefail
dir=$1; shift
src=""; published=0
while [ $# -gt 0 ]; do
  case $1 in
    --sources) src=$2; shift 2 ;;
    --published) published=1; shift ;;
    *) echo "unknown option $1" >&2; exit 2 ;;
  esac
done
mkdir -p "$dir"
here=$(cd "$(dirname "$0")" && pwd)

fetch() {  # fetch NAME SHA256 URL [FALLBACK_URL]
  local name=$1 sha=$2 url=$3 alt=${4:-}
  if [ -n "$src" ] && [ -f "$src/$name" ]; then
    cp "$src/$name" "$dir/$name"
  else
    curl -fsSL --retry 3 -o "$dir/$name" "$url" || { [ -n "$alt" ] && curl -fsSL --retry 3 -o "$dir/$name" "$alt"; }
  fi
  echo "$sha  $dir/$name" | sha256sum -c --quiet - || { echo "checksum mismatch: $name" >&2; exit 1; }
}

szabo=https://static-content.springer.com/esm/art%3A10.1186%2Fgb-2004-5-8-r59/MediaObjects
vdsp=https://static-content.springer.com/esm/art%3A10.1186%2Fgb-2002-3-7-research0034/MediaObjects
s3=https://pmc-oa-opendata.s3.amazonaws.com
fetch gb-2004-5-8-r59-s1.xls 6f4a8913754eaccb83962d4823f0e73f5c75535066799d847e73ec3ff3804407 \
  $szabo/13059_2004_863_MOESM1_ESM.xls $s3/PMC507884.1/gb-2004-5-8-r59-s1.xls
fetch gb-2002-3-7-research0034-s1.TXT 4c5daecd5889b9eb8dcb995a4fa0b396d51922873f6bb4f3a6aadfc1bec871f7 \
  $vdsp/13059_2001_453_MOESM1_ESM.txt $s3/PMC126239.1/gb-2002-3-7-research0034-s1.TXT
fetch MOESM5.eps 28518a70ab010d446215009263a7b7da82f65697c9db5ef676b1bf422fcaee02 \
  $szabo/13059_2004_863_MOESM5_ESM.eps

if [ $published = 1 ]; then
  fetch MOESM2.eps 76b735225c97be0277bf511642f69be8427d55c9a6041a832c46cf13446ac890 $szabo/13059_2004_863_MOESM2_ESM.eps
  fetch MOESM3.eps 0bb4799b03dc81d4235fc61818230891458d1cd8bf2e6a4f531732ae4bab7e33 $szabo/13059_2004_863_MOESM3_ESM.eps
  fetch MOESM4.eps 65080a34783984a2dfead880cebcef8357bb3dbe97e23ed23cfa9fa62c710172 $szabo/13059_2004_863_MOESM4_ESM.eps
  for i in 1 2 3; do
    gs -q -dSAFER -dBATCH -dNOPAUSE -dEPSCrop -sDEVICE=png16m -r300 -dTextAlphaBits=4 -dGraphicsAlphaBits=4 \
      -sOutputFile="$dir/Fig$i.png" "$dir/MOESM$((i + 1)).eps"
    python3 "$here/compare_runs.py" "$dir/Fig$i.png" "$here/../published/Fig$i.png" > /dev/null \
      || { echo "published/Fig$i.png is not the render of MOESM$((i + 1)).eps" >&2; exit 1; }
  done
  echo "published figures equal their EPS renders"
fi
echo "inputs ok"

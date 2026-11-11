#!/usr/bin/env bash
# Download every input of the PMC1274252 reproduction and check its SHA-256.
#
#   fetch_inputs.sh OUTDIR [--sources DIR] [--weka-versions]
#
# The PROSPECTR site (genetics.med.ed.ac.uk/prospectr) is gone; its training and test sets, the
# download page and the genome-wide score dump survive in the Wayback Machine. Additional File 1
# comes from PMC's open-access bucket (fallback: the BMC site). Weka 3.4.3 (September 2004, the
# release current when the paper was submitted) comes from SourceForge. --sources DIR reuses local
# copies with the same names. --weka-versions also fetches Weka 3.4.1, 3.4.2 and 3.4.4.
set -euo pipefail
out=${1:?usage: fetch_inputs.sh OUTDIR [--sources DIR] [--weka-versions]}
shift
sources=""
versions=0
while [ $# -gt 0 ]; do
  case "$1" in
    --sources) sources=$2; shift 2 ;;
    --weka-versions) versions=1; shift ;;
    *) echo "unknown option $1" >&2; exit 2 ;;
  esac
done
mkdir -p "$out"
W=https://web.archive.org/web

fetch() {  # name sha256 url [fallback url]
  local name=$1 sum=$2; shift 2
  local dest="$out/$name"
  if [ -n "$sources" ] && [ -f "$sources/$name" ]; then
    cp "$sources/$name" "$dest"
  else
    local ok=0
    for url in "$@"; do
      if curl -fsSL --retry 4 --retry-delay 5 --max-time 600 -o "$dest" "$url"; then ok=1; break; fi
      echo "download failed: $url" >&2
    done
    [ $ok = 1 ] || { echo "could not download $name" >&2; exit 1; }
  fi
  echo "$sum  $dest" | sha256sum -c --quiet - || { echo "checksum mismatch: $name" >&2; exit 1; }
}

fetch omim_trainingset.arff a0ae11c7699fa2e59723674739b3fe40a207d756156a9b5c55758e1ea4a04a74 \
  "$W/20060930234112id_/http://www.genetics.med.ed.ac.uk/prospectr/omim_trainingset.arff"
fetch hgmd_testset.arff b318539e240ad0e183d10b51ff9f95da56957ca73f86d5ea00f10858ee243e52 \
  "$W/20060930234008id_/http://www.genetics.med.ed.ac.uk/prospectr/hgmd_testset.arff"
fetch pocus_testset.arff f2f4c6240bddbbd29c728461135ee0b70e09cf1713c5b6596e5e684dd9fce349 \
  "$W/20060930234153id_/http://www.genetics.med.ed.ac.uk/prospectr/pocus_testset.arff"
fetch download.shtml 513494a01519d5f6f4a32cacbd5504b2d309df2b9febb76107c1762b3265e739 \
  "$W/20060118010809id_/http://www.genetics.med.ed.ac.uk/prospectr/download.shtml"
fetch dump.tab cb98eb81ae728f472f065fcc78b4db7f8ecf4c84e8395e217042e7b3e1afc703 \
  "$W/20050427084936id_/http://www.genetics.med.ed.ac.uk/prospectr/downloads/dump.tab"
fetch 1471-2105-6-55-S1.xls b17a1a511ba0beda1907e410767bb03fa09e4f8067bde378d8b4949bec827e94 \
  "https://pmc-oa-opendata.s3.amazonaws.com/PMC1274252.1/1471-2105-6-55-S1.xls" \
  "https://static-content.springer.com/esm/art%3A10.1186%2F1471-2105-6-55/MediaObjects/12859_2004_380_MOESM1_ESM.xls"
fetch weka-3-4-3.zip 4fa0aa43f8faefdb029d7fd30294eee95f5bc0b330d9d48b4f5c8fb371fb8068 \
  "https://downloads.sourceforge.net/project/weka/weka-3-4/3.4.3/weka-3-4-3.zip" \
  "https://prdownloads.sourceforge.net/weka/weka-3-4-3.zip"
if [ $versions = 1 ]; then
  fetch weka-3-4-1.zip 4d3b9e145b8e23760a027cfb760c6576500ecb4fd46649593d4e4cf3433439ed \
    "https://downloads.sourceforge.net/project/weka/weka-3-4/3.4.1/weka-3-4-1.zip"
  fetch weka-3-4-2.zip eee9f9518e44650f65cb44792e671bea5d37956b84deb884b659dcffd1825533 \
    "https://downloads.sourceforge.net/project/weka/weka-3-4/3.4.2/weka-3-4-2.zip"
  fetch weka-3-4-4.zip eb4ee7d6d988282937fd774814b5ad637dfc3fa0ab6bbb167c14cd016aaf2e93 \
    "https://downloads.sourceforge.net/project/weka/weka-3-4/3.4.4/weka-3-4-4.zip"
fi
echo "all inputs present and checked in $out"

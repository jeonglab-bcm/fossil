#!/usr/bin/env bash
# Download the inputs of the reproduction, check their SHA-256 and unpack them.
#   fetch_inputs.sh OUTDIR [--sources DIR]
# OUTDIR/data: HPRD.net, OPHID.net and the authors' prediction files (DiseaseNetPreds.zip, unpacked
#   into preds/), from the paper's site cbcb.umd.edu/DiseaseNet as the Wayback Machine captured it on
#   2010-07-02 (the site is gone; these captures are the only copies).
# OUTDIR/paper: the paper and its supplement (PMC open-access copy on AWS; fallback Europe PMC).
# OUTDIR/weka.jar: Weka 3.6.6 (Maven Central), for the consensus Random Forest.
# --sources DIR reuses local copies named as below (DIR/HPRD.net, DIR/PMC2853684.1.pdf, ...).
set -euo pipefail
out="$1"; shift
src=""
while [ $# -gt 0 ]; do
  case "$1" in
    --sources) src="$2"; shift 2 ;;
    *) echo "unknown option $1" >&2; exit 2 ;;
  esac
done
mkdir -p "$out/data" "$out/paper"
wb=https://web.archive.org/web
pmc=https://pmc-oa-opendata.s3.amazonaws.com/PMC2853684.1
fetch() {  # dest sha256 url [fallback-url]
  local dest="$1" sum="$2" url="$3" fb="${4:-}" name
  name=$(basename "$dest")
  if [ -n "$src" ] && [ -f "$src/$name" ]; then
    cp "$src/$name" "$dest"
  elif ! curl -fsSL --retry 3 --retry-delay 5 -o "$dest" "$url"; then
    if [ -n "$fb" ]; then echo "download failed, trying $fb" >&2; curl -fsSL --retry 3 -o "$dest" "$fb"; else exit 1; fi
  fi
  echo "$sum  $dest" | sha256sum -c --quiet -
}
fetch "$out/data/HPRD.net" 01dc4f131f34be7c8d136ebd5ad3cf1650fdc5381e8d7f66e3a66be1d3d17c55 \
  "$wb/20100702195129id_/http://cbcb.umd.edu/DiseaseNet/HPRD.net"
fetch "$out/data/OPHID.net" c5ac93c5c5c2655e746f6a1a87828a49ebc7de817cacff4252ddb403828448ae \
  "$wb/20100702195046id_/http://cbcb.umd.edu/DiseaseNet/OPHID.net"
fetch "$out/data/DiseaseNetPreds.zip" a81ff1a16144fb1260e59ba0a4a227c6c63c5e12d848b7480cc2fbd864fa04af \
  "$wb/20100702195150id_/http://cbcb.umd.edu/DiseaseNet/DiseaseNetPreds.zip"
fetch "$out/paper/PMC2853684.1.pdf" d1798054854107be16d8349e783555a9d9427080aab6040d5fbe15a369278840 \
  "$pmc/PMC2853684.1.pdf"
fetch "$out/paper/btq076_1.pdf" fb4647e9c21df8e0a4dbed2a7d405686f37e1238919d695b4a040af4152a3b94 \
  "$pmc/btq076_1.pdf"
fetch "$out/weka.jar" 1b3d05d73cb1608b39361a99974b83474954d951b389528556be24a8f823883f \
  https://repo1.maven.org/maven2/nz/ac/waikato/cms/weka/weka-stable/3.6.6/weka-stable-3.6.6.jar
mkdir -p "$out/data/preds"
python3 -c "import sys, zipfile; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" "$out/data/DiseaseNetPreds.zip" "$out/data/preds"
rm "$out/data/DiseaseNetPreds.zip"
n=$(ls "$out/data/preds" | wc -l)
[ "$n" -eq 23 ] || { echo "expected 23 prediction files, found $n" >&2; exit 1; }
echo "inputs ok"

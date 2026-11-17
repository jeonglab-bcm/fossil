#!/bin/bash
# Download the inputs of the PMC2949886 reproduction and check their SHA-256.
#   fetch_inputs.sh DIR [--sources LOCAL_DIR]
# With --sources, files already in LOCAL_DIR (same names, or the PMC2949886/sources layout) are
# copied instead of downloaded. Nothing downloaded here is committed (see the paper README).
#   MOESM1.PDF      Additional File 1 (theory, simulation settings, Figures S1-S9)
#   MOESM2-8.pdf    the authors' original files for Figures 1-7 (R 2.10.0 and cairo vector PDFs)
#   GSE13425_series_matrix.txt.gz   Den Boer et al. 2009 leukemia data (GEO)
set -euo pipefail
dir=$1; shift
src=""
if [ "${1:-}" = "--sources" ]; then src=$2; fi
mkdir -p "$dir"
ESM=https://static-content.springer.com/esm/art%3A10.1186%2F1471-2105-11-450/MediaObjects
declare -A URL=(
  [MOESM1.PDF]="$ESM/12859_2010_3907_MOESM1_ESM.PDF https://pmc-oa-opendata.s3.amazonaws.com/PMC2949886.1/1471-2105-11-450-S1.PDF"
  [MOESM2.pdf]="$ESM/12859_2010_3907_MOESM2_ESM.pdf"
  [MOESM3.pdf]="$ESM/12859_2010_3907_MOESM3_ESM.pdf"
  [MOESM4.pdf]="$ESM/12859_2010_3907_MOESM4_ESM.pdf"
  [MOESM5.pdf]="$ESM/12859_2010_3907_MOESM5_ESM.pdf"
  [MOESM6.pdf]="$ESM/12859_2010_3907_MOESM6_ESM.pdf"
  [MOESM7.pdf]="$ESM/12859_2010_3907_MOESM7_ESM.pdf"
  [MOESM8.pdf]="$ESM/12859_2010_3907_MOESM8_ESM.pdf"
  [GSE13425_series_matrix.txt.gz]="https://ftp.ncbi.nlm.nih.gov/geo/series/GSE13nnn/GSE13425/matrix/GSE13425_series_matrix.txt.gz"
)
declare -A SHA=(
  [MOESM1.PDF]=34643ddb210f4495cd5babeab6f271e6c09e26ca16a2a99406bd356869dc2ae7
  [MOESM2.pdf]=284517aa0b144553eb1819e0dc8547a2055cd9ca4a82ab789890f6c5db41ca30
  [MOESM3.pdf]=d47b7743d2daf4d4fd184ac12acae1912a208ea949dd3cf77d95a9100a42f958
  [MOESM4.pdf]=9070034e7af84f5d470a6dd7a5344350655a5f08f1d4d6a2b8074e480592230f
  [MOESM5.pdf]=f4e6f03774e040284d655ce583bacfec5d1a42886f69d9bef52d36a972884111
  [MOESM6.pdf]=1cf2424a1e2a59cbab4debea2fd691e149bd6d19c4ce7d643b2b8c053b531668
  [MOESM7.pdf]=792468bde749045d4addd852f3cfc76c268a6c83ef9a0bbb3367c653e9ebb066
  [MOESM8.pdf]=4f1815f55741fb9042add314cd7da6aa55f54741f84370dc72b26b66ed95cdcc
  [GSE13425_series_matrix.txt.gz]=1f76cbe1b1c88f39fa468ebddb5e0773693c99cb889651d5d5ffe6208ddf81a2
)
for f in "${!URL[@]}"; do
  out="$dir/$f"
  if [ -n "$src" ]; then
    for cand in "$src/$f" "$src/geo/$f"; do [ -f "$cand" ] && cp "$cand" "$out" && break; done
  fi
  if [ ! -s "$out" ]; then
    for u in ${URL[$f]}; do
      curl -sSfL --retry 3 --retry-delay 5 -o "$out" "$u" && break || echo "download failed: $u" >&2
    done
  fi
  echo "${SHA[$f]}  $out" | sha256sum -c --quiet - || { echo "checksum mismatch: $f" >&2; exit 1; }
done
echo "inputs ok: ${#URL[@]} files"

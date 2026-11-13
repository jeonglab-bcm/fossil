#!/usr/bin/env bash
# Download the paper's inputs and check their SHA-256.
#
#   fetch_inputs.sh OUTDIR [SOURCES]
#
# With SOURCES, files already there are copied instead of downloaded (the local
# PMC2813257/sources folder). Downloads:
#   * the 1,753 HIV-1 env C2-V5 GenBank records of the paper's four accession ranges, through
#     NCBI E-utilities;
#   * LANL's set1_clinical_data.txt (visit numbers to months for patients 4 and 10) and the
#     Shriner 2004 sequences, from the Neher group's synmut repository, which redistributes them;
#   * MUSCLE 3.6 (public domain) as source, built here, because the paper used that version and
#     drive5.com's current page offers 3.8.31 only;
#
# The published figures are not downloaded: the paper is in the public domain (CC0), so the
# original-resolution figures are committed in figure-reproduction/published/.
set -euo pipefail

OUT=${1:?usage: fetch_inputs.sh OUTDIR [SOURCES]}
SRC=${2:-}
mkdir -p "$OUT"/{genbank,lanl,muscle}

RANGES="AF137629:AF138703 AF204402:AF204670 AY449806:AY450055 AY450056:AY450257"
EUTILS="https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
SYNMUT="https://raw.githubusercontent.com/neherlab/synmut/master/data/longitudinal/Shankarappa"
MUSCLE_URL="https://drive5.com/muscle/downloads3.6/muscle3.6_src.tar.gz"

sha() { sha256sum "$1" | cut -d' ' -f1; }

get() {  # get URL DEST [SOURCE_RELATIVE]
  local url=$1 dest=$2 rel=${3:-}
  if [ -n "$SRC" ] && [ -n "$rel" ] && [ -f "$SRC/$rel" ]; then
    cp "$SRC/$rel" "$dest"
  else
    curl -fsSL --retry 3 --retry-delay 5 -o "$dest" "$url"
  fi
}

if [ ! -s "$OUT/genbank/env.gb" ]; then
  if [ -n "$SRC" ] && [ -f "$SRC/genbank/env.gb" ]; then
    cp "$SRC/genbank/env.gb" "$OUT/genbank/env.gb"
  else
    : > "$OUT/genbank/env.gb"
    for range in $RANGES; do
      echo "GenBank $range" >&2
      ids=$(curl -fsSL --retry 3 --retry-delay 5 -G "$EUTILS/esearch.fcgi" \
        --data-urlencode "db=nuccore" --data-urlencode "retmax=2000" \
        --data-urlencode "term=${range%%:*}:${range##*:}[ACCN]" \
        | grep -o '<Id>[0-9]*</Id>' | sed 's/<[^>]*>//g' | tr '\n' ',')
      curl -fsSL --retry 3 --retry-delay 5 -d "db=nuccore&rettype=gb&retmode=text&id=${ids%,}" \
        "$EUTILS/efetch.fcgi" >> "$OUT/genbank/env.gb"
      sleep 1
    done
  fi
fi

get "$SYNMUT/set1_clinical_data.txt" "$OUT/lanl/set1_clinical_data.txt" "synmut/set1_clinical_data.txt"
get "$SYNMUT/set1_Shriner.fasta" "$OUT/lanl/set1_Shriner.fasta" "synmut/set1_Shriner.fasta"
get "$MUSCLE_URL" "$OUT/muscle/muscle3.6_src.tar.gz" "muscle/muscle3.6_src.tar.gz"
# Checksums. The GenBank file is not pinned: E-utilities writes the records in the order the
# server returns them and stamps no date, but the records themselves have not changed since 2004.
cat > "$OUT/checksums.txt" <<EOF
$(sha "$OUT/lanl/set1_clinical_data.txt")  lanl/set1_clinical_data.txt
$(sha "$OUT/lanl/set1_Shriner.fasta")  lanl/set1_Shriner.fasta
$(sha "$OUT/muscle/muscle3.6_src.tar.gz")  muscle/muscle3.6_src.tar.gz
EOF
expect() {  # expect RELATIVE SHA256
  local got; got=$(sha "$OUT/$1")
  if [ "$got" != "$2" ]; then
    echo "checksum mismatch for $1: $got, expected $2" >&2
    exit 1
  fi
}
expect muscle/muscle3.6_src.tar.gz \
  32b818a51f421e1d687f513dc31374a330470950151a5e7df961e64781699431
expect lanl/set1_clinical_data.txt \
  8659bb7cdfdbd96b841dd0b827bf285c0df53e4b635048280518d48ffab4ed89
expect lanl/set1_Shriner.fasta \
  150846c036f2dfd18c80095d8b143b32d7286690e67cc94290021ec0db42ab82

# Build MUSCLE 3.6 from its own source: the 2005 binary is 32 bit.
if [ ! -x "$OUT/muscle/muscle" ]; then
  tar xzf "$OUT/muscle/muscle3.6_src.tar.gz" -C "$OUT/muscle"
  make -C "$OUT/muscle/muscle3.6_src" -j"$(nproc)" >"$OUT/muscle/build.log" 2>&1 || true
  cp "$OUT/muscle/muscle3.6_src/muscle" "$OUT/muscle/muscle"
fi
"$OUT/muscle/muscle" -version

grep -c '^LOCUS' "$OUT/genbank/env.gb"

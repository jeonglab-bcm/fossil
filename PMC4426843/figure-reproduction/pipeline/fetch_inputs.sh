#!/bin/bash
# Download the public inputs into OUT and check them against params/SHA256SUMS.
# Usage: fetch_inputs.sh OUT [light|full] [SOURCES]
#   light: miRBase 20 mature miRNAs, Ensembl 75 BioMart GO and gene tables, the paper's
#          supplementary tables (PMC open-access copy, CC BY 4.0).
#   full:  also the Ensembl 75 GTFs, toplevel genomes and core assembly tables (about 2 GB),
#          for regenerating the 3' UTRs and miRanda predictions.
#   SOURCES: a folder with local copies; files found there are linked instead of downloaded.
set -euo pipefail
OUT=$1; MODE=${2:-light}; SRC=${3:-}
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$OUT"; cd "$OUT"
E=https://ftp.ensembl.org/pub/release-75
M=$E/mysql/ensembl_mart_75
S3=https://pmc-oa-opendata.s3.amazonaws.com/PMC4426843.1
get() {  # get URL [NAME]
  local f=${2:-$(basename "$1")}
  if [ -s "$f" ]; then return; fi
  if [ -n "$SRC" ] && [ -s "$SRC/$f" ]; then ln -sf "$(cd "$SRC" && pwd)/$f" "$f"; return; fi
  curl -sSfL --retry 5 -o "$f.part" "$1"
  mv "$f.part" "$f"
}
get https://mirbase.org/download_version_files/20/mature.fa
get $M/ensembl_mart_75.sql.gz
for sp in hsapiens mmusculus; do
  for t in go_GO__dm translation__main gene__main; do get $M/${sp}_gene_ensembl__${t}.txt.gz; done
done
for i in 1 2 3 4 5; do get $S3/supp_btv023_supplementary_table_$i.xls; done
if [ "$MODE" = full ]; then
  get $E/gtf/homo_sapiens/Homo_sapiens.GRCh37.75.gtf.gz
  get $E/gtf/mus_musculus/Mus_musculus.GRCm38.75.gtf.gz
  get $E/fasta/homo_sapiens/dna/Homo_sapiens.GRCh37.75.dna.toplevel.fa.gz
  get $E/fasta/mus_musculus/dna/Mus_musculus.GRCm38.75.dna.toplevel.fa.gz
  for c in homo_sapiens_core_75_37 mus_musculus_core_75_38; do
    for t in seq_region assembly_exception; do get "$E/mysql/$c/$t.txt.gz" "${c}__$t.txt.gz"; done
  done
fi
# Check every downloaded file against the committed sums; a file without a sum is an error.
for f in *; do
  grep -q "  $f\$" "$HERE/params/SHA256SUMS" || { echo "no checksum for $f" >&2; exit 1; }
done
awk -v d="$PWD" '{ if (system("test -e \"" d "/" $2 "\"") == 0) print }' "$HERE/params/SHA256SUMS" \
  | sha256sum -c --quiet -

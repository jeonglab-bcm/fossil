#!/usr/bin/env bash
# Download Additional Files 1 to 4 of Standley et al. 2007 (PMC open-access copy), CATH 3.0.0,
# SCOP 1.69, AAindex2 and BLOSUM62, and check each file's SHA-256.
# Usage: fetch_inputs.sh [DIR]   (DIR: reuse local copies with the same file names)
set -euo pipefail
pmc=https://pmc-oa-opendata.s3.amazonaws.com/PMC1955748.1
cath=https://download.cathdb.info/cath/releases/all-releases/v3_0_0/cath-classification-data
declare -A url=(
  [1471-2105-8-116-S1.txt]=$pmc/1471-2105-8-116-S1.txt
  [1471-2105-8-116-S2.tiff]=$pmc/1471-2105-8-116-S2.tiff
  [1471-2105-8-116-S3.xls]=$pmc/1471-2105-8-116-S3.xls
  [1471-2105-8-116-S4.tiff]=$pmc/1471-2105-8-116-S4.tiff
  [cath-domain-list-v3_0_0.txt]=$cath/cath-domain-list-v3_0_0.txt
  [cath-domain-boundaries-v3_0_0.txt]=$cath/cath-domain-boundaries-v3_0_0.txt
  [dir.cla.scop.1.69.txt]=https://scop.berkeley.edu/downloads/parse/dir.cla.scop.1.69.txt
  [aaindex2]=https://www.genome.jp/ftp/db/community/aaindex/aaindex2
  [BLOSUM62]=https://ftp.ncbi.nlm.nih.gov/blast/matrices/BLOSUM62
  [blosum62_3.blast]=https://ftp.ncbi.nlm.nih.gov/repository/blocks/unix/blosum/BLOSUM/blosum62_3.blast
)
declare -A sha=(
  [1471-2105-8-116-S1.txt]=dd6f084825f5348eb2a5478cdc4859adf844d3537c8007e13446ed0ff22a9f12
  [1471-2105-8-116-S2.tiff]=151741be25cf2f13ae6bc82ddd2b9c46e572af3741eb7898ed9b1b910311d5cd
  [1471-2105-8-116-S3.xls]=b3b524a337a3ada72b8a1dc02e437ff6f93f582d3268ca21535b45ae4a48acc0
  [1471-2105-8-116-S4.tiff]=c0340257652d16390debb8172fc64ad059fe4388eb708df0f93f9123c8ba4964
  [cath-domain-list-v3_0_0.txt]=29cbc48eeb4d4044aaafa3fc1ebc5690d201dbbfb79cdb3bc40b5c5da1025fe5
  [cath-domain-boundaries-v3_0_0.txt]=3a1fea4842b16d3ce0bc7d3f175dc18ad008f325c4456588f8f068f373ba3d99
  [dir.cla.scop.1.69.txt]=1f52da663c74e6e564fe4e0a0d9441c84d2ef23b944a68104b320cb3b7ab7bab
  [aaindex2]=d3eb30c075452aa737b111a3d127358d0b669d0e847fca967b253a05c7796aa9
  [BLOSUM62]=85510d3846ee6d5f4778e425cf8daf6e0dbb889b306f2d13434e1254780efb40
  [blosum62_3.blast]=faedaa40bf54bac37a6d5d012f17f9d958eef5184342d487d1f30588902c2b4f
)
for f in 1471-2105-8-116-S1.txt 1471-2105-8-116-S2.tiff 1471-2105-8-116-S3.xls 1471-2105-8-116-S4.tiff \
         cath-domain-list-v3_0_0.txt cath-domain-boundaries-v3_0_0.txt dir.cla.scop.1.69.txt aaindex2 \
         BLOSUM62 blosum62_3.blast; do
  if [ -n "${1:-}" ] && [ -f "$1/$f" ]; then
    cp "$1/$f" "$f"
  else
    for wait in 2 4 8 16 0; do
      curl -sSfL "${url[$f]}" -o "$f" && break
      [ "$wait" -gt 0 ] || { echo "$f: download failed (${url[$f]})" >&2; exit 1; }
      sleep "$wait"
    done
  fi
  got=$(shasum -a 256 "$f" | cut -d' ' -f1)
  [ "$got" = "${sha[$f]}" ] || { echo "$f: SHA-256 $got, expected ${sha[$f]}" >&2; exit 1; }
done

#!/usr/bin/env bash
# Download the inputs of the reproduction, check each file's SHA-256 and put it in the
# working directory:
#   S2.txt, S3.txt     Additional Files 2 and 3 (RPI2241 and RPI369 positives), PMC open access
#   pos2241.rpi        RPI2241 positives with sequences   } Dobbs-Lab/RPIMotif, the authors'
#   neg2241.rpi        RPI2241 negatives with sequences   } lab, Data/ at a pinned commit
#   ipminer369.tsv, ipminer369_protein.fa, ipminer369_rna.fa
#                      RPI369 with negatives as IPMiner (Pan et al. 2016) distributes it
# Usage: fetch_inputs.sh [DIR]   (DIR: reuse local copies with the names above)
set -euo pipefail
pmc="https://pmc-oa-opendata.s3.amazonaws.com/PMC3322362.1"
dobbs="https://raw.githubusercontent.com/Dobbs-Lab/RPIMotif/9cfa951d4ac782ed29558a8f7b00d2e626679f06/Data"
ipminer="https://raw.githubusercontent.com/xypan1232/IPMiner/68aa6d73b2f208c16e82ff199b04efe56a2ffc6f/ncRNA-protein"
declare -A url=(
  [S2.txt]="$pmc/1471-2105-12-489-S2.TXT"
  [S3.txt]="$pmc/1471-2105-12-489-S3.TXT"
  [pos2241.rpi]="$dobbs/Positive_Fasta_RPI2241.txt"
  [neg2241.rpi]="$dobbs/Negative_Fasta_RPI2241.txt"
  [ipminer369.tsv]="$ipminer/RPI369_all.txt"
  [ipminer369_protein.fa]="$ipminer/RPI369_protein.fa"
  [ipminer369_rna.fa]="$ipminer/RPI369_rna.fa"
)
declare -A sha=(
  [S2.txt]=eb785e026af28d1acea0f6b0dc1070ca928a01acdd918e51164a16fbe348e26a
  [S3.txt]=94554b2cb0e7b17b59019ee302e01f3965fc21b774ed0eb30a5cc0ca4e69c1ed
  [pos2241.rpi]=9880c52bbc9206a381048e326f57eeffe9f68b1f582b394d1925afbd4c379ff9
  [neg2241.rpi]=e848dacd47071e04a61665649a9afab79b3a170f061c262cbe91dde81b01e00b
  [ipminer369.tsv]=721436e009f243a7ae53ac4bc4068eb99899e7466c7eb44fc0f25d2bc5b72d82
  [ipminer369_protein.fa]=1fce075e671bd36f8fec9c006b7f0b8ac7de03ea6062f248d0a8fddae267ea0e
  [ipminer369_rna.fa]=56855489e67b4b7d0fbc70874ee7eb9225517bd6a389666c9bd09c44bb95d779
)
for f in "${!url[@]}"; do
  if [ -n "${1:-}" ] && [ -f "$1/$f" ]; then
    cp "$1/$f" "$f"
  else
    curl -fsSL --retry 3 --retry-all-errors --retry-delay 10 -o "$f" "${url[$f]}"
  fi
  got=$(shasum -a 256 "$f" | cut -d' ' -f1)
  [ "$got" = "${sha[$f]}" ] || { echo "$f: SHA-256 $got, expected ${sha[$f]}" >&2; exit 1; }
done

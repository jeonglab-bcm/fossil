#!/usr/bin/env bash
# Download the inputs and check them against params/SHA256SUMS.
#
# usage: fetch_inputs.sh OUTDIR [light|full] [SOURCES_DIR]
#
# light: the SCOP 1.53 benchmark (Liao and Noble), the Gist 2.3 source (its doc/sample.* run
#        checks the port) and the paper's PDF from PMC's open-access bucket (the published figures
#        in published/ are its embedded images; extract_figures.py checks they are identical).
# full:  also the lab's Pse-in-One 2.0 (its 2016 nrdb90 BLAST database) and NCBI BLAST+ 2.17.0,
#        to regenerate the PSI-BLAST profiles (about 4 CPU hours).
# SOURCES_DIR: a folder with local copies (same file names); used when present.
set -euo pipefail
out=$1; mode=${2:-light}; src=${3:-}
here=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$out"

get() {  # name url [fallback-url]
  local name=$1; shift
  if [ -n "$src" ] && [ -s "$src/$name" ]; then cp "$src/$name" "$out/$name"; return; fi
  for u in "$@"; do
    if curl -fsSL --retry 3 --retry-delay 5 -o "$out/$name" "$u"; then return; fi
    echo "download failed: $u" >&2
  done
  echo "could not download $name" >&2; exit 1
}

NOBLE=https://noble.gs.washington.edu/proj/svm-pairwise
WB=https://web.archive.org/web/2024id_
get scop.1.53.1e-25.fasta "$NOBLE/scop.1.53.1e-25.fasta" "$WB/$NOBLE/scop.1.53.1e-25.fasta"
get all_seq_fam_membership.txt "$NOBLE/all_seq_fam_membership.txt" "$WB/$NOBLE/all_seq_fam_membership.txt"
get gist-2.3.tar.gz https://svm.msl.ubc.ca/releases/gist-2.3.tar.gz "$WB/https://svm.msl.ubc.ca/releases/gist-2.3.tar.gz"
get PMC4015815.1.pdf https://pmc-oa-opendata.s3.amazonaws.com/PMC4015815.1/PMC4015815.1.pdf
names="scop.1.53.1e-25.fasta all_seq_fam_membership.txt gist-2.3.tar.gz PMC4015815.1.pdf"
if [ "$mode" = full ]; then
  get Pse-in-One-2.0.zip http://bliulab.net/Pse-in-One2.0/static/download/Pse-in-One-2.0.zip
  get ncbi-blast-2.17.0+-x64-linux.tar.gz https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/2.17.0/ncbi-blast-2.17.0+-x64-linux.tar.gz
  names="$names Pse-in-One-2.0.zip ncbi-blast-2.17.0+-x64-linux.tar.gz"
fi
( cd "$out" && for n in $names; do grep "  $n\$" "$here/params/SHA256SUMS"; done | sha256sum -c - )
mkdir -p "$out/gist" && tar xzf "$out/gist-2.3.tar.gz" -C "$out/gist" gist-2.3/doc
if [ "$mode" = full ]; then
  mkdir -p "$out/psein1" "$out/blast"
  unzip -q -o "$out/Pse-in-One-2.0.zip" 'Pse-in-One-2.0/psiblast/nrdb90/*' -d "$out/psein1"
  tar xzf "$out/ncbi-blast-2.17.0+-x64-linux.tar.gz" -C "$out/blast" ncbi-blast-2.17.0+/bin/psiblast
fi
echo "inputs ready in $out ($mode)"

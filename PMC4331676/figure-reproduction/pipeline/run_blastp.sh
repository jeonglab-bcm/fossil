#!/bin/bash
# blastp of the benchmark against PDB186 for the homology filter (light: seconds).
#   run_blastp.sh FASTA_DIR OUT.tsv
set -euo pipefail
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
${MAKEBLASTDB:-makeblastdb} -in "$1/pdb186.fasta" -dbtype prot -out "$d/pdb186" >/dev/null
${BLASTP:-blastp} -query "$1/benchmark.fasta" -db "$d/pdb186" -evalue 10 -max_target_seqs 186 \
  -outfmt "6 qseqid sseqid nident length qlen slen evalue" -seg no > "$2"

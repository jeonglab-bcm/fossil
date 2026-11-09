#!/usr/bin/env bash
# PSI-BLAST profile of every sequence in a FASTA file, one ASCII PSSM per sequence.
# Settings (the paper names PSI-BLAST on nr but gives no settings): 3 iterations, BLAST+ defaults
# otherwise (inclusion E-value 0.002), database UniRef100 release 2010_01 (the oldest UniProt
# archive; the 2005 nr is not archived).
# Usage: run_psiblast.sh FASTA DB OUTDIR THREADS [TASK NTASKS]   (TASK of NTASKS: every NTASKS-th sequence)
set -euo pipefail
fa=$1; db=$2; out=$3; threads=$4; task=${5:-0}; ntasks=${6:-1}
psiblast=${PSIBLAST:-psiblast}
mkdir -p "$out"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
awk -v t="$task" -v n="$ntasks" '/^>/{i++; keep=((i-1)%n==t); name=substr($1,2)} keep{print > "'"$tmp"'/" name ".fa"}' "$fa"
for q in "$tmp"/*.fa; do
  name=$(basename "$q" .fa)
  [ -s "$out/$name.pssm" ] && continue
  "$psiblast" -query "$q" -db "$db" -num_iterations 3 -num_threads "$threads" \
    -out_ascii_pssm "$tmp/$name.pssm" -save_pssm_after_last_round -out /dev/null 2> "$tmp/$name.err" \
    || { cat "$tmp/$name.err" >&2; exit 1; }
  mv "$tmp/$name.pssm" "$out/$name.pssm"
done

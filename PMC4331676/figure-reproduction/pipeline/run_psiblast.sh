#!/bin/bash
# Build one ASCII PSSM per sequence with PSI-BLAST (BLAST+), as in the paper: 3 iterations,
# E-value 0.001. Heavy: run as a Slurm array (see run_psiblast.sbatch), never on a login node.
#   run_psiblast.sh FASTA_DIR DB OUTDIR TASK NTASKS THREADS
# FASTA_DIR holds benchmark.fasta and pdb186.fasta; sequence k (over both files) goes to task
# k mod NTASKS. Output: OUTDIR/<set>_<id>.pssm. Existing PSSMs are kept (restartable).
set -euo pipefail
fasta_dir=$1; db=$2; outdir=$3; task=$4; ntasks=$5; threads=${6:-8}
psiblast=${PSIBLAST:-psiblast}
mkdir -p "$outdir"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
k=0
for set in benchmark pdb186; do
  while read -r header && read -r seq; do
    if (( k % ntasks == task )); then
      id=${header#>}; id=${id%%|*}
      out="$outdir/${set}_${id}.pssm"
      if [ ! -s "$out" ]; then
        printf '>%s\n%s\n' "$id" "$seq" > "$tmp/q.fa"
        "$psiblast" -query "$tmp/q.fa" -db "$db" -num_iterations 3 -evalue 0.001 \
          -num_threads "$threads" -out_ascii_pssm "$tmp/q.pssm" -out /dev/null
        if [ -s "$tmp/q.pssm" ]; then mv "$tmp/q.pssm" "$out"; else echo "no PSSM: $set $id" >&2; fi
      fi
    fi
    k=$((k + 1))
  done < "$fasta_dir/$set.fasta"
done

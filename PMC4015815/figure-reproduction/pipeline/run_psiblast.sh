#!/usr/bin/env bash
# PSI-BLAST frequency profiles for every benchmark sequence (SVM-DT input).
#
# usage: run_psiblast.sh FASTA DB OUTDIR [JOBS] [ITERATIONS] [EVALUE]
#
# Settings from the same lab's Pse-in-One 2.0 (profile.py, 2017): -num_iterations 3
# -evalue 0.001 against its nrdb90 (built 1 Apr 2016), ASCII PSSM output. The paper itself says
# only "PSI-BLAST ... against a non-redundant database". One query per file, named by its SCOP id;
# existing PSSMs are kept, so the step can be resumed.
set -euo pipefail
fasta=$1; db=$2; out=$3; jobs=${4:-4}; iters=${5:-3}; evalue=${6:-0.001}
psiblast=${PSIBLAST:-psiblast}
mkdir -p "$out/query" "$out/pssm" "$out/log"
awk -v d="$out/query" '/^>/{name=substr($1,2); f=d"/"name".fa"} {print > f}' "$fasta"
ls "$out/query" | sed 's/\.fa$//' | xargs -P "$jobs" -I{} bash -c '
  q="$0/query/{}.fa"; p="$0/pssm/{}.pssm"
  if [ ! -s "$p.done" ]; then
    "$1" -query "$q" -db "$2" -evalue "$4" -num_iterations "$3" -num_threads 1 \
      -out_ascii_pssm "$p" -outfmt 6 -out /dev/null > "$0/log/{}.log" 2>&1 || true
    echo ok > "$p.done"
  fi' "$out" "$psiblast" "$db" "$iters" "$evalue"
echo "PSSMs written: $(ls "$out/pssm" | grep -c '\.pssm$') of $(ls "$out/query" | wc -l)"

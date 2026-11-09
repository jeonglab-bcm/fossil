#!/usr/bin/env bash
# PSI-BLAST for every benchmark sequence (SVM-DT input).
#
# usage: run_psiblast.sh FASTA DB OUTDIR [JOBS] [ITERATIONS] [EVALUE] [ALIGN]
#
# ITERATIONS, EVALUE: -num_iterations and -evalue. EVALUE "default" leaves PSI-BLAST's own (10).
#   2017 (the lab's Pse-in-One 2.0, profile.py): 3 iterations, -evalue 0.001.
#   2008 (the lab's Top-n-gram paper, ref. [28]): "default except that the number of iterations
#   is set to 10".
# ALIGN: "align" also writes every round's alignments (outfmt 7, query and subject segments) to
#   OUTDIR/aln/<id>.tsv, from which profile2008.py builds the 2008 frequency profiles.
#
# One query per file, named by its SCOP id. A query is marked done only when PSI-BLAST exits 0
# and wrote its PSSM; a failed search is logged and the run stops with an error (exit 1) after
# the other queries finish. Existing done queries are kept, so the step can be resumed.
set -euo pipefail
fasta=$1; db=$2; out=$3; jobs=${4:-4}; iters=${5:-3}; evalue=${6:-0.001}; align=${7:-}
psiblast=${PSIBLAST:-psiblast}
mkdir -p "$out/query" "$out/pssm" "$out/log"
[ "$align" = align ] && mkdir -p "$out/aln"
awk -v d="$out/query" '/^>/{name=substr($1,2); f=d"/"name".fa"} {print > f}' "$fasta"
export out psiblast db iters evalue align
status=0
ls "$out/query" | sed 's/\.fa$//' | xargs -P "$jobs" -I{} bash -c '
  id={}; q="$out/query/$id.fa"; p="$out/pssm/$id.pssm"
  [ -s "$p.done" ] && exit 0
  args=(-query "$q" -db "$db" -num_iterations "$iters" -num_threads 1 -out_ascii_pssm "$p")
  [ "$evalue" != default ] && args+=(-evalue "$evalue")
  if [ "$align" = align ]; then
    args+=(-outfmt "7 qseqid sseqid evalue qstart qend sstart send qseq sseq" -out "$out/aln/$id.tsv")
  else
    args+=(-outfmt 6 -out /dev/null)
  fi
  if "$psiblast" "${args[@]}" > "$out/log/$id.log" 2>&1 && [ -s "$p" ]; then
    echo ok > "$p.done"
  else
    echo "PSI-BLAST failed for $id (see $out/log/$id.log)" >&2
    exit 1
  fi' || status=$?
done_n=$(ls "$out/pssm" | grep -c '\.pssm\.done$' || true)
echo "PSSMs done: $done_n of $(ls "$out/query" | wc -l)"
if [ "$status" -ne 0 ]; then
  echo "at least one PSI-BLAST search failed" >&2
  exit 1
fi

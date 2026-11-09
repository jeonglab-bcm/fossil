#!/usr/bin/env bash
# The same steps as main.nf, in order, without Nextflow (the committed output/ was written this
# way; main.nf runs the same scripts with the same arguments).
#
# usage: run_local.sh OUTDIR [SOURCES_DIR] [DMAX] [WORKERS] [profiles]
#   DMAX     default 0,10,20,40,50,60,80,100,150,200
#   profiles regenerate the PSI-BLAST profiles instead of reading pipeline/inputs/
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
P=$here/pipeline
out=$(mkdir -p "$1" && cd "$1" && pwd); src=${2:-}; dmax=${3:-0,10,20,40,50,60,80,100,150,200}
workers=${4:-4}; profiles=${5:-}
py=${PYTHON:-python3}
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
cd "$work"

bash "$P/fetch_inputs.sh" downloads "$([ "$profiles" = profiles ] && echo full || echo light)" "$src"
D=$work/downloads
$py "$P/extract_figures.py" "$D/PMC4015815.1.pdf" "$here/published" "$out/figures_check.json"
$py "$P/port_check.py" "$D/gist/gist-2.3/doc" "$out/port_check.json"

if [ "$profiles" = profiles ]; then
  PSIBLAST=$D/blast/ncbi-blast-2.17.0+/bin/psiblast bash "$P/run_psiblast.sh" "$D/scop.1.53.1e-25.fasta" \
    "$D/psein1/Pse-in-One-2.0/psiblast/nrdb90/nrdb90" psiblast "$workers" 10 default align
  $py "$P/profile2008.py" "$D/scop.1.53.1e-25.fasta" psiblast/aln top1.fasta "$out/top1_stats.json" \
    --workers "$workers"
  gzip -n -9 -c top1.fasta > "$out/top1_nrdb90_i10_2008.fasta.gz"
else
  gunzip -c "$P/inputs/top1_nrdb90_i10_2008.fasta.gz" > top1.fasta
fi

for m in dr dt; do
  seqs=residues; [ $m = dt ] && seqs=top1:top1.fasta
  $py "$P/run_sweep.py" --fasta "$D/scop.1.53.1e-25.fasta" --membership "$D/all_seq_fam_membership.txt" \
    --sequences $seqs --dmax "$dmax" --seed 1 --workers "$workers" --out fresh_$m.csv
  $py "$P/merge_sweep.py" fresh_$m.csv "$here/output/sweep_$m.csv" "$out/sweep_$m.csv"
  for fam in 2.5.1.3 2.5.1.1; do
    $py "$P/discriminant_weights.py" --fasta "$D/scop.1.53.1e-25.fasta" \
      --membership "$D/all_seq_fam_membership.txt" --sequences $seqs --family $fam --dmax 150 \
      --seed 1 --out "$out/weights_${m}_${fam}.json"
  done
done

cd "$out"
PUB=$here/published
$py "$P/figure3_axes.py" "$PUB/figure-3.png" fig3_published.json
$py "$P/figure3.py" "$PUB/figure-3.png" fig3_published.json sweep_dr.csv sweep_dt.csv .
$py "$P/figure4.py" "$PUB/figure-4.png" weights_dt_2.5.1.3.json weights_dr_2.5.1.3.json . \
  weights_dr_2.5.1.1.json weights_dt_2.5.1.1.json
$py "$P/figure5_read.py" "$PUB/figure-5.png" fig5_published.json
$py "$P/figure5.py" "$PUB/figure-5.png" fig5_published.json weights_dt_2.5.1.3.json weights_dr_2.5.1.3.json .
$py "$P/tables.py" sweep_dr.csv sweep_dt.csv weights_dr_2.5.1.3.json weights_dt_2.5.1.3.json tables.json
for f in 3 4 5; do
  $py "$P/compare_figure.py" --published "$PUB/figure-$f.png" --render fig${f}_ours.png \
    --out compare/figure-$f --published-grey 255 --render-grey 255
done
$py "$P/build_results.py" . "$here/results_notes.json" results.json
$py "$P/check_results.py" results.json --write --skip-files
$py "$P/build_page.py" . "$PUB" site/index.html
$py "$P/check_reproduction.py" . "$here/output" report.md || true
echo "done: $out"

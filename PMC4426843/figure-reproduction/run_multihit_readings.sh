#!/bin/bash
# Table 2's multi-hit column under several readings of the method (issue #33), on Skyriver.
#
# Usage (from this folder, on the login node; everything heavy is submitted to Slurm):
#   bash run_multihit_readings.sh WORK [PYTHON]
#
# WORK must hold what a --full run makes and the committed site tables do not keep:
#   WORK/utr/{hsa,mmu}.map.tsv          dedup_utrs.py maps (UTRS process)
#   WORK/hits/{hsa,mmu}/*.pairs.tsv     miRanda per-pair summaries (MIRANDA process)
#   WORK/go/{hsa,mmu}_go_bp.tsv         build_go.py tables (GO process)
#   WORK/sites/{hsa,mmu}.tsv            the reference site tables (sites_codec.py decode of
#                                       pipeline/inputs/sites_*.txt.xz, or gene_sites.py --sites max)
# It writes WORK/sites/<sp>.<reading>.tsv, WORK/emp/<sp>_<size>.<reading>.counts.tsv (one Slurm job
# per reading and null: 8 CPUs, about 10 minutes, defq15), and then
# WORK/readings/multihit_readings.csv and multihit_terms.tsv.gz (copied to output/ for the commit).
#
# Readings, each one change against the reference (Table 2: most sites on one UTR, seed as Table 2):
#   seed2     the reference with another seed (seed + 500,000): Monte Carlo noise
#   longest   sites on the gene's longest passing UTR
#   sum       sites summed over the gene's distinct passing UTRs
#   sum_tx    sites summed over the gene's passing transcripts
#   univ      overlap denominator over GO-annotated genes only
#   allpairs  multi-hit sites from every pair miRanda reports, not only pairs passing the thresholds
set -euo pipefail
WORK=$(realpath "$1"); PY=${2:-python3}
HERE=$(cd "$(dirname "$0")" && pwd); P=$HERE/pipeline
mkdir -p "$WORK/slurm" "$WORK/emp" "$WORK/readings"
cd "$WORK"

sites=$(sbatch --parsable -p debugq -t 01:00:00 -c 1 --mem 16G -J mh-sites -o slurm/mh-sites-%j.out --wrap "
  set -e
  for sp in hsa mmu; do
    for v in longest sum sum_tx; do $PY -I $P/gene_sites.py utr/\$sp.map.tsv sites/\$sp.\$v.tsv hits/\$sp/*.pairs.tsv --sites \$v; done
    $PY -I $P/gene_sites.py utr/\$sp.map.tsv sites/\$sp.allpairs.tsv hits/\$sp/*.pairs.tsv --all-pairs
  done")

jobs=""
submit() {  # reading sp species size seed extra-args...
  local v=$1 sp=$2 species=$3 size=$4 seed=$5; shift 5
  jobs="$jobs:$(sbatch --parsable -p defq15 -t 02:00:00 -c 8 --mem 24G --dependency=afterok:$sites \
    -J mh-$sp-$size-$v -o slurm/mh-%x-%j.out --wrap "
    export OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
    $PY -I $P/empirical.py --go go/${sp}_go_bp.tsv --lists $P/inputs/s3_mirna_lists.tsv --species $species \
      --size $size --iterations 999999 --seed $seed --out emp/${sp}_${size}.$v $*")"
}
for spec in "hsa Human 0 1 2 3 5 8 9 10 11 15 18 25 26 39 46 130 176" "mmu Mouse 1000 1 8 10 12 27 37"; do
  set -- $spec; sp=$1; species=$2; base=$3; shift 3
  for size in "$@"; do
    seed=$((base + size))
    submit seed2 $sp $species $size $((seed + 500000)) --sites sites/$sp.tsv
    for v in longest sum sum_tx; do submit $v $sp $species $size $seed --sites sites/$sp.$v.tsv; done
    submit univ $sp $species $size $seed --sites sites/$sp.tsv --denominator universe
    submit allpairs $sp $species $size $seed --sites sites/$sp.tsv --multi-sites sites/$sp.allpairs.tsv
  done
done

sbatch -p debugq -t 00:20:00 -c 1 --mem 8G -J mh-summary -o slurm/mh-summary-%j.out --dependency=afterok$jobs --wrap "
  set -e
  mkdir -p readings/max; ln -sf $HERE/output/empirical/*.counts.tsv.gz readings/max/
  args=max=readings/max
  for v in seed2 longest sum sum_tx univ allpairs; do
    mkdir -p readings/\$v; ln -sf \$PWD/emp/*.\$v.counts.tsv readings/\$v/; args=\"\$args \$v=readings/\$v\"
  done
  $PY -I $P/multihit_readings.py $P/params/published_table2.csv readings \$args"

#!/bin/bash
# Table 2's multi-hit column under several readings of the method (issue #33), on Skyriver.
#
# Usage (from this folder, on the login node; everything heavy is submitted to Slurm):
#   bash run_multihit_readings.sh WORK [PYTHON]
#   READINGS="last_mart idkey" bash run_multihit_readings.sh WORK [PYTHON]   (only these readings;
#   the summary still covers every reading whose counts are in WORK/emp)
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
# Readings from the PR #34 review: the authors' script (README on the Internet Archive) reads
# miRanda's per-transcript '>>' lines from a BioMart 3' UTR FASTA, so a site table keyed while
# reading the file keeps one transcript's count. WORK/orders/<sp>.{mart,txid}.txt are transcript IDs
# in the row order of the Ensembl 75 mart table <species>_gene_ensembl__transcript__main and sorted.
#   last_mart / last_txid / last_gtf  the gene's last passing transcript in mart / ID / GTF order
#   first_mart                        the gene's first passing transcript in mart order
#   idkey             most sites on one UTR per Ensembl gene ID; IDs sharing a name are summed
#   idkey_last_mart   last_mart per Ensembl gene ID; IDs sharing a name are summed
set -euo pipefail
WORK=$(realpath "$1")
HERE=$(cd "$(dirname "$0")" && pwd); P=$HERE/pipeline
PY=${2:-$HERE/../.env/bin/python}  # needs numpy and scipy on the compute nodes (as run_skyriver.sbatch)
mkdir -p "$WORK/slurm" "$WORK/emp" "$WORK/readings"
cd "$WORK"

ALL="seed2 longest sum sum_tx univ allpairs last_mart last_txid last_gtf first_mart idkey idkey_last_mart"
READINGS=${READINGS:-$ALL}
opts() {  # gene_sites.py options of a reading that has its own site table
  case $1 in
    longest|sum|sum_tx) echo "--sites $1" ;;
    allpairs) echo "--all-pairs" ;;
    last_gtf) echo "--sites last" ;;
    last_mart|last_txid|first_mart) echo "--sites ${1%%_*} --order orders/\$sp.${1#*_}.txt" ;;
    idkey) echo "--key gene_id" ;;
    idkey_last_mart) echo "--sites last --order orders/\$sp.mart.txt --key gene_id" ;;
  esac
}
cmds=""
for v in $READINGS; do
  o=$(opts $v); [ -n "$o" ] && cmds="$cmds $PY -I $P/gene_sites.py utr/\$sp.map.tsv sites/\$sp.$v.tsv hits/\$sp/*.pairs.tsv $o;"
done
sites=$(sbatch --parsable -p debugq -t 02:00:00 -c 1 --mem 16G -J mh-sites -o slurm/mh-sites-%j.out --wrap "
  set -e
  for sp in hsa mmu; do $cmds done")

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
    for v in $READINGS; do
      case $v in
        seed2) submit seed2 $sp $species $size $((seed + 500000)) --sites sites/$sp.tsv ;;
        univ) submit univ $sp $species $size $seed --sites sites/$sp.tsv --denominator universe ;;
        allpairs|idkey|idkey_last_mart)  # targets as in the reference; only the site counts change
          submit $v $sp $species $size $seed --sites sites/$sp.tsv --multi-sites sites/$sp.$v.tsv ;;
        *) submit $v $sp $species $size $seed --sites sites/$sp.$v.tsv ;;
      esac
    done
  done
done

sbatch -p debugq -t 00:20:00 -c 1 --mem 8G -J mh-summary -o slurm/mh-summary-%j.out --dependency=afterok$jobs --wrap "
  set -e
  mkdir -p readings/max; ln -sf $HERE/output/empirical/*.counts.tsv.gz readings/max/
  args=max=readings/max
  for v in $ALL; do
    ls emp/*.\$v.counts.tsv >/dev/null 2>&1 || continue
    mkdir -p readings/\$v; ln -sf \$PWD/emp/*.\$v.counts.tsv readings/\$v/; args=\"\$args \$v=readings/\$v\"
  done
  $PY -I $P/multihit_readings.py $P/params/published_table2.csv readings \$args"

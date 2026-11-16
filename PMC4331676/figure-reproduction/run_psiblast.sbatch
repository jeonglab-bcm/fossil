#!/bin/bash
# PSSMs for PMC4331676 on Skyriver: sbatch --array=0-39 run_psiblast.sbatch DB_PATH OUTDIR
#SBATCH --job-name=p22psi
#SBATCH --partition=defq610
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --output=/home/sofias/fossil-issue22/PMC4331676/work/logs/psi-%A_%a.out
set -euo pipefail
here=/home/sofias/fossil-issue22/PMC4331676
export PSIBLAST=$here/work/ncbi-blast-2.16.0+/bin/psiblast
bash $here/figure-reproduction/pipeline/run_psiblast.sh $here/work/data "$1" "$2" \
  "$SLURM_ARRAY_TASK_ID" 40 4

#!/bin/bash
# Leave-one-out scores for one dataset and method, as a Slurm job array over shards.
#
#   sbatch --array=0-47 --export=ALL,DATASET=e,METHOD=blmt figure-reproduction/run_skyriver.sbatch
#
# Each task writes work/scores/parts/<dataset>_<method>_<shard>.npz; merge_scores.sh puts them
# together. The repository folder is shared, the compute nodes' /tmp is not.
#SBATCH --job-name=blmdti
#SBATCH --partition=defq15
#SBATCH --time=08:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --output=work/logs/%x_%A_%a.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-.}"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
SHARDS=${SLURM_ARRAY_TASK_COUNT:-1}
SHARD=${SLURM_ARRAY_TASK_ID:-0}
mkdir -p work/scores/parts work/logs
.venv/bin/python figure-reproduction/pipeline/compute_scores.py \
  --data sources/yamanishi2008 --dataset "$DATASET" --method "$METHOD" \
  --shard "$SHARD" --shards "$SHARDS" \
  --out "work/scores/parts/${DATASET}_${METHOD}_${SHARD}.npz"

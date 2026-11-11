#!/bin/bash
# Run line $SLURM_ARRAY_TASK_ID of a task file on a compute node (never the login node).
#   sbatch --array=1-N figure-reproduction/run_tasks.sbatch TASKFILE
#SBATCH --job-name=pmc2666661
#SBATCH --partition=defq15
#SBATCH --time=1-00:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=3G
#SBATCH --output=work/logs/%x_%A_%a.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR}"
export PYTHONPATH="$PWD/package/src" OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1 NUMBA_CACHE_DIR="$PWD/work/numba-cache"
line=$(sed -n "${SLURM_ARRAY_TASK_ID}p" "$1")
echo "$line"
eval "$line"

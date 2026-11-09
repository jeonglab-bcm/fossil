#!/bin/bash
# The leave-one-out of Figs 3 and 5 on the Skyriver cluster: one SVM pair fitted per held-out chain
# (1,868 chains for the SPCH-SVM, 1,972 for the SPCHDE-SVM; about 30 CPU hours in all).
# Submit from the repository root after `run_svm.py prepare` has written $SVM (default PMC1800866/work/svm):
#   sbatch PMC1800866/figure-reproduction/run_loo.sbatch
# then merge:  python PMC1800866/figure-reproduction/pipeline/run_svm.py merge CH $SVM  (and CHDE)
#SBATCH --job-name=p19loo
#SBATCH --partition=debugq
#SBATCH --time=08:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=6G
#SBATCH --array=0-95
#SBATCH --output=PMC1800866/work/logs/loo-%A_%a.out
set -euo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
SVM=${SVM:-PMC1800866/work/svm}
PY=${PY:-PMC1800866/.venv/bin/python}
i=$SLURM_ARRAY_TASK_ID
if [ "$i" -lt 48 ]; then v=CH; t=$i; else v=CHDE; t=$((i - 48)); fi
"$PY" PMC1800866/figure-reproduction/pipeline/run_svm.py loo $v "$SVM" $t 48

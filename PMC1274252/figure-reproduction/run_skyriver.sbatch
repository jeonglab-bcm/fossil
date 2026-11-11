#!/bin/bash
# Run the whole PMC1274252 pipeline on Skyriver (BCM) inside one Slurm job, never on the login node.
#   sbatch PMC1274252/figure-reproduction/run_skyriver.sbatch      (from the repository root)
# PYTHON: an interpreter with requirements.txt installed (default: PMC1274252/.venv/bin/python).
#SBATCH --job-name=pmc1274252
#SBATCH --partition=debugq
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --output=PMC1274252/work/nextflow-%j.out
set -euo pipefail
module load nextflow/25.04.6
export PATH="$HOME/.local/bin:$PATH"
PY=${PYTHON:-$PWD/PMC1274252/.venv/bin/python}
nextflow run PMC1274252/figure-reproduction/main.nf --outdir ${OUTDIR:-PMC1274252/work/results} --python "$PY" \
  ${SOURCES:+--sources $SOURCES} -ansi-log false -work-dir PMC1274252/work/nf-work "$@"

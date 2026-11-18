#!/bin/bash
# Run the whole pipeline on the Skyriver cluster. The Nextflow head runs in this job (debugq); with
# -profile skyriver every process is a separate Slurm job on defq15.
#SBATCH --job-name=pmc4765871-nf
#SBATCH --partition=debugq
#SBATCH --time=08:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --output=nextflow-%j.out
set -euo pipefail
module load nextflow/25.04.6
# Submit from the repository root: sbatch PMC4765871/figure-reproduction/run_skyriver.sbatch [--full]
VENV=${VENV:-$PWD/PMC4765871/.venv}   # Python 3.12 with requirements.txt
nextflow run PMC4765871/figure-reproduction/main.nf -profile skyriver --outdir "${OUTDIR:-results}" \
  --python "$VENV/bin/python" ${SOURCES:+--sources "$SOURCES"} -ansi-log false "$@"

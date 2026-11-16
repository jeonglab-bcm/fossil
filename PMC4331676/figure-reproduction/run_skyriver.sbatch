#!/bin/bash
# Run the whole pipeline on the Skyriver cluster. The Nextflow head runs in this job; with
# -profile skyriver every process is a separate Slurm job on defq610, never on the login node.
# Submit from the repository root:
#   sbatch PMC4331676/figure-reproduction/run_skyriver.sbatch
#   sbatch PMC4331676/figure-reproduction/run_skyriver.sbatch --blastdb /path/uniref100 --blast /path/ncbi-blast-2.16.0+/bin
#SBATCH --job-name=pmc4331676-nf
#SBATCH --partition=defq610
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --output=PMC4331676/work/logs/nextflow-%j.out
set -euo pipefail
module load nextflow/25.04.6
export PATH=$HOME/.local/bin:$PATH   # uv, for the package check
VENV=${VENV:-$PWD/PMC4331676/.env}   # Python 3.12 with requirements.txt and ./PMC4331676/package
nextflow run PMC4331676/figure-reproduction/main.nf -profile skyriver --outdir "${OUTDIR:-results}" \
  --python "$VENV/bin/python" ${SOURCES:+--sources "$SOURCES"} -ansi-log false "$@"

#!/bin/bash
# Run the whole pipeline on the Skyriver cluster. The Nextflow head runs in this job (debugq); with
# -profile skyriver every process is a separate Slurm job, never on the login node.
#SBATCH --job-name=pmc1800866-nf
#SBATCH --partition=debugq
#SBATCH --time=08:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --output=pmc1800866-nf-%j.out
set -euo pipefail
module load nextflow/25.04.6
# Submit from the repository root: sbatch PMC1800866/figure-reproduction/run_skyriver.sbatch [--full]
VENV=${VENV:-$PWD/PMC1800866/.venv}   # Python 3.12 with requirements.txt and the package installed
export PATH="$VENV/bin:$PATH"
nextflow run PMC1800866/figure-reproduction/main.nf -profile skyriver --outdir "${OUTDIR:-results}" \
  --python "$VENV/bin/python" ${SOURCES:+--sources "$SOURCES"} -ansi-log false "$@"

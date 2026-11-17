#!/bin/bash
# Run the pipeline on Skyriver: the Nextflow head in this job, every process as its own Slurm job.
#   sbatch PMC2949886/figure-reproduction/run_skyriver.sbatch [--full]
# Needs R 4.3.3 with multtest, qvalue, limma, jsonlite, knitr, markdown and testthat in
# PMC2949886/.Rlib, and the Python packages of requirements.txt in PMC2949886/.venv.
#SBATCH --job-name=pmc2949886-nf
#SBATCH --partition=debugq
#SBATCH --time=4:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --output=PMC2949886/work/logs/nextflow_%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR}"
source /etc/profile.d/modules.sh
module load R/4.3.3 nextflow/25.04.6
export R_LIBS_USER="$PWD/PMC2949886/.Rlib"
export PATH="$PWD/PMC2949886/.venv/bin:$HOME/.local/bin:$PATH"
nextflow run PMC2949886/figure-reproduction/main.nf -profile skyriver --outdir PMC2949886/work/results \
  -work-dir PMC2949886/work/nf-work -ansi-log false --sources PMC2949886/sources "$@"

#!/bin/bash
# Run the pipeline on Skyriver: the Nextflow head in this job, every process as its own Slurm job.
#   sbatch PMC2853684/figure-reproduction/run_skyriver.sbatch [--sources DIR]
# Expects PMC2853684/.venv (requirements.txt), MCL in PMC2853684/.mcl (bioconda mcl=14.137) and Java 21.
#SBATCH --job-name=pmc2853684-nf
#SBATCH --partition=defq15
#SBATCH --time=2:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --output=PMC2853684/work/logs/nextflow_%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR}"
source /etc/profile.d/modules.sh
module load nextflow/25.04.6 java/21
export PATH="$PWD/PMC2853684/.venv/bin:$PWD/PMC2853684/.mcl/bin:$HOME/.local/bin:$PATH"
nextflow run PMC2853684/figure-reproduction/main.nf -profile skyriver --outdir PMC2853684/work/results \
  -work-dir PMC2853684/work/nf-work -ansi-log false "$@"

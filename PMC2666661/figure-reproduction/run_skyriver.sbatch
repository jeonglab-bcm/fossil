#!/bin/bash
# Run the pipeline on Skyriver: the Nextflow head in this job, every process as its own Slurm job.
#   sbatch PMC2666661/figure-reproduction/run_skyriver.sbatch [--full] [--port_check]
#SBATCH --job-name=pmc2666661-nf
#SBATCH --partition=debugq
#SBATCH --time=8:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --output=PMC2666661/work/logs/nextflow_%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR}"
source /etc/profile.d/modules.sh
module load nextflow/25.04.6
export PATH="$PWD/PMC2666661/.venv/bin:$HOME/.local/bin:$PATH"
nextflow run PMC2666661/figure-reproduction/main.nf -profile skyriver --outdir PMC2666661/work/results \
  -work-dir PMC2666661/work/nf-work -ansi-log false "$@"

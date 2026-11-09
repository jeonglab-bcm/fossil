#!/bin/bash
# Run the whole pipeline on Skyriver inside one Slurm allocation, never on the login node.
# Submit from the repository root:
#
#   sbatch PMC2735674/figure-reproduction/run_skyriver_pipeline.sbatch [--full]
#SBATCH --job-name=pmc2735674
#SBATCH --partition=debugq
#SBATCH --time=08:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --output=PMC2735674/figure-reproduction/nextflow-%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-.}"
module load nextflow/25.04.6
export PATH="$PWD/PMC2735674/.venv/bin:$PATH"
# The whole pipeline runs inside this one allocation (Nextflow's local executor), so its steps do
# not queue one by one. Use -profile skyriver instead to give every step its own Slurm job.
nextflow run PMC2735674/figure-reproduction/main.nf \
  --outdir "${OUTDIR:-PMC2735674/work/run}" --cpus "${SLURM_CPUS_PER_TASK:-4}" \
  --sources PMC2735674/sources -ansi-log false "$@"

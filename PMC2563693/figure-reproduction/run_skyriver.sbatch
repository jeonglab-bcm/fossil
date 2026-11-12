#!/bin/bash
# Run the PMC2563693 pipeline on Skyriver (BCM) from the repository root, never on the login node:
#   sbatch PMC2563693/figure-reproduction/run_skyriver.sbatch            # default (CI) run, local executor
#   sbatch PMC2563693/figure-reproduction/run_skyriver.sbatch --full     # every CV repeat, one Slurm job per chunk
#SBATCH --job-name=pmc2563693-nf
#SBATCH --partition=debugq
#SBATCH --time=06:00:00
#SBATCH --cpus-per-task=16
#SBATCH --mem=48G
#SBATCH --output=pmc2563693-nf-%j.out
set -euo pipefail
module load nextflow/25.04.6
PY=${PY:-$PWD/PMC2563693/.venv/bin/python}
if [[ "${1:-}" == "--full" ]]; then
  nextflow run PMC2563693/figure-reproduction/main.nf --outdir results --python "$PY" --full -profile skyriver -ansi-log false
else
  nextflow run PMC2563693/figure-reproduction/main.nf --outdir results --python "$PY" -ansi-log false ${NF_EXTRA:-}
fi

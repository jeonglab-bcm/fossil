#!/bin/bash
# Full run on the Skyriver cluster, inside one Slurm job on defq15 (Nextflow's local executor uses
# the job's cores; add "-profile skyriver" to send each task to defq15 as its own job instead).
# From the repository root:
#   sbatch PMC2711306/figure-reproduction/run_skyriver.sbatch [extra nextflow arguments]
# Uses the reproduction's virtual environment (PMC2711306/.venv: requirements.txt and the package)
# and GNU Octave from conda-forge in PMC2711306/.octave for the port check.
#SBATCH --job-name=pmc2711306
#SBATCH --partition=defq15
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=PMC2711306/figure-reproduction/nextflow-%j.out
set -euo pipefail
module load nextflow/25.04.6
root=$(pwd)
export OCTAVE_HOME=$root/PMC2711306/.octave
export PATH=$HOME/.local/bin:$PATH
nextflow run PMC2711306/figure-reproduction/main.nf -ansi-log false \
  --python "$root/PMC2711306/.venv/bin/python" --octave "$OCTAVE_HOME/bin/octave-cli" \
  --sources "$root/PMC2711306/work/fetchfull" "$@"

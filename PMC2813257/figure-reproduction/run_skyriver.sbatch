#!/bin/bash
# Run the pipeline on Skyriver (BCM): the Nextflow head runs inside this job and submits every
# process as its own Slurm job. Never run the pipeline on the login node.
#
#   sbatch PMC2813257/figure-reproduction/run_skyriver.sbatch
#SBATCH --job-name=pmc2813257
#SBATCH --partition=debugq
#SBATCH --time=04:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --output=PMC2813257/figure-reproduction/nextflow-%j.out
set -euo pipefail
module load nextflow/25.04.6
nextflow run PMC2813257/figure-reproduction/main.nf -profile skyriver \
    --outdir "${OUTDIR:-results}" --python "${PYTHON:-python3}" -ansi-log false "$@"

#!/bin/bash
# Run the whole pipeline on the Skyriver cluster. The Nextflow head runs in this job (debugq);
# with -profile skyriver every process is a separate Slurm job on defq15.
#SBATCH --job-name=pmc4426843-nf
#SBATCH --partition=debugq
#SBATCH --time=08:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --output=nextflow-%j.out
set -euo pipefail
module load nextflow/25.04.6
# Submit from PMC4426843/figure-reproduction (sbatch run_skyriver.sbatch [--full]), or pass
# --chdir=PMC4426843/figure-reproduction; the job starts in that folder.
HERE=$PWD
ENV=${ENV:-$HERE/../.env}   # conda env: miranda 3.3a, R 4.4, Python 3.12, numpy, scipy, xlrd, pillow
nextflow run "$HERE/main.nf" -profile skyriver --outdir "${OUTDIR:-results}" \
  --python "$ENV/bin/python" --rscript "$ENV/bin/Rscript" --miranda "$ENV/bin/miranda" \
  ${SOURCES:+--sources "$SOURCES"} -ansi-log false "$@"

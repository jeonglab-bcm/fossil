#!/bin/bash
# Run the whole pipeline on the Skyriver cluster. The Nextflow head runs in this job (debugq);
# with -profile skyriver every process is a separate Slurm job on defq15.
#SBATCH --job-name=pmc2349296-nf
#SBATCH --partition=debugq
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --output=nextflow-%j.out
set -euo pipefail
module load nextflow/25.04.6
# Submit from PMC2349296/figure-reproduction (sbatch run_skyriver.sbatch), or pass
# --chdir=PMC2349296/figure-reproduction; the job starts in that folder.
HERE=$PWD
ENV=${ENV:-$HERE/../.env}   # conda env with R 4.4, Python 3.12, numpy, pillow, scipy
nextflow run "$HERE/main.nf" -profile skyriver --outdir "${OUTDIR:-results}" \
  --python "$ENV/bin/python" --rscript "$ENV/bin/Rscript" ${SOURCES:+--sources "$SOURCES"} -ansi-log false "$@"

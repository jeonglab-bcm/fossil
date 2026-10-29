#!/bin/sh
# Independent refit of the 24 conversion-reaction models (Table 1): 2000 Latin hypercube starts
# each, L-BFGS-B. Usage: refit_all.sh SOURCES OUTDIR [PYTHON]
set -eu
SRC=$1; OUT=$2; PY=${3:-python3}
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$OUT"
for study in cr1 cr2; do
  for model in 1norm 1logn_mean 1logn_median 2norm_k1a 2logn_mean_k1a 2logn_median_k1a \
               2norm_k1b 2logn_mean_k1b 2logn_median_k1b 2norm_k2 2logn_mean_k2 2logn_median_k2; do
    "$PY" "$HERE/refit.py" --sources "$SRC" --study "$study" --model "$model" --starts 2000 \
      --out "$OUT/${study}__${model}.json" 2>/dev/null
  done
done

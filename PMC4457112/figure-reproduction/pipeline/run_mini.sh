#!/usr/bin/env bash
# The mini reproduction: every step of the full run on a few baseline files, small enough for CI.
# Usage: run_mini.sh DOWNLOADS NNNN,NNNN,... OUT_DIR WORKERS
# Training: the files' 1987-2010 citations (all of them, not 7.5%); tests: their 2011 and 2012 citations.
# Forward selection and cross-validation with one 2-fold split.
set -euo pipefail
dl=$1; files=$2; out=$3; workers=${4:-4}
here=$(cd "$(dirname "$0")" && pwd)
py=${PYTHON:-python3}
mkdir -p "$out"
$py "$here/extract_medline.py" --out medline --files "$files" --local "$dl" --workers "$workers"
$py "$here/manifest.py" medline/manifest.json "$out/baseline_manifest.json"
$py "$here/build_dataset.py" medline data --fraction 1.0
cp data/dataset.json "$out/"
$py "$here/featurize.py" data --workers "$workers"
$py "$here/models.py" data "$out" --workers 2 --selection-repeats 1 --cv-repeats 1
$py "$here/score_all.py" medline data "$out" --workers "$workers"

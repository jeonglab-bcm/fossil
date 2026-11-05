#!/bin/bash
# Run miRanda 3.3a with its default settings and keep the per-pair summary lines ('>>').
# Usage: run_miranda.sh MIRNAS.fa UTRS.fa OUT.tsv [MIRANDA]
# Output columns: mirna, utr, total score, total energy, max score, max energy, strand,
# mirna length, utr length, site positions (space separated).
# The paper's thresholds (score > 155, energy < -20 kcal/mol) are applied downstream, to the
# totals: Supplementary Table S3's target lists match that reading, not per-site filtering.
set -euo pipefail
MIRANDA=${4:-miranda}
"$MIRANDA" "$1" "$2" ${MIRANDA_OPTS:-} -quiet \
  | awk -F'\t' 'BEGIN{OFS="\t"} /^>>/ {sub(/^>>/, "", $1); print}' > "$3.tmp"
mv "$3.tmp" "$3"

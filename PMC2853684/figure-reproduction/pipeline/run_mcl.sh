#!/usr/bin/env bash
# MCL clusterings of both networks at inflation 2.0 (the supplement's value, MCL's default).
#   run_mcl.sh DATA_DIR OUT_DIR [MCL_BINARY]
# MCL 14-137 (micans.org; Ubuntu package `mcl`, bioconda `mcl=14.137`). Its clusters give the
# authors' MCL scores on every candidate pair of both networks (README).
set -euo pipefail
data=$1; out=$2; mcl=${3:-mcl}
mkdir -p "$out"
for net in HPRD OPHID; do
  "$mcl" "$data/$net.net" --abc -I 2.0 -o "$out/mcl_${net}_I2.0.txt" 2> "$out/mcl_${net}.log"
done
"$mcl" --version | head -1 > "$out/mcl_version.txt"

#!/usr/bin/env bash
# Run Weka 3.4's ADTree as PROSPECTR's download page describes (-B 15 -E -1), on the archived sets
# and on the same sets restricted to Table 1's features, through WekaRun.java.
#
#   run_weka.sh DOWNLOADS T1DIR OUTDIR [ZIP]
#
# T1DIR '-' skips the Table 1 feature set.
# ZIP defaults to DOWNLOADS/weka-3-4-3.zip. Needs a JDK (javac and java, 8 or later).
set -euo pipefail
dl=$1; t1=$2; out=$3; zip=${4:-$1/weka-3-4-3.zip}
here=$(cd "$(dirname "$0")" && pwd)
work=$(mktemp -d)
unzip -q -j -o "$zip" '*/weka.jar' -d "$work"
javac -nowarn --release 8 -cp "$work/weka.jar" -d "$work" "$here/WekaRun.java" 2>&1 | grep -v -E '^Note:|warning' || true
cp=$work/weka.jar:$work
mkdir -p "$out"
java -cp "$cp" WekaRun "$out/main" 15 -1 all "$dl/omim_trainingset.arff" hgmd="$dl/hgmd_testset.arff" pocus="$dl/pocus_testset.arff"
if [ "$t1" != "-" ]; then
  java -cp "$cp" WekaRun "$out/table1" 15 -1 all "$t1/table1_training.arff" hgmd="$t1/table1_hgmd.arff" pocus="$t1/table1_pocus.arff"
fi
rm -rf "$work"

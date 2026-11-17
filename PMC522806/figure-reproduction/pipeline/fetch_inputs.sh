#!/usr/bin/env bash
# Download the inputs of the PMC522806 reproduction and check their SHA-256.
#   fetch_inputs.sh OUTDIR [--sources DIR]
# --sources DIR: copy a file from DIR when it is there instead of downloading it (the local cache
# PMC522806/sources/data).
#
# Inputs (none is committed to the repository): the seven Kent Ridge datasets in the paper's
# "transformed" format, as Elvira .dbc files zipped on the University of Granada mirror of the
# Kent Ridge Bio-medical Data Set Repository (the paper's sdmc.lit.org.sg site is gone). The mirror
# is the only live copy we found; it accepts scripted downloads. There is no fallback mirror: the
# Wayback Machine (original site captured 2005-11-27) could not be reached from the build session.
set -euo pipefail
out="$1"; shift
src=""
while [ $# -gt 0 ]; do
  case "$1" in
    --sources) src="$2"; shift 2 ;;
    *) echo "unknown option $1" >&2; exit 2 ;;
  esac
done
mkdir -p "$out"
fetch() {  # name sha256 url
  local name="$1" sum="$2" url="$3"
  if [ -n "$src" ] && [ -f "$src/$name" ]; then
    cp "$src/$name" "$out/$name"
  else
    curl -fsSL --retry 3 --retry-delay 5 -o "$out/$name" "$url"
  fi
  echo "$sum  $out/$name" | sha256sum -c --quiet -
  (cd "$out" && unzip -o -q "$name")
}
u=https://leo.ugr.es/elvira/DBCRepository
fetch ALL-AML_Leukemia.zip 131220829fc5504980de674360bbbc8190b2fe45cc2727eebf8aca09958c81e0 $u/Leukemia/ALL-AML_Leukemia.zip
fetch LungCancer-Harvard2.zip 0ad87b5d133d72be6615f20b434ebd8d5a8c4534ecf01bd36b03e921be98e257 $u/LungCancer/LungCancer-Harvard2.zip
fetch ProstateCancer.zip 73073ff3260a02e785704479efc5d02d24efdb67c641b62cd3ddda332d097594 $u/ProstateCancer/ProstateCancer.zip
fetch DLBCL-Stanford.zip 50f0f317bd24a909123002b9dd6473287ab6f917a1e59b19d578d4ae0943f182 $u/DLBCL/DLBCL-Stanford.zip
fetch Ovarian-PBSII-061902.zip f74a7a64e7ecbe279762d9ed4b9941d332253606b1776ec10a48f3ca1f46e452 $u/OvarianCancer/Ovarian-PBSII-061902.zip
fetch ColonTumor.zip 0f9dd5d50804d472c8f894343d9b77f7a0c7e3e198e0f30c341dc6170a4f1efa $u/ColonTumor/ColonTumor.zip
fetch MLL_Leukemia.zip b8d380aa2a8d4c19580545ff5345b64cef4cfb6d3ee76760136b13e2d75a782f $u/Leukemia/MLL_Leukemia.zip
rm -f "$out"/*.x "$out"/*_Total.dbc "$out"/prostate_outcome.dbc
echo "inputs ok"

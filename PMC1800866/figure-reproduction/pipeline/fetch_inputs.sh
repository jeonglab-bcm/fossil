#!/usr/bin/env bash
# Download the inputs of the reproduction and check their SHA-256.
#
#   fetch_inputs.sh DIR [SOURCES_DIR] [--full]
#
# Default: the paper's open-access files (PDF, Additional files 1 and 3, the nine figures) from the
# PMC open-access bucket on AWS, with Europe PMC as the fallback. SOURCES_DIR reuses local copies.
# --full also fetches what the slow steps need: the RefSeq Build 35.1 human proteome (NCBI) and
# the mmCIF files of the 2,314 PDB entries of Additional file 1 (about 1 GB). The PSI-BLAST
# database (UniRef100 release 2010_01, 5.7 GB) is fetched by run_profiles.sbatch, not here.
set -euo pipefail
dir=$1; shift
src=""; full=0
for a in "$@"; do
  case "$a" in
    --full) full=1 ;;
    "") ;;
    *) src=$a ;;
  esac
done
here=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$dir"
PMC=https://pmc-oa-opendata.s3.amazonaws.com/PMC1800866.1
EPMC=https://europepmc.org/articles/PMC1800866/bin
files="PMC1800866.1.pdf 1471-2105-8-39-S1.tgz 1471-2105-8-39-S3.TXT"
for i in 1 2 3 4 5 6 7 8 9; do files="$files 1471-2105-8-39-$i.jpg"; done
get() {  # name url [fallback]
  local f=$dir/$1
  if [ -n "$src" ] && [ -s "$src/$1" ]; then cp "$src/$1" "$f"; return; fi
  curl -sfL --retry 3 -o "$f" "$2" || { [ -n "${3:-}" ] && curl -sfL --retry 3 -o "$f" "$3"; }
}
for f in $files; do get "$f" "$PMC/$f" "$EPMC/$f"; done
# Two structures released after the paper (Figs 8 and 9 checks). Not checksummed: RCSB may remediate them.
for e in 5zlq 2hd5; do get "$e.cif.gz" "https://files.rcsb.org/download/$e.cif.gz" "https://files.wwpdb.org/pub/pdb/data/structures/divided/mmCIF/${e:1:2}/$e.cif.gz"; done
if [ "$full" = 1 ]; then
  get protein.fa.gz https://ftp.ncbi.nlm.nih.gov/genomes/archive/old_refseq/Homo_sapiens/ARCHIVE/BUILD.35.1/protein/protein.fa.gz
fi
( cd "$dir" && grep -F -f <(ls) "$here/params/SHA256SUMS" | sha256sum -c --quiet )
mkdir -p "$dir/s1" && tar xzf "$dir/1471-2105-8-39-S1.tgz" -C "$dir/s1"
if [ "$full" = 1 ]; then
  awk '{print substr($2,1,4)}' "$dir"/s1/SVM_evaluation_data/C*_* | sort -u > "$dir/pdb_ids.txt"
  if [ -n "$src" ] && [ -d "$src/cif" ]; then cp -r "$src/cif" "$dir/cif"; fi
  bash "$here/fetch_structures.sh" "$dir/pdb_ids.txt" "$dir/cif"
fi
echo "inputs in $dir"

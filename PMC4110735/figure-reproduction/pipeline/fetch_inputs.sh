#!/usr/bin/env bash
# Download every input of the PMC4110735 reproduction into DIR, check SHA-256, unpack.
# Usage: fetch_inputs.sh DIR [--sources LOCALDIR] [--go]
#   --sources: copy files from LOCALDIR (same file names) instead of downloading, when present there.
#   --go: also fetch the Gene Ontology and the annotation files used for Tables 4 and 5 (about 50 MB).
set -euo pipefail
DIR=${1:?usage: fetch_inputs.sh DIR [--sources LOCALDIR] [--go]}
shift
SRC=""; GO=0
while [ $# -gt 0 ]; do
  case "$1" in
    --sources) SRC=$2; shift 2;;
    --go) GO=1; shift;;
    *) echo "unknown option $1" >&2; exit 2;;
  esac
done
mkdir -p "$DIR"
GNW=https://raw.githubusercontent.com/tschaffter/genenetweaver/c5310349f5d5723306585c2bb62aedbdeb70db46
GOR=https://release.geneontology.org/2026-08-05
# name  sha256  url  [fallback url]
FILES=(
"gnw-networks.jar 1bb1128431fca714504c956c54e8a77ddc08b8d205be1f8f63b9ae0782bcc5ac $GNW/lib/gnw-networks.jar"
"DREAM4_1.30.0.tar.gz 3b10c742e0be65c47e1c9242e8b81ebbefdb9ff8025fcb7961870c4524b2203f https://bioconductor.org/packages/3.14/data/experiment/src/contrib/DREAM4_1.30.0.tar.gz https://mghp.osn.xsede.org/bir190004-bucket01/archive.bioconductor.org/packages/3.14/data/experiment/src/contrib/DREAM4_1.30.0.tar.gz"
"yeast.matrix 8be03510d772f20d97c81b973e11314a3637de43dd56f4ad945c1464aaeb9b75 http://arep.med.harvard.edu/biclustering/yeast.matrix"
"yeast.genes 20bac410511fd295771a6b074706f1532d04f14e7361c7060f8b535c9d10e379 http://arep.med.harvard.edu/biclustering/yeast.genes"
"GDS3702.soft.gz 5c8fb62f79323cec7dbbff8ee3e041f1e28691450ab237a0905cd1bb8b4e6a43 https://ftp.ncbi.nlm.nih.gov/geo/datasets/GDS3nnn/GDS3702/soft/GDS3702.soft.gz"
"GDS958.soft.gz ac9b144dc9d5451630445e6cf670299b8a2be8b0aeda9310027b6e309c8aa56f https://ftp.ncbi.nlm.nih.gov/geo/datasets/GDSnnn/GDS958/soft/GDS958.soft.gz"
"GDS825.soft.gz 85b2e98ad94e9bf17f0d9921b8eb33827655cf8673b69979c2d7b67ee4f0b440 https://ftp.ncbi.nlm.nih.gov/geo/datasets/GDSnnn/GDS825/soft/GDS825.soft.gz"
"logcho_237_4class.txt 2e753b4936f1519e15b22c4b5b3d550092237fe7af2b76020072e69194278e2e http://faculty.washington.edu/kayee/cluster/logcho_237_4class.txt"
"normcho_237_4class.txt e543549032acd08203b56037d5b870ee6cf5f3ffc2e4789375cacddb9b641501 http://faculty.washington.edu/kayee/cluster/normcho_237_4class.txt"
"log_cellcycle_384_17.txt da0776b93460c1dedd8956bc3fd95cc258327ed5478422ef59a37e13aa4d7de7 http://faculty.washington.edu/kayee/cluster/log_cellcycle_384_17.txt"
)
if [ $GO = 1 ]; then
FILES+=(
"go-basic.obo b08d45b268b8c24ccb2513dbbbc7d4df9f6521c099b413f79eb31e06e0fa3bcc $GOR/ontology/go-basic.obo"
"YEAST-mod.gaf.gz bea6d4453bb47db293d9103b73866801fe8e341975e5f8b5f3ca42053098d089 $GOR/annotations/gaf/YEAST-mod.gaf.gz"
"RAT-mod.gaf.gz c34076e471912d3e00b2fc6ae4959d51d23d2d31de7dab35fcaa38955c8fa612 $GOR/annotations/gaf/RAT-mod.gaf.gz"
"MOUSE-mod.gaf.gz 6cbefce3a2efd9862f102a2732e923fde525c8fa59a3e5ce22e8178c3ebb0093 $GOR/annotations/gaf/MOUSE-mod.gaf.gz"
)
fi
for entry in "${FILES[@]}"; do
  set -- $entry
  name=$1; sha=$2; shift 2
  out="$DIR/$name"
  if [ -n "$SRC" ] && [ -f "$SRC/$name" ]; then
    cp "$SRC/$name" "$out"
  else
    ok=0
    for url in "$@"; do
      if curl -fsSL --retry 3 --retry-delay 5 -o "$out" "$url"; then ok=1; break; fi
      echo "download failed: $url" >&2
    done
    [ $ok = 1 ] || { echo "could not download $name" >&2; exit 1; }
  fi
  got=$(sha256sum "$out" | cut -d' ' -f1)
  if [ "$got" != "$sha" ]; then echo "SHA-256 mismatch for $name: $got" >&2; exit 1; fi
  echo "ok $name"
done
# unpack: DREAM3 and DREAM4 network files from GNW, DREAM4 released data
mkdir -p "$DIR/dream3net" "$DIR/dream4net" "$DIR/dream4_raw"
unzip -q -o -j "$DIR/gnw-networks.jar" 'ch/epfl/lis/networks/dream3/InSilico*.xml' -d "$DIR/dream3net"
unzip -q -o -j "$DIR/gnw-networks.jar" 'ch/epfl/lis/networks/dream4/insilico*.xml' -d "$DIR/dream4net"
tmp=$(mktemp -d)
tar xzf "$DIR/DREAM4_1.30.0.tar.gz" -C "$tmp" DREAM4/inst/extdata/lightlyProcessedDownloadedData.tar.gz
tar xzf "$tmp/DREAM4/inst/extdata/lightlyProcessedDownloadedData.tar.gz" -C "$tmp"
cp -r "$tmp"/lightlyProcessedDownloadedData/insilico_size* "$DIR/dream4_raw/"
find "$DIR/dream4_raw" -name '._*' -delete
rm -rf "$tmp"
echo "inputs ready in $DIR"

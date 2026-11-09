#!/bin/bash
# Download the inputs of the PMC2711306 reproduction and check their SHA-256.
#
# Usage: fetch_inputs.sh OUT_DIR MODE [SOURCES_DIR]
#   MODE light: BioGRID 2.0.35 and the paper's supplement (Tables S1-S7), enough to rebuild
#               HumanBG and to check the committed networks (the pull-request run).
#   MODE full:  also Collins et al.'s PE scores (Wayback Machine copy of interactome-cmp.ucsf.edu),
#               BioGRID 2.0.50, GOA human release 70, HPRD release 9 (Pathway Commons 2), the
#               current KEGG REST lists and the authors' Matlab code (Wayback Machine copy of
#               kuchaev.com/Denoising).
#   SOURCES_DIR: a folder with local copies (same file names) to use instead of downloading.
set -euo pipefail
out=$1; mode=${2:-light}; src=${3:-}
mkdir -p "$out"

fetch() {  # name sha256 url [url ...]
  local name=$1 sum=$2; shift 2
  if [ -n "$src" ] && [ -f "$src/$name" ]; then
    cp "$src/$name" "$out/$name"
  else
    local ok=0
    for url in "$@"; do
      for attempt in 1 2 3 4 5; do
        if curl -sfL --retry 3 -m 900 -A "fossil-reproduction (curl)" -o "$out/$name.part" "$url" \
           && ! head -c 2000 "$out/$name.part" | grep -qi "<html"; then
          mv "$out/$name.part" "$out/$name"; ok=1; break 2
        fi
        sleep $((attempt * 20))
      done
    done
    [ $ok = 1 ] || { echo "download failed: $name" >&2; exit 1; }
  fi
  if [ "$sum" != "-" ]; then
    echo "$sum  $out/$name" | sha256sum -c --quiet - || { echo "checksum mismatch: $name" >&2; exit 1; }
  fi
}

BG=https://downloads.thebiogrid.org/Download/BioGRID/Release-Archive
PMC=https://pmc-oa-opendata.s3.amazonaws.com/PMC2711306.1
WB=http://web.archive.org/web

fetch BIOGRID-ORGANISM-2.0.35.tab.zip 995f392992f871104e03a94ebe4c6b3f480363e02e9086ccf707ea757866e96e \
  $BG/BIOGRID-2.0.35/BIOGRID-ORGANISM-2.0.35.tab.zip
declare -A S=(
  [s002]=31052eb9889e1c8dcfacea1b09c552bb11e43c13a68e97298638316ad791a4a5
  [s003]=e5b74a7e02e6976af0a3a25b751cf0f98eb6ae84d2c7355e4845ecf9151c1712
  [s004]=072346a4e1ea5daf0eafd87e89fa1e2774f5367f995d048bd1007f983b9ee64f
  [s005]=7d940799e11c2cb338dfeb4c14bc72ce431aa30d3240f806fccd76d3b540185a
  [s006]=5f65a5926a005a1baeeb393af4986fc900a438b11a4aeef679befb996c2faa0d
  [s007]=b536286d2fcde016130c1c61a5ca9f43e855be48bf8ad5b97fcefc59d6c57245
  [s008]=3fb43756901c1d35a72bf892eee808b98d85e01c520dbc5ad6243b19ca56eded
)
for k in "${!S[@]}"; do
  fetch pcbi.1000454.$k.doc "${S[$k]}" "$PMC/pcbi.1000454.$k.doc" \
    "https://journals.plos.org/ploscompbiol/article/file?type=supplementary&id=10.1371/journal.pcbi.1000454.$k"
done
(cd "$out" && unzip -oqj BIOGRID-ORGANISM-2.0.35.tab.zip \
  "textfiles/BIOGRID-ORGANISM-Homo_sapiens-2.0.35.tab.txt" \
  "textfiles/BIOGRID-ORGANISM-Saccharomyces_cerevisiae-2.0.35.tab.txt")

if [ "$mode" = full ]; then
  fetch combined_scores.txt d030d4aab423013922dd27b2209b3d662e5220b425e742d38fe3c084f9a15ca5 \
    "$WB/20100715141255id_/http://interactome-cmp.ucsf.edu/scores/combined_scores.txt"
  fetch BIOGRID-ORGANISM-2.0.50.tab.zip 9ecdfdb67dc65dafdac19eb10e2fddb3fb45bf8f79921c3fd5d5c1a7235416b9 \
    $BG/BIOGRID-2.0.50/BIOGRID-ORGANISM-2.0.50.tab.zip
  (cd "$out" && unzip -oqj BIOGRID-ORGANISM-2.0.50.tab.zip "*Homo_sapiens-2.0.50.tab.txt")
  fetch gene_association.goa_human.70.gz f1528aa006515c83078bad18518b5a29deabefb952f4c56113e74cb37c1442c6 \
    https://ftp.ebi.ac.uk/pub/databases/GO/goa/old/HUMAN/gene_association.goa_human.70.gz
  fetch pc2_v3_hsa_extended_sif.tsv.gz 7435ad230b5ddf09517cbc5b5a50339e373054928f8fef2917a383f1b8aa18da \
    "https://download.baderlab.org/PathwayCommons/PC2/v3/Pathway%20Commons%202%20homo%20sapiens.EXTENDED_BINARY_SIF.tsv.gz"
  # KEGG changes with every release: no fixed checksum; the run records what it read
  fetch link_pathway_hsa.tsv - https://rest.kegg.jp/link/pathway/hsa
  fetch list_hsa.tsv - https://rest.kegg.jp/list/hsa
  fetch denoising.zip 8ce983d3ea7c67be5ed08e21bbf762504653c8b8c8d945c4d1d87c21e86548cc \
    "$WB/20160606195006id_/http://kuchaev.com/Denoising/denoising.zip"
  (cd "$out" && mkdir -p authors && unzip -oq denoising.zip -d authors)
fi
(cd "$out" && sha256sum -- * 2>/dev/null | grep -v "^.* authors$" > SHA256SUMS.txt || true)
echo "inputs ready in $out ($mode)"

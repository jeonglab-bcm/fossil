#!/usr/bin/env bash
# Download the inputs of the PMC2661051 reproduction and check their SHA-256.
#
#   fetch_inputs.sh DIR [--sources LOCALDIR] [--unigene]
#
# --sources LOCALDIR: copy files from LOCALDIR when they are there (same names), download the rest.
# --unigene: also download NCBI UniGene build 236 (Hs.data.gz, 156 MB) and rebuild the clone-to-
#   symbol map of the Hedenfalk clones; it must equal the committed inputs/hedenfalk_image2unigene.tsv.
#
# The simulation study (Tables 2-6) needs no input. p53 (Figs 2, 3): the GSEA datasets of
# Subramanian et al. (2005), which the Broad serves only after a login; we take them from two
# public GitHub mirrors with identical files. Hedenfalk (Fig. 4, Table 7): strimmerlab.github.io.
set -euo pipefail
dir=$1; shift
src=""; unigene=0
while [ $# -gt 0 ]; do
  case $1 in
    --sources) src=$2; shift 2 ;;
    --unigene) unigene=1; shift ;;
    *) echo "unknown option $1" >&2; exit 2 ;;
  esac
done
mkdir -p "$dir"
here=$(cd "$(dirname "$0")" && pwd)

fetch() {  # fetch NAME SHA256 URL [FALLBACK_URL]
  local name=$1 sha=$2 url=$3 alt=${4:-}
  if [ -n "$src" ] && [ -f "$src/$name" ]; then
    cp "$src/$name" "$dir/$name"
  else
    curl -fsSL --retry 3 -o "$dir/$name" "$url" || { [ -n "$alt" ] && curl -fsSL --retry 3 -o "$dir/$name" "$alt"; }
  fi
  echo "$sha  $dir/$name" | sha256sum -c --quiet - || { echo "checksum mismatch: $name" >&2; exit 1; }
}

ash=https://raw.githubusercontent.com/stephens999/ash-orig/master/data/GSEA
joker=https://raw.githubusercontent.com/jokergoo/GSEA_book/master/data
fetch P53_collapsed_symbols.gct d80112a099874e3069af37bd954c3c49728c75d886956790abb47fd15dd0b5da \
  $ash/p53/P53_collapsed_symbols.gct $joker/P53_collapsed_symbols.gct
fetch P53.cls 6c882c4fa660eb341ca5ff0d0f45adc2f08c7b3d4e18ffeb7f7f8019f8301975 \
  $ash/p53/P53.cls $joker/P53.cls
fetch P53_hgu95av2.gct e75f251c0df052c182481da6ba5402a3b04fb3dad06b4de2dce6b7997806c774 \
  $ash/p53/P53_hgu95av2.gct
fetch c2.symbols.gmt 4c5e98ac7f97aaab810b47c0e4a41dd7fa6b825535d5859bc219443903515fc7 \
  $ash/c2.symbols.gmt $joker/c2.symbols.gmt
fetch hedenfalk.rda.gz ee75570b7743185672fb2675e642968a4e5529da1d589c8f0960a06d5fe631c6 \
  https://strimmerlab.github.io/data/hedenfalk.rda.gz

# IMAGE clone -> UniGene cluster -> gene symbol for the Hedenfalk clones, from UniGene build 236
# (NCBI, public domain). Committed because the source is 156 MB; --unigene rebuilds and checks it.
map=$here/../inputs/hedenfalk_image2unigene.tsv
echo "1bb615db49634a6b6af3d4a4c68a6f7662ef40ae98ceb7febdcc8879267e8a3b  $map" | sha256sum -c --quiet - \
  || { echo "checksum mismatch: inputs/hedenfalk_image2unigene.tsv" >&2; exit 1; }
cp "$map" "$dir/hedenfalk_image2unigene.tsv"
if [ $unigene = 1 ]; then
  fetch Hs.data.gz 710031fa860bfc74498c96fa1b6c155e2f178d654b387543703c7335f1b5931d \
    https://ftp.ncbi.nih.gov/repository/UniGene/Homo_sapiens/Hs.data.gz
  Rscript -e 'load(gzcon(gzfile(commandArgs(TRUE)[1]))); writeLines(unique(as.character(hedenfalk.imagecloneid)), commandArgs(TRUE)[2])' \
    "$dir/hedenfalk.rda.gz" "$dir/clones.txt"
  zcat "$dir/Hs.data.gz" | awk '/^ID /{id=$2; g=""} /^GENE /{g=$2} /^SEQUENCE/ && /CLONE=IMAGE:/{match($0,/CLONE=IMAGE:[0-9]+/); print substr($0,RSTART+12,RLENGTH-12)"\t"id"\t"g}' \
    | awk -F'\t' 'NR==FNR{c[$1]=1;next} ($1 in c)' "$dir/clones.txt" - | sort -u > "$dir/rebuilt_map.tsv"
  cmp "$dir/rebuilt_map.tsv" <(sort -u "$map") || { echo "rebuilt UniGene map differs from the committed one" >&2; exit 1; }
  echo "UniGene map rebuilt and equal to the committed one"
fi
echo "inputs ok"

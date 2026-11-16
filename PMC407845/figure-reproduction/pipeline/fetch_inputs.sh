#!/usr/bin/env bash
# Download the inputs of the PMC407845 reproduction and check their SHA-256.
#   fetch_inputs.sh OUTDIR [--sources DIR]
# --sources DIR: copy a file from DIR (or DIR/sgd for the expression archives) when it is there,
# instead of downloading it (the local cache PMC407845/sources/).
#
# Inputs (none is committed to the repository):
#   binding_by_gene.tsv   Lee et al. 2002 ChIP-chip, 113 TFs (Young lab).
#   simon_all_genes.tsv   Simon et al. 2001 ChIP-chip, 9 cell cycle TFs (Young lab).
#   <Author_Year>.zip     the expression compendium: 15 SGD expression archives (2010 reprocessing).
#   sgd.gaf.gz, gene_ontology.obo   Gene Ontology release 2004-03-01 (the earliest archived).
#   S288C R64-1-1 genome  sequence and GFF, for the 600 bp upstream regions of Table 3.
#   moesm2.eps            the paper's Fig. 2 as vector PostScript (BMC "original file"), for its
#                         bar heights.
# Fallbacks: SGD files from downloads.yeastgenome.org when the S3 archive fails; GO files from
# release.geneontology.org when the S3 bucket fails. The Young lab files have no mirror.
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
fetch() {  # name sha256 url [fallback-url]
  local name="$1" sum="$2" url="$3" fb="${4:-}"
  if [ -n "$src" ] && [ -f "$src/$name" ]; then
    cp "$src/$name" "$out/$name"
  elif [ -n "$src" ] && [ -f "$src/sgd/$name" ]; then
    cp "$src/sgd/$name" "$out/$name"
  elif ! curl -fsSL --retry 3 -o "$out/$name" "$url"; then
    if [ -n "$fb" ]; then echo "download failed, trying $fb" >&2; curl -fsSL --retry 3 -o "$out/$name" "$fb"; else exit 1; fi
  fi
  echo "$sum  $out/$name" | sha256sum -c --quiet -
}

fetch binding_by_gene.tsv d4db1099eaebe420b669a494ccfc4e9c497dd8b4c5b71b67631308c7540f1ef5 \
  http://younglab.wi.mit.edu/regulatory_network/binding_by_gene.tsv
fetch simon_all_genes.tsv a085b5804f946726fd35cb02af89926282d024d9d3710948aaa678da798df420 \
  http://younglab.wi.mit.edu/cellcycle/all_genes.tsv

sgd=https://s3-us-west-2.amazonaws.com/sgd-archive.yeastgenome.org
sgd2=https://downloads.yeastgenome.org
while read -r name sum; do
  fetch "$name.zip" "$sum" "$sgd/expression/microarray/$name/$name.zip" "$sgd2/expression/microarray/$name/$name.zip"
done <<'EOF'
Chu_1998_PMID_9784122 f6d0013b1a3f3ac183adeb555a602384e84b14b1057f59772586965a7f880b5f
DeRisi_1997_PMID_9381177 2114cc733949bef6e72d37ef78fabbb421e8d78db451da063c600ecf33aa5487
Gasch_2000_PMID_11102521 31f41d08b1f7e2bcded2933518eb99809b39c2a1a34f8c9e9b56f6b61ee8d5ab
Gasch_2001_PMID_11598186 d4e4e730d7854f9c0361fc38ae17c790b305b792321461eac449c2f69387ce47
Gross_2000_PMID_10922376 ef5119d94c6b6edb960a68049ab2974183d17caf075a474f5d59fc18b0f14de6
Hughes_2000_PMID_10929718 27e6723b54c84c7f58e77f0de2d6b73d35dca349fecb28cec3167613e57cbc99
Keller_2001_PMID_11504737 2dee8957cfaf80a1e6c714e330a72ebfaea9c3dce30326ca10472c5c5620d17a
Kuhn_2001_PMID_11154278 c2316f6c7ffc57e8d6dc1781d2c99b6997d2d8db7d833ab8ea820b27313975da
Ogawa_2000_PMID_11102525 7229e301e24a004cbd7cbab98befab6788f8186659b68c9734c9e1478ce67283
Protchenko_2001_PMID_11673473 a4a2a2476b0fc413acf5368bba69bb70fe53e379de670a1dcfedab81fc46ed34
Roberts_2000_PMID_10657304 d2abdf3aef836d2f82d49d71a751938ad434ffbbd660d9b2f547d476b6589b8f
Spellman_1998_PMID_9843569 7b46af23498289f2b9a9afeac0c5ec04d73d50ad1953bd5c5c585c6f09ca3687
Sudarsanam_2000_PMID_10725359 d61fd826859f88abe91ea93ba0b8de09f3405bf8aac92f525a3c037db96f0260
Yoshimoto_2002_PMID_12058033 5b76d08f37817c1c7e7f0e92c3f91e4452b9ec8a1631b5b773aff7929899eef0
Yun_2000_PMID_10744769 90c8f904c5d365cae0b5930a75ce52f4a858d667435b127a36d02341a0ba7962
Zhu_2000_PMID_10894548 913e7eba963b6a28728e7517cd72f623f2823e497a1d8def90e8764a32907d0b
EOF

go=https://s3.amazonaws.com/go-data-product-release/2004-03-01
go2=https://release.geneontology.org/2004-03-01
fetch sgd.gaf.gz c0384b66021680ceb5a0780e0b443a6321e9abf9de2fc56c391a62b493a2b40f "$go/annotations/sgd.gaf.gz" "$go2/annotations/sgd.gaf.gz"
fetch gene_ontology.obo d8b6b4a3a183e6aa16cb933a7f681d99b6f5e26c40c2e9815772e86516a1e885 "$go/ontology/gene_ontology.obo" "$go2/ontology/gene_ontology.obo"

g=S288C_reference_genome_R64-1-1_20110203.tgz
fetch "$g" 34202715e816ea8a4d44eb22d24f9627b636f0a8867f1300cdab220cde1bb515 \
  "$sgd/sequence/S288C_reference/genome_releases/$g" "$sgd2/sequence/S288C_reference/genome_releases/$g"

fetch moesm2.eps bd3c5172bb56c2fdf255a3b2e6bf088c44f9d38b04863b921a19bbe741aa18ba \
  "https://static-content.springer.com/esm/art%3A10.1186%2F1471-2105-5-31/MediaObjects/12859_2003_147_MOESM2_ESM.eps"
echo "inputs ok"

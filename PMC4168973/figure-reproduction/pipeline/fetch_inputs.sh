#!/usr/bin/env bash
# Download every input of the PMC4168973 reproduction and check its SHA-256.
#   fetch_inputs.sh DIR [--sources LOCAL_DIR]
# With --sources, files already in LOCAL_DIR (same names) are copied instead of downloaded.
set -euo pipefail
out=${1:?usage: fetch_inputs.sh DIR [--sources LOCAL_DIR]}
src=""
if [ "${2:-}" = "--sources" ]; then src=${3:?}; fi
mkdir -p "$out"
GEO=https://ftp.ncbi.nlm.nih.gov/geo
MSIG=https://data.broadinstitute.org/gsea-msigdb/msigdb/release/6.0
BIOC=https://bioconductor.org/packages/3.18/data/experiment/src/contrib
# name  sha256  url  [fallback url]
while read -r name sha url alt; do
  [ -z "$name" ] && continue
  if [ -n "$src" ] && [ -f "$src/$name" ]; then
    cp "$src/$name" "$out/$name"
  else
    curl -fsSL --retry 3 -o "$out/$name" "$url" || { [ -n "${alt:-}" ] && curl -fsSL --retry 3 -o "$out/$name" "$alt"; }
  fi
  echo "$sha  $out/$name" | sha256sum -c --quiet -
done <<LIST
GSE3494-GPL96_series_matrix.txt.gz 2cbfc355e7bd4c9d3f0dfb7c1212ac98c473ca19ba505bde299b3e5a7442fcae $GEO/series/GSE3nnn/GSE3494/matrix/GSE3494-GPL96_series_matrix.txt.gz
GSE1456-GPL96_series_matrix.txt.gz 294f51ed7dc83c9fe3525ea188e86fb68447aa0a866a061aa216b55077793b8d $GEO/series/GSE1nnn/GSE1456/matrix/GSE1456-GPL96_series_matrix.txt.gz
GSE4922-GPL96_series_matrix.txt.gz 126cc8f3411413afc5ab6264a585c0508a29d49d61a6996f078242dc8339e95c $GEO/series/GSE4nnn/GSE4922/matrix/GSE4922-GPL96_series_matrix.txt.gz
GSE4922_Clinical_file_for_both_Uppsala_Singapore_Samples.txt f936e89eb46480ea6313f50da70db4200baf302afa77afc265233d60d052fc1f $GEO/series/GSE4nnn/GSE4922/suppl/GSE4922_Clinical_file_for_both_Uppsala_Singapore_Samples.txt
GSE7390_series_matrix.txt.gz 950cde4ba15f919d11cd446657798600776b1f9c84db180ff8e7c1af727780cc $GEO/series/GSE7nnn/GSE7390/matrix/GSE7390_series_matrix.txt.gz
GPL96.annot.gz 88e0b22362bac779eb220b3b185c80faa6510a92b9358eaad159a561ab4351c4 $GEO/platforms/GPLnnn/GPL96/annot/GPL96.annot.gz
c2.cp.biocarta.v6.0.symbols.gmt 2909f3a06d4c25522d442f49af29fcb30385ed661ac19a6bff774d3462cd1e4d $MSIG/c2.cp.biocarta.v6.0.symbols.gmt https://data.broadinstitute.org/gsea-msigdb/msigdb/release/6.2/c2.cp.biocarta.v6.2.symbols.gmt
c2.cp.kegg.v6.0.symbols.gmt 1f67666e72756d9d25671dbb94478791e57b289e79fed5d707dee06c08f06e0e $MSIG/c2.cp.kegg.v6.0.symbols.gmt https://data.broadinstitute.org/gsea-msigdb/msigdb/release/6.2/c2.cp.kegg.v6.2.symbols.gmt
breastCancerUPP_1.40.0.tar.gz d75880feff1c0a8c10ff9c24179229ae18144d074c044a58edd9bbd3176e2956 $BIOC/breastCancerUPP_1.40.0.tar.gz https://bioconductor.org/packages/3.18/data/experiment/src/contrib/Archive/breastCancerUPP/breastCancerUPP_1.40.0.tar.gz
genefu_2.34.0.tar.gz bb55478c0af19fc6ec9cd750423e94e63a9a6ec56c0ce838ef9784632ce2d663 https://bioconductor.org/packages/3.18/bioc/src/contrib/genefu_2.34.0.tar.gz https://bioconductor.org/packages/3.18/bioc/src/contrib/Archive/genefu/genefu_2.34.0.tar.gz
LIST
tar -xzf "$out/genefu_2.34.0.tar.gz" -C "$out" genefu/data/sig.gene70.rda genefu/data/pam50.rda
tar -xzf "$out/breastCancerUPP_1.40.0.tar.gz" -C "$out" breastCancerUPP/data/upp.rda
echo "inputs ok"

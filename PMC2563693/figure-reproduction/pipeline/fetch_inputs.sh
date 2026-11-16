#!/usr/bin/env bash
# Download every input of the PMC2563693 reproduction and check its SHA-256.
#
#   fetch_inputs.sh OUTDIR [--sources DIR]
#
# --sources DIR: copy files already downloaded into DIR (same layout) instead of downloading them;
# their checksums are still checked. Each file has a fallback URL where one exists.
#
# OUTDIR/gsea   MSigDB v1.0 C2 and the two lung datasets of Subramanian et al. 2005 (Broad GSEA site)
# OUTDIR/geo    GEO series matrices: GSE2034 (Breast USA), GSE2624 (NF-kB), GSE3933 (Prostate),
#               and GSE2034's MINiML archive for its clinical table (relapse status)
# OUTDIR/bioc   Bioconductor data packages: seventyGeneData (Breast Netherlands, van de Vijver 295)
#               and stjudem (Leukemia, Yeoh et al. 2002; removed after Bioconductor 3.17)
# OUTDIR/paper/supp  the paper's vector supplementary figures S1-S5 (PLOS)
set -euo pipefail

out="$1"; shift || true
sources=""
while [ $# -gt 0 ]; do
  case "$1" in
    --sources) sources="$2"; shift 2 ;;
    *) echo "unknown option $1" >&2; exit 2 ;;
  esac
done

GSEA=https://data.broadinstitute.org/gsea-msigdb/gsea/dataset_files
GEO=https://ftp.ncbi.nlm.nih.gov/geo/series
PLOS="https://journals.plos.org/ploscompbiol/article/file?type=supplementary&id=10.1371/journal.pcbi.1000217"
EPMC="https://www.ebi.ac.uk/europepmc/webservices/rest/PMC2563693/supplementaryFiles"

# path  sha256  url  [fallback url]
FILES=$(cat <<EOF
gsea/c2.symbols.gmt 4c5e98ac7f97aaab810b47c0e4a41dd7fa6b825535d5859bc219443903515fc7 $GSEA/c2.symbols.gmt
gsea/Lung_Michigan_collapsed_symbols.gct 7a7cf6c0a0da19fb359dce6ae650f093219b61ad83123bf3a12610b7f320219e $GSEA/Lung_Michigan_collapsed_symbols.gct
gsea/Lung_Boston_collapsed_symbols.gct bbb2fce2be29918279109f00cb0757050c25baae4dfbe59731a831c2c1b85128 $GSEA/Lung_Boston_collapsed_symbols.gct
gsea/Lung_Michigan.cls bca4b1a0c96b4a7d55addf6cba7276d93f9da7408d480fa931a86698729c1699 $GSEA/Lung_Michigan.cls
gsea/Lung_Boston.cls aea796a4d52965ff2885dfee745608791155abe80ab4797f9db02ab0bb180f6f $GSEA/Lung_Boston.cls
geo/GSE2034_series_matrix.txt.gz f6a99c62f0a291858f14806ad7b5faf1da159f88630d11cfe994815ff3bf9ea3 $GEO/GSE2nnn/GSE2034/matrix/GSE2034_series_matrix.txt.gz
geo/GSE2034_family.xml.tgz e8d242a076f304a1de96b27506d30376431fa0f437b0c1426a30cd06c49f03c9 $GEO/GSE2nnn/GSE2034/miniml/GSE2034_family.xml.tgz
geo/GSE2624_series_matrix.txt.gz 1cc5a889e3217178d0c17417241e6af0e963f371a1e39fd27caa5fbff69b9bae $GEO/GSE2nnn/GSE2624/matrix/GSE2624_series_matrix.txt.gz
geo/GSE3933-GPL2695_series_matrix.txt.gz 8a04638ced62fdd754c1f54988ee420f2bc6d54120306fe75a9a866fe51edf37 $GEO/GSE3nnn/GSE3933/matrix/GSE3933-GPL2695_series_matrix.txt.gz
geo/GSE3933-GPL3044_series_matrix.txt.gz 5de01afabc140900f128ef83e509686af7732fc0de8bbd0786e1969cc3618d68 $GEO/GSE3nnn/GSE3933/matrix/GSE3933-GPL3044_series_matrix.txt.gz
geo/GSE3933-GPL3289_series_matrix.txt.gz 04e32e53927cb6a22f9277a7f6a6170948ab01fc70182bc123506066dd024c87 $GEO/GSE3nnn/GSE3933/matrix/GSE3933-GPL3289_series_matrix.txt.gz
bioc/seventyGeneData_1.48.0.tar.gz ff362d79e0f4a554c432889dd8dc9599873a517d7a864c6894ce884a711fd2eb https://bioconductor.org/packages/3.23/data/experiment/src/contrib/seventyGeneData_1.48.0.tar.gz https://bioconductor.org/packages/3.23/data/experiment/src/contrib/Archive/seventyGeneData/seventyGeneData_1.48.0.tar.gz
bioc/stjudem_1.40.0.tar.gz 34222e9590da29b5b0793933c620e33fb98ed4522b0ccb6b1cad7c715dba868d https://bioconductor.org/packages/3.17/data/experiment/src/contrib/stjudem_1.40.0.tar.gz
paper/supp/pcbi.1000217.s003.pdf a291c97606116eb878997198f6234fedb0db7ab68e69fc45ad8fc862b70f24c1 $PLOS.s003
paper/supp/pcbi.1000217.s004.pdf 17760b45c54f037b6c166d6798295a6eaf13ab31b57ebafe561ec3f0dfcdc928 $PLOS.s004
paper/supp/pcbi.1000217.s005.pdf 8d1105d2d2b31f435d97bf4f797b1689db28c1a2913776c425f2309de4ddd9e0 $PLOS.s005
paper/supp/pcbi.1000217.s006.pdf 84d950e74ad1bfad7b09e8c122bb24eccf6348df6eb9bd1e81cf5cc474f22769 $PLOS.s006
paper/supp/pcbi.1000217.s007.pdf b108eed5d97e5bbaeb93f0e81b88e2e8bdc3611c3d7ea0898128221460c03c7a $PLOS.s007
EOF
)

get() {  # url dest
  curl -sfL --retry 3 --retry-delay 5 -A "Mozilla/5.0 (fossil reproduction)" -o "$2" "$1"
}

mkdir -p "$out"
while read -r path sha url fallback; do
  [ -z "$path" ] && continue
  dest="$out/$path"
  mkdir -p "$(dirname "$dest")"
  if [ -n "$sources" ] && [ -f "$sources/$path" ]; then
    cp "$sources/$path" "$dest"
  else
    get "$url" "$dest" || { [ -n "${fallback:-}" ] && get "$fallback" "$dest"; } || {
      # the PLOS supplements are also in Europe PMC's supplementary-file archive
      if [[ "$path" == paper/supp/* ]]; then
        tmp=$(mktemp -d); get "$EPMC" "$tmp/supp.zip" && unzip -q -o "$tmp/supp.zip" "$(basename "$path")" -d "$(dirname "$dest")"
      else
        echo "download failed: $path" >&2; exit 1
      fi
    }
  fi
  got=$(sha256sum "$dest" | cut -d' ' -f1)
  if [ "$got" != "$sha" ]; then
    echo "checksum mismatch: $path ($got, expected $sha)" >&2; exit 1
  fi
done <<< "$FILES"

# Unpack what the pipeline reads.
tar -xzf "$out/geo/GSE2034_family.xml.tgz" -C "$out/geo" GSE2034-tbl-2.txt
mkdir -p "$out/geo/gse2034_miniml" && mv "$out/geo/GSE2034-tbl-2.txt" "$out/geo/gse2034_miniml/"
echo "20a5e688ee338434cd1f1c3363930b0f  $out/geo/gse2034_miniml/GSE2034-tbl-2.txt" | md5sum -c --quiet
for f in seventyGeneData_1.48.0 stjudem_1.40.0; do tar -xzf "$out/bioc/$f.tar.gz" -C "$out/bioc"; done
echo "inputs ready in $out"

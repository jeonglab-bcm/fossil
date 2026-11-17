#!/usr/bin/env bash
# Install the pinned R environment of the PMC4168973 reproduction on Ubuntu 24.04 (as root or with
# sudo): R 4.3.3 and the R packages from the Ubuntu archive at fixed versions, then pathifier
# 1.40.0 (Bioconductor 3.18) and penalized 0.9-53 (CRAN) from their source tarballs (SHA-256
# checked). The package pdscox itself is installed by the pipeline from PMC4168973/package.
set -euo pipefail
SUDO=""; [ "$(id -u)" = 0 ] || SUDO=sudo
$SUDO apt-get update -qq
$SUDO env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
  r-base-core=4.3.3-2build2 r-base-dev=4.3.3-2build2 \
  r-bioc-limma=3.58.1+dfsg-1 r-bioc-biobase=2.62.0-1 r-cran-survival=3.5-8-1 \
  r-cran-princurve=2.1.6-1 r-cran-r.oo=1.26.0-1 r-cran-rcpp=1.0.12-1 r-cran-rcpparmadillo=0.12.8.1.0-1build1 \
  r-cran-jsonlite=1.8.8+dfsg-1 r-cran-knitr=1.45+dfsg-1 r-cran-rmarkdown=2.25+dfsg-3 r-cran-testthat=3.2.1-1 \
  pandoc=3.1.3+ds-2
tmp=$(mktemp -d)
get() {  # name sha256 url [fallback]
  curl -fsSL --retry 3 -o "$tmp/$1" "$3" || curl -fsSL --retry 3 -o "$tmp/$1" "$4"
  echo "$2  $tmp/$1" | sha256sum -c --quiet -
  $SUDO R CMD INSTALL "$tmp/$1"
}
get pathifier_1.40.0.tar.gz 76dd66e9e9690eb73002de1ee4042497c2ef5e94fae202e280d308505a60b078 \
  https://bioconductor.org/packages/3.18/bioc/src/contrib/pathifier_1.40.0.tar.gz \
  https://bioconductor.org/packages/3.18/bioc/src/contrib/Archive/pathifier/pathifier_1.40.0.tar.gz
get penalized_0.9-53.tar.gz bf346aff13c3bf8ca1c30181570e7186728aceb939824a3650b4102e3355d9dc \
  https://cran.r-project.org/src/contrib/penalized_0.9-53.tar.gz \
  https://cran.r-project.org/src/contrib/Archive/penalized/penalized_0.9-53.tar.gz
rm -rf "$tmp"

#!/usr/bin/env bash
# Install the pinned R environment of the PMC2661051 reproduction on Ubuntu 24.04 (as root or with
# sudo): R 4.3.3 and the R packages from the Ubuntu archive at fixed versions, and globaltest 5.56.0
# from its Bioconductor 3.18 source tarball (SHA-256 checked). The package gseamod itself is
# installed by the pipeline from PMC2661051/package.
set -euo pipefail
SUDO=""; [ "$(id -u)" = 0 ] || SUDO=sudo
$SUDO apt-get update -qq
$SUDO env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
  r-base-core=4.3.3-2build2 r-base-dev=4.3.3-2build2 \
  r-bioc-limma=3.58.1+dfsg-1 r-cran-fdrtool=1.2.17-1 r-cran-corpcor=1.6.10-1 \
  r-bioc-biobase=2.62.0-1 r-bioc-annotationdbi=1.64.1-1 r-bioc-annotate=1.80.0+dfsg-1 r-cran-survival=3.5-8-1 \
  r-cran-jsonlite=1.8.8+dfsg-1 r-cran-knitr=1.45+dfsg-1 r-cran-rmarkdown=2.25+dfsg-3 r-cran-testthat=3.2.1-1 \
  pandoc=3.1.3+ds-2
tmp=$(mktemp -d)
curl -fsSL --retry 3 -o "$tmp/globaltest_5.56.0.tar.gz" \
  https://bioconductor.org/packages/3.18/bioc/src/contrib/globaltest_5.56.0.tar.gz \
  || curl -fsSL --retry 3 -o "$tmp/globaltest_5.56.0.tar.gz" \
  https://bioconductor.org/packages/3.18/bioc/src/contrib/Archive/globaltest/globaltest_5.56.0.tar.gz
echo "b9dcd63668b914e2cb28e7268090c49ed8eef62f0b1f836574805aff42d76c92  $tmp/globaltest_5.56.0.tar.gz" | sha256sum -c --quiet -
$SUDO R CMD INSTALL "$tmp/globaltest_5.56.0.tar.gz"
rm -rf "$tmp"

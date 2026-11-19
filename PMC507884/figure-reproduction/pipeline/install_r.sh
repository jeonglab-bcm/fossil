#!/usr/bin/env bash
# Install the pinned R environment of the PMC507884 reproduction on Ubuntu 24.04 (as root or with
# sudo): R 4.3.3 and the R packages from the Ubuntu archive at fixed versions (nlme 3.1-164, the
# version the reproduction was made with). The package hkselect itself is installed by the
# pipeline from PMC507884/package.
set -euo pipefail
SUDO=""; [ "$(id -u)" = 0 ] || SUDO=sudo
$SUDO apt-get update -qq
$SUDO env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
  r-base-core=4.3.3-2build2 r-base-dev=4.3.3-2build2 \
  r-cran-nlme=3.1.164-1build1 r-cran-numderiv=2016.8-1.1-3 r-cran-readxl=1.4.3-1 \
  r-cran-jsonlite=1.8.8+dfsg-1 r-cran-knitr=1.45+dfsg-1 r-cran-rmarkdown=2.25+dfsg-3 r-cran-testthat=3.2.1-1 \
  pandoc=3.1.3+ds-2

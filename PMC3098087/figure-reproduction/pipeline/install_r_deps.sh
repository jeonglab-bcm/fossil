#!/usr/bin/env bash
# Install R and the R packages of the PMC3098087 pipeline on Ubuntu 24.04 (as root or with sudo),
# at the versions the committed outputs were made with:
#   R 4.3.3 and class 7.3-22, randomForest 4.7-1.1, e1071 1.7-14, Hmisc 5.1-1, jsonlite 1.8.8,
#   testthat 3.2.1, knitr 1.45, rmarkdown 2.25 (Ubuntu 24.04 packages), pandoc 3.1.3;
#   pamr 1.57 and stepPlr 0.93 from CRAN sources (CRAN archive as the fallback).
set -euo pipefail
SUDO=$([[ $(id -u) -eq 0 ]] && echo "" || echo sudo)
$SUDO apt-get update -qq
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y -qq --no-install-recommends \
  r-base-core=4.3.3-2build2 r-base-dev r-cran-class r-cran-randomforest r-cran-e1071 r-cran-hmisc \
  r-cran-jsonlite r-cran-testthat r-cran-knitr r-cran-rmarkdown pandoc poppler-utils > /dev/null
for pkg in pamr_1.57 stepPlr_0.93; do
  name=${pkg%_*}
  curl -fsSL --retry 3 -o "/tmp/$pkg.tar.gz" "https://cran.r-project.org/src/contrib/$pkg.tar.gz" \
    || curl -fsSL --retry 3 -o "/tmp/$pkg.tar.gz" "https://cran.r-project.org/src/contrib/Archive/$name/$pkg.tar.gz"
  $SUDO R CMD INSTALL "/tmp/$pkg.tar.gz" > /dev/null
done
Rscript -e 'for (p in c("class", "randomForest", "e1071", "pamr", "stepPlr", "Hmisc", "jsonlite")) cat(p, as.character(packageVersion(p)), "\n")'

# Install the R packages the pipeline uses: minet from Bioconductor 3.18 (R 4.3), version 3.60.0.
lib <- Sys.getenv("GECON_RLIB"); if (nzchar(lib)) { dir.create(lib, showWarnings = FALSE, recursive = TRUE); .libPaths(c(lib, .libPaths())) }
options(repos = c(CRAN = "https://cloud.r-project.org"))
if (!requireNamespace("BiocManager", quietly = TRUE)) install.packages("BiocManager")
BiocManager::install(version = "3.18", ask = FALSE, update = FALSE)
BiocManager::install("minet", ask = FALSE, update = FALSE)
stopifnot(as.character(packageVersion("minet")) == "3.60.0")

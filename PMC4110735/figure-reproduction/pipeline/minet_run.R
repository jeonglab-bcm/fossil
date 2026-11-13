# ARACNE, CLR and MRNET from minet (Meyer et al. 2008) with minet()'s defaults, as the paper says
# ("we use the parameters as used in [28]"): estimator "spearman", no discretisation.
# Usage: Rscript minet_run.R IN.tsv OUTPREFIX   (IN: genes in rows, conditions in columns, header row)
args <- commandArgs(trailingOnly = TRUE)
lib <- Sys.getenv("GECON_RLIB"); if (nzchar(lib)) .libPaths(c(lib, .libPaths()))
suppressPackageStartupMessages(library(minet))
x <- as.matrix(read.delim(args[1], row.names = 1, check.names = FALSE))
d <- t(x)  # minet wants samples in rows
for (m in c("aracne", "clr", "mrnet")) {
  net <- minet(d, method = m, estimator = "spearman", disc = "none")
  write.table(net, paste0(args[2], "_", m, ".tsv"), sep = "\t", quote = FALSE, col.names = NA)
}
cat(as.character(packageVersion("minet")), "\n")

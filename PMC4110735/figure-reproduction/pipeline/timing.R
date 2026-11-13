# Time minet's ARACNE (mutual information matrix + ARACNE) on a genes x conditions TSV.
# Usage: Rscript timing.R IN.tsv REPS   -> prints "mim_seconds aracne_seconds total_seconds" (medians)
args <- commandArgs(trailingOnly = TRUE)
lib <- Sys.getenv("GECON_RLIB"); if (nzchar(lib)) .libPaths(c(lib, .libPaths()))
suppressPackageStartupMessages(library(minet))
x <- t(as.matrix(read.delim(args[1], row.names = 1, check.names = FALSE)))
reps <- as.integer(args[2])
t1 <- t2 <- numeric(reps)
for (i in seq_len(reps)) {
  a <- system.time(mim <- build.mim(x, estimator = "spearman"))[["elapsed"]]
  b <- system.time(net <- aracne(mim))[["elapsed"]]
  t1[i] <- a; t2[i] <- b
}
cat(median(t1), median(t2), median(t1 + t2), "\n")

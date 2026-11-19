# Pathway deregulation scores of one data set.
#   Rscript pds.R DATA_DIR SET OUT.csv CORES [PATHWAY_INDICES]
# PATHWAY_INDICES (comma-separated, 1-based, into the 403 gene sets) limits the run to those
# pathways (the CI check); without it every pathway is scored, in chunks of 40 saved next to
# OUT.csv (OUT.csv.part<k>.csv), so an interrupted run resumes where it stopped. Every pathway uses
# the same subsamplings (seed 1), so chunking does not change any score. Writes pathways x samples,
# with a column "flipped" (TRUE when the ends were swapped so that the score rises with expression).
suppressPackageStartupMessages(library(pdscox))
invisible(Sys.setlocale("LC_COLLATE", "C"))  # group order ("LN+" before "LN-") must not depend on the locale
a <- commandArgs(TRUE)
d <- readRDS(file.path(a[1], paste0(a[2], ".rds")))
gs <- readRDS(file.path(a[1], "genesets.rds"))
idx <- if (length(a) >= 5 && nzchar(a[5])) as.integer(strsplit(a[5], ",")[[1]]) else seq_along(gs)
score <- function(i) {
  sc <- pathway_scores(d$expr, gs[i], cores = as.integer(a[4]), seed = 1)
  data.frame(pathway = rownames(sc), flipped = attr(sc, "flipped"), signif(sc, 10), check.names = FALSE)
}
chunks <- split(idx, ceiling(seq_along(idx) / 40))
parts <- lapply(seq_along(chunks), function(k) {
  f <- paste0(a[3], ".part", k, ".csv")
  if (length(chunks) > 1 && file.exists(f)) return(read.csv(f, check.names = FALSE))
  p <- score(chunks[[k]])
  if (length(chunks) > 1) write.csv(p, f, row.names = FALSE)
  p
})
write.csv(do.call(rbind, parts), a[3], row.names = FALSE)
unlink(paste0(a[3], ".part", seq_along(chunks), ".csv"))

# Pathway deregulation scores of one data set.
#   Rscript pds.R DATA_DIR SET OUT.csv CORES [PATHWAY_INDICES]
# PATHWAY_INDICES (comma-separated, 1-based, into the 403 gene sets) limits the run to those
# pathways (the CI check); without it every pathway is scored. Writes pathways x samples, with a
# column "flipped" (TRUE when the ends were swapped so that the score rises with expression).
suppressPackageStartupMessages(library(pdscox))
a <- commandArgs(TRUE)
d <- readRDS(file.path(a[1], paste0(a[2], ".rds")))
gs <- readRDS(file.path(a[1], "genesets.rds"))
if (length(a) >= 5 && nzchar(a[5])) gs <- gs[as.integer(strsplit(a[5], ",")[[1]])]
sc <- pathway_scores(d$expr, gs, cores = as.integer(a[4]), seed = 1)
out <- data.frame(pathway = rownames(sc), flipped = attr(sc, "flipped"), signif(sc, 10),
                  check.names = FALSE)
write.csv(out, a[3], row.names = FALSE)

# Read the Sotiriou et al. (2003) BRB-ArrayTools project into an R matrix.
#   Rscript read_sotiriou.R PROJECT_DIR OUT.rds
# BinaryData/ProcessedLog1..7 hold 4-byte little-endian floats, 15 arrays per file, each array's
# 7,650 log ratios in turn (7 x 15 = 105 slots for 99 arrays; the last six are empty). Missing
# values are -9999999; the paper replaced missing log values with 0. Arrays are in the order of
# ExperimentNames1, which is the order of ExperimentTable.
args <- commandArgs(trailingOnly = TRUE)
bd <- file.path(args[1], "BinaryData")
ngenes <- as.integer(trimws(readLines(file.path(bd, "NumUniqueGenes1"), warn = FALSE)))
chunk <- as.integer(trimws(readLines(file.path(bd, "ExpChunkSize1"), warn = FALSE)))
tab <- read.delim(file.path(bd, "ExperimentTable"), check.names = FALSE, stringsAsFactors = FALSE)
n <- nrow(tab)
vals <- unlist(lapply(1:ceiling(n / chunk), function(i) {
  f <- file.path(bd, paste0("ProcessedLog", i))
  readBin(f, "numeric", size = 4, endian = "little", n = file.size(f) / 4)
}))
x <- t(matrix(vals, nrow = ngenes))[seq_len(n), ]
miss <- x < -1e6
x[miss] <- 0
er <- as.integer(trimws(tab[["ER category LBA (1=positive; 0=negative)"]]))
grade <- as.integer(trimws(tab[["Grade"]]))
rownames(x) <- tab[["Experiment Names"]]
out <- list(x = x, er = er, grade = grade, missing = sum(miss), arrays = n, probes = ngenes)
saveRDS(out, args[2])
cat(sprintf("%d arrays x %d probes, %d missing set to 0; ER- %d, ER+ %d; grade 1-2 %d, grade 3 %d\n",
            n, ngenes, sum(miss), sum(er == 0), sum(er == 1), sum(grade <= 2), sum(grade == 3)))

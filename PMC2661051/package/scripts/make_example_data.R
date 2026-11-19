# Writes the example files in inst/extdata. Run from the package folder after installing gseamod:
#   Rscript scripts/make_example_data.R
library(gseamod)
d <- simulate_ackermann(seed = 2009)
ext <- "inst/extdata"
write.csv(data.frame(gene = rownames(d$X), round(d$X, 4), check.names = FALSE),
          file.path(ext, "sim_expression.csv"), row.names = FALSE)
write.csv(data.frame(sample = colnames(d$X), class = d$y), file.path(ext, "sim_labels.csv"), row.names = FALSE)
writeLines(vapply(names(d$sets), function(n) paste(c(n, "simulated", rownames(d$X)[d$sets[[n]]]), collapse = "\t"), ""),
           file.path(ext, "sim_sets.gmt"))
# The expected output: Table 4 of the paper, resampling column (mean of squared moderated t,
# gene sampling, 100 simulated data sets), as printed.
write.csv(data.frame(set = paste0("set", 1:9),
                     detection_rate = c("0.67", "0.92", "0.01", "0.44", "0.41", "0.85", "1.00", "0.70", "0.90")),
          file.path(ext, "paper_table4_resampling.csv"), row.names = FALSE, quote = FALSE)

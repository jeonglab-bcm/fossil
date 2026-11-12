# Writes the bundled example data (inst/extdata):
#   example_data.csv          1000 features x 20 samples from the paper's simulation design
#                             (pi0 = 0.8, n = 10 per group, bitriangular effects, noise SD 0.1),
#                             set.seed(2010), values rounded to 6 significant digits
#   expected_fdr_power.csv    achieved FDR and power after filtering, computed here with base R
#                             only (stats::t.test, stats::quantile, stats::p.adjust), not with filterfdr
# Run from the package folder: Rscript inst/scripts/make_example_data.R
library(filterfdr)
set.seed(2010)
s <- simulate_two_group(m = 1000, pi0 = 0.8, n = 10, noise_sd = 0.1)
x <- signif(s$x, 6)
colnames(x) <- c(paste0("X", 1:10), paste0("Y", 1:10))
d <- data.frame(feature = sprintf("f%04d", seq_len(nrow(x))), null = s$null, x, check.names = FALSE)
write.csv(d, "inst/extdata/example_data.csv", row.names = FALSE, quote = FALSE)

# expected output, independent of the package
gx <- grep("^X", names(d)); gy <- grep("^Y", names(d))
xm <- as.matrix(d[, c(gx, gy)])
p <- apply(xm, 1, function(r) t.test(r[1:10], r[11:20], var.equal = TRUE)$p.value)
stat <- list(foldchange = abs(rowMeans(xm[, 1:10]) - rowMeans(xm[, 11:20])),
             signal = rowMeans(xm),
             variance = apply(xm, 1, var))
out <- NULL
for (f in names(stat)) for (fr in c(0, 0.25, 0.5, 0.75)) {
  keep <- if (fr == 0) rep(TRUE, nrow(xm)) else stat[[f]] > quantile(stat[[f]], fr)
  rej <- rep(FALSE, nrow(xm))
  rej[keep] <- p.adjust(p[keep], "BH") <= 0.05
  out <- rbind(out, data.frame(filter = f, fraction = fr, kept = sum(keep), rejected = sum(rej),
                               false_positives = sum(rej & d$null),
                               fdr = if (sum(rej)) sum(rej & d$null) / sum(rej) else 0,
                               power = sum(rej & !d$null) / sum(!d$null)))
}
write.csv(out, "inst/extdata/expected_fdr_power.csv", row.names = FALSE, quote = FALSE)
print(out)

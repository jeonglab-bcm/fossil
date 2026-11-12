# One simulated data set (the paper's "chosen at random"; ours is data set 1):
# the filter statistics by hypothesis (Fig. 2) and the FDR-bias test with
# 1000 permutations and the achieved FDR of BH, aBH, BY, q-value and
# Bonferroni on the unpermuted data (Figs 6 and S4).
#
# Usage: Rscript one_dataset.R <dataset> <noise_sd> <nperm> <out.json>
suppressMessages({library(filterfdr); library(jsonlite)})
args <- commandArgs(TRUE)
ds <- as.integer(args[1]); noise_sd <- as.numeric(args[2]); nperm <- as.integer(args[3]); out <- args[4]
F11 <- c(seq(0, 0.9, 0.1), 0.99)

set.seed(ds)
s <- simulate_two_group(noise_sd = noise_sd)
tt <- row_ttest(s$x, s$group)
fs <- filter_statistics(s$x, s$group, t = tt$statistic)

res <- list(dataset = ds, noise_sd = noise_sd, nperm = nperm,
            stats = list(null = s$null, foldchange = fs$foldchange, signal = fs$signal,
                         variance = fs$variance, tstat = fs$tstat))

# achieved FDR on the unpermuted data
fdr <- list()
for (f in c("foldchange", "signal", "variance")) {
  meth <- c("BH", "aBH", "BY", "bonferroni", if (f != "foldchange") "qvalue")
  d <- filter_curve(s, F11, f, meth, 0.05)
  fdr[[f]] <- split(d$fdr, d$method)
}
res$fdr <- fdr

# FDR-bias test: one set of permutations for all filters (set.seed(10^6 + ds)), one-sided
set.seed(1e6 + ds)
bt <- fdr_bias_test(s$x, s$group, c("foldchange", "signal", "variance"), F11, nperm)
boxes <- function(q) lapply(seq_len(ncol(q)), function(j)
  as.list(setNames(boxplot.stats(q[, j])$stats, c("whisker_low", "q1", "median", "q3", "whisker_high"))))
res$test <- lapply(bt, function(b) {
  two <- apply(b$Q, 2, function(v) suppressWarnings(ks.test(v, "punif")$p.value))
  list(fractions = F11, p.value = unname(b$p.value), label = unname(b$label),
       p.value_two_sided = unname(two), box = boxes(b$Q))
})
writeLines(toJSON(res, digits = NA, auto_unbox = TRUE), out)

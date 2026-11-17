# Simulation study (Additional File 1, section 8) for one chunk of data sets.
#
# Usage: Rscript simulate.R <first> <last> <noise_sd> <out_prefix> [pi0, default 0.8]
#
# Data set i is simulated with set.seed(i). For each data set:
#   curves   achieved FDR, power and pi0 at alpha 0.05 for the four filters and
#            four FDR methods (Figs 3, 4, S2), fractions 0..0.9, 0.99, 1
#   levels   BH at 21 levels for the three filters (Figs 5 and S3)
#   wilcoxon BH at 0.05 with the Wilcoxon rank-sum test (Fig. S6)
#   post     filtering before and after the correction (Figs S8, S9), data sets 1..200
# The chunk's sums over its data sets are written (so the means over all chunks
# can be formed without keeping every data set), plus the per-data-set rows of
# post (the figures plot one point per data set).
suppressMessages(library(filterfdr))
args <- commandArgs(TRUE)
first <- as.integer(args[1]); last <- as.integer(args[2])
noise_sd <- as.numeric(args[3]); out <- args[4]
pi0 <- if (length(args) >= 5) as.numeric(args[5]) else 0.8

F12 <- c(seq(0, 0.9, 0.1), 0.99, 1)
F11 <- c(seq(0, 0.9, 0.1), 0.99)
LEVELS <- c(seq(0, 0.95, 0.05), 0.99)
rows <- list()
post <- list()
for (i in first:last) {
  set.seed(i)
  s <- simulate_two_group(m = 5000, pi0 = pi0, n = 10, noise_sd = noise_sd, noise = "feature")
  d <- rbind(
    cbind(set = "curves", filter_curve(s, F12, c("foldchange", "signal", "variance", "tstat", "random"),
                                       c("BH", "BY", "aBH", "qvalue"), 0.05)),
    cbind(set = "levels", filter_curve(s, F11, c("foldchange", "signal", "variance"), "BH", LEVELS)),
    cbind(set = "wilcoxon", filter_curve(s, F11, c("foldchange", "signal", "variance", "tstat"), "BH", 0.05,
                                         test = "wilcoxon")))
  rows[[length(rows) + 1]] <- d
  if (i <= 200) {
    post[[length(post) + 1]] <- cbind(dataset = i, do.call(rbind, lapply(c("foldchange", "signal", "variance"),
                                      function(f) postfilter_compare(s, f))))
  }
}
fmt <- function(d) { for (k in names(d)) if (is.double(d[[k]])) d[[k]] <- sprintf("%.10g", d[[k]]); d }
d <- do.call(rbind, rows)
d$n <- 1
# sums over the chunk's data sets (a point missing in a data set, such as q-value with
# too few features left, counts in n only where present)
sums <- aggregate(cbind(fdr, power, pi0, rejected, kept, n) ~ set + filter + fraction + method + alpha,
                  data = d, FUN = sum)
sums <- sums[do.call(order, unname(as.list(sums[, c("set", "filter", "method", "alpha", "fraction")]))), ]
write.csv(fmt(sums), paste0(out, "_sums.csv"), row.names = FALSE, quote = FALSE)
if (length(post)) write.csv(fmt(do.call(rbind, post)), paste0(out, "_post.csv"), row.names = FALSE, quote = FALSE)

# Pool each simulated meta-analysis of crosscheck.py with R's metafor (rma, method = "DL"): an independent
# implementation to check rommeta's vectorized pooling against.
#   Rscript metafor_replicates.R TRIALS.csv OUT.csv
# MD and ROM: metafor's escalc. SMD: the paper's formula (Appendix), pooled by metafor. Studies whose ln RoM
# is undefined (a non-positive mean) are left out, as rma does with missing values.
suppressPackageStartupMessages(library(metafor))
args <- commandArgs(trailingOnly = TRUE)
d <- read.csv(args[1])
out <- list()
for (key in unique(paste(d$scenario, d$replicate))) {
  x <- d[paste(d$scenario, d$replicate) == key, ]
  N <- x$n_exp + x$n_contr
  sp <- sqrt(((x$n_exp - 1) * x$sd_exp^2 + (x$n_contr - 1) * x$sd_contr^2) / (N - 2))
  g <- (x$mean_exp - x$mean_contr) / sp * (1 - 3 / (4 * N - 9))
  es <- list(
    MD = escalc("MD", m1i = mean_exp, sd1i = sd_exp, n1i = n_exp, m2i = mean_contr, sd2i = sd_contr, n2i = n_contr, data = x),
    SMD = data.frame(yi = g, vi = N / (x$n_exp * x$n_contr) + g^2 / (2 * (N - 3.94))),
    RoM = suppressWarnings(escalc("ROM", m1i = mean_exp, sd1i = sd_exp, n1i = n_exp, m2i = mean_contr, sd2i = sd_contr, n2i = n_contr, data = x)))
  for (m in names(es)) {
    f <- suppressWarnings(rma(yi, vi, data = es[[m]], method = "DL"))
    out[[length(out) + 1]] <- data.frame(scenario = x$scenario[1], replicate = x$replicate[1], measure = m, k = f$k,
                                         estimate = sprintf("%.15g", as.numeric(f$b)), se = sprintf("%.15g", f$se),
                                         tau2 = sprintf("%.15g", f$tau2), q = sprintf("%.15g", f$QE), i2 = sprintf("%.15g", f$I2))
  }
}
write.csv(do.call(rbind, out), args[2], row.names = FALSE, quote = FALSE)
cat(sprintf("metafor %s: %d fits\n", packageVersion("metafor"), length(out)))

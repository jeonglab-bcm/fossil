# Expected output for src/rommeta/data/trials.csv from an independent implementation: R's metafor
# (escalc and rma with method = "DL"), not from rommeta.
#   Rscript scripts/metafor_expected.R src/rommeta/data/trials.csv src/rommeta/data/trials_expected.csv
# MD and ROM are metafor's own effect sizes (vtype "LS"; no bias correction for ROM). metafor's SMD uses
# another variance and an exact small-sample correction, so the paper's SMD (Appendix: g x [1 - 3/(4N - 9)],
# Var = N/(n_e n_c) + g^2/(2(N - 3.94))) is computed here in R from the formula and pooled by metafor.
# CIs use qnorm(0.975) = 1.959964 (metafor's), so the package is called with z = 1.959963984540054 to compare.
suppressPackageStartupMessages(library(metafor))
args <- commandArgs(trailingOnly = TRUE)
d <- read.csv(args[1])
md  <- escalc("MD",  m1i = mean_exp, sd1i = sd_exp, n1i = n_exp, m2i = mean_contr, sd2i = sd_contr, n2i = n_contr, data = d)
rom <- escalc("ROM", m1i = mean_exp, sd1i = sd_exp, n1i = n_exp, m2i = mean_contr, sd2i = sd_contr, n2i = n_contr, data = d)
N <- d$n_exp + d$n_contr
sp <- sqrt(((d$n_exp - 1) * d$sd_exp^2 + (d$n_contr - 1) * d$sd_contr^2) / (N - 2))
g <- (d$mean_exp - d$mean_contr) / sp * (1 - 3 / (4 * N - 9))
vg <- N / (d$n_exp * d$n_contr) + g^2 / (2 * (N - 3.94))
row <- function(measure, fit, back) {
  e <- as.numeric(fit$b)
  data.frame(measure = measure, k = fit$k,
             estimate = if (back) exp(e) else e, ci_low = if (back) exp(fit$ci.lb) else fit$ci.lb,
             ci_high = if (back) exp(fit$ci.ub) else fit$ci.ub, p = fit$pval,
             log_estimate = if (back) e else NA, se = fit$se, q = fit$QE, tau2 = fit$tau2, i2 = fit$I2)
}
out <- rbind(row("MD", rma(yi, vi, data = md, method = "DL"), FALSE),
             row("SMD", rma(g, vg, method = "DL"), FALSE),
             row("RoM", rma(yi, vi, data = rom, method = "DL"), TRUE))
for (col in names(out)[-(1:2)]) out[[col]] <- ifelse(is.na(out[[col]]), "", sprintf("%.15g", out[[col]]))
write.csv(out, args[2], row.names = FALSE, quote = FALSE)
cat(sprintf("metafor %s: %s\n", packageVersion("metafor"), args[2]))

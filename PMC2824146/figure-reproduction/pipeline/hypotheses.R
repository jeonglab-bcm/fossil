# Hypothesis tests for two Fig. 6 gaps, with the package's own functions.
#   Rscript hypotheses.R hypotheses.json [REPS_LR] [REPS_CC]
# A. Fig. 6a, likelihood ratio p-values after MI: how the m chi-square statistics are pooled.
#    Li et al. (1991) D2 (ours) against D2 with the variance of d in place of sqrt(d), the median
#    of the m p-values, and the mean of the m p-values; MAR at 50 and 75%, three MI methods.
# C. Figs 7 and 8, MNAR: X3's own term, ln(1.3) X3 / SD(X3) on the raw scale (ours) against the
#    same on the log(X3 + 1) scale; MICE estimate and coverage of X3 at 50 and 75%.
# B. Fig. 6b-d, complete cases under MAR: the time term of X5's missingness, ln(0.7) ln(t).
#    Ours (log of t / SD(t)), the log time divided by its SD, no time term, and the term reversed.
suppressMessages(library(misscox))
a <- commandArgs(TRUE)
reps_lr <- if (length(a) >= 2) as.integer(a[2]) else 10L
reps_cc <- if (length(a) >= 3) as.integer(a[3]) else 200L
cv <- gbsg_covariates(); pr <- generation_parameters(cv)
k <- 9
d2 <- function(d, sq = TRUE) {
  m <- length(d); u <- if (sq) sqrt(d) else d
  r <- (1 + 1 / m) * stats::var(u)
  st <- (mean(d) / k - (m + 1) / (m - 1) * r) / (1 + r)
  df2 <- k^(-3 / m) * (m - 1) * (1 + 1 / r)^2
  stats::pf(max(st, 0), k, df2, lower.tail = FALSE)
}
imp <- list(MICE_PMM = function(x, s) misscox:::impute_mice(x, 20, 20, "pmm", TRUE, s),
            AREG = function(x, s) misscox:::impute_areg(x, 20, 1, s),
            MIX_notrunc = function(x, s) misscox:::impute_mix(x, 20, 100, s, truncate = FALSE))
A <- list()
for (lev in c(0.50, 0.75)) for (meth in names(imp)) {
  p <- sapply(seq_len(reps_lr), function(r) {
    x <- simulate_cohort(1000, pr, seed = misscox:::replicate_seed(r))
    xm <- impose_missing(x, "MAR", lev, seed = misscox:::replicate_seed(r, 2, round(100 * lev)))
    lr <- vapply(imp[[meth]](xm, misscox:::replicate_seed(r, 2, round(100 * lev), 99)),
                 function(f) analyse_complete(f)$lr, 0)
    pv <- stats::pchisq(lr, k, lower.tail = FALSE)
    c(D2 = d2(lr), D2_var_d = d2(lr, FALSE), median_p = stats::median(pv), mean_p = mean(pv))
  })
  A[[length(A) + 1]] <- c(list(level = lev, method = meth, reps = reps_lr), as.list(rowMeans(p)))
}
mech_x5 <- function(x, lev, variant, seed) {
  set.seed(seed)
  n <- nrow(x); d <- missing_design(lev, n)
  lo <- function(p) log(p / (1 - p))
  t5 <- switch(variant, ours = log(0.7) * log(x$time / sd(x$time)),
               log_t_over_sd = log(0.7) * log(x$time) / sd(log(x$time)),
               none = rep(0, n), reversed = -log(0.7) * log(x$time / sd(x$time)))
  pr_ <- function(b0, term, extra) stats::plogis(b0 - mean(term) + term + extra)
  u <- matrix(stats::runif(4 * n), n, 4)
  m3 <- u[, 1] <= pr_(lo(d$p0["X3"]), log(0.8) * x$X4 / sd(x$X4), 0)
  m2 <- u[, 2] <= pr_(lo(d$p0["X2"]), log(3) * x$X1 / sd(x$X1), log(d$odds_ratios["X2_MX3"]) * m3)
  m5 <- u[, 3] <= pr_(lo(d$p0["X5"]), t5, log(d$odds_ratios["X5_MX2"]) * m2)
  m8 <- u[, 4] <= pr_(lo(d$p0["X8"]), log(7) * x$X7, log(d$odds_ratios["X8_MX3"]) * m3)
  x[!(m3 | m2 | m5 | m8), ]
}
B <- list()
for (variant in c("ours", "log_t_over_sd", "none", "reversed")) for (lev in c(0.50, 0.75)) {
  s <- sapply(seq_len(reps_cc), function(r) {
    x <- simulate_cohort(1000, pr, seed = misscox:::replicate_seed(r))
    f <- analyse_complete(mech_x5(x, lev, variant, misscox:::replicate_seed(r, 2, round(100 * lev), 77)))
    c(r2 = f$r2, d = f$d, surv = f$surv)
  })
  B[[length(B) + 1]] <- c(list(variant = variant, level = lev, reps = reps_cc), as.list(rowMeans(s)))
}
mnar_x3 <- function(x, lev, scale, seed) {
  xm <- impose_missing(x, "MNAR", lev, seed = seed)
  if (scale == "raw") return(xm)
  set.seed(seed)
  n <- nrow(x); d <- missing_design(lev, n); lo <- function(p) log(p / (1 - p))
  pr_ <- function(b0, term, extra) stats::plogis(b0 - mean(term) + term + extra)
  u <- matrix(stats::runif(4 * n), n, 4)
  l3 <- log(x$X3 + 1)
  m3 <- u[, 1] <= pr_(lo(d$p0["X3"]), log(1.3) * l3 / sd(l3), 0)
  m2 <- u[, 2] <= pr_(lo(d$p0["X2"]), log(0.6) * x$X2 / sd(x$X2), log(d$odds_ratios["X2_MX3"]) * m3)
  m5 <- u[, 3] <= pr_(lo(d$p0["X5"]), log(8) * x$X5, log(d$odds_ratios["X5_MX2"]) * m2)
  m8 <- u[, 4] <= pr_(lo(d$p0["X8"]), log(0.9) * x$X8g, log(d$odds_ratios["X8_MX3"]) * m3)
  out <- x; out$X3[m3] <- NA; out$X2[m2] <- NA; out$X5[m5] <- NA; out$X8g[m8] <- NA
  out
}
tv <- c(X3 = -0.0023407)  # our true value (summary.json)
C <- list()
for (scale in c("raw", "log")) for (lev in c(0.50, 0.75)) {
  s <- sapply(seq_len(reps_lr), function(r) {
    x <- simulate_cohort(1000, pr, seed = misscox:::replicate_seed(r))
    f <- handle_missing(mnar_x3(x, lev, scale, misscox:::replicate_seed(r, 3, round(100 * lev))), "MICE",
                        seed = misscox:::replicate_seed(r, 3, round(100 * lev), 6))
    c(est_X3 = f$est_X3, covered = f$lo_X3 <= tv[["X3"]] && tv[["X3"]] <= f$hi_X3)
  })
  C[[length(C) + 1]] <- c(list(scale = scale, level = lev, method = "MICE", reps = reps_lr), as.list(rowMeans(s)))
}
writeLines(jsonlite::toJSON(list(lr_pooling = A, cc_time_term = B, mnar_x3_scale = C), auto_unbox = TRUE, digits = 8,
                            pretty = TRUE), a[1])

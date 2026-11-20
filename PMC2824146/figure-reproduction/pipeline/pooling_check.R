# Fig. 6a check: pool the m = 20 likelihood ratio / Wald results of each MI replicate in several
# standard ways (D1, Wald with total variance, D2 as in the paper, D2 on var(d), D3, and summaries of
# the m p-values), to see whether any gives the paper's MAR p-values. Same cohorts, missingness and
# seeds as run_sim.R.   Rscript pooling_check.R <first_rep> <last_rep> <out.csv>
suppressMessages(library(misscox))
a <- commandArgs(TRUE)
reps <- as.integer(a[1]):as.integer(a[2]); out <- a[3]
cv <- gbsg_covariates(); pr <- generation_parameters(cv)
k <- 9; m <- 20
it <- c(MIX = 100, MICE = 20, AREG = 1)
meth_code <- setNames(seq_along(method_labels()), method_labels())
imp <- list(
  MICE             = function(x, s) misscox:::impute_mice(x, m, it[["MICE"]], "norm", TRUE, s),
  MICE_PMM         = function(x, s) misscox:::impute_mice(x, m, it[["MICE"]], "pmm", TRUE, s),
  MICE_PMM_notrans = function(x, s) misscox:::impute_mice(x, m, it[["MICE"]], "pmm", FALSE, s),
  AREG             = function(x, s) misscox:::impute_areg(x, m, it[["AREG"]], s),
  MIX_notrunc      = function(x, s) misscox:::impute_mix(x, m, it[["MIX"]], s, truncate = FALSE))

fit_one <- function(f) {
  fit <- fit_full_cox(f)
  list(b = coef(fit), V = vcov(fit), lr = 2 * diff(fit$loglik), ll0 = fit$loglik[1],
       X = fit$x, y = fit$y)
}
# log partial likelihood of one dataset at fixed coefficients (for D3)
ll_at <- function(fo, b) {
  g <- survival::coxph(fo$y ~ fo$X, init = b, ties = "efron",
                       control = survival::coxph.control(iter.max = 0))
  g$loglik[1]
}
df_li <- function(r) {          # Li, Raghunathan and Rubin (1991) denominator df
  t <- k * (m - 1)
  if (t > 4) 4 + (t - 4) * (1 + (1 - 2 / t) / r)^2 else t * (1 + 1 / k) * (1 + 1 / r)^2 / 2
}
pool_all <- function(fs) {
  B_ <- t(sapply(fs, `[[`, "b")); lr <- sapply(fs, `[[`, "lr")
  qbar <- colMeans(B_); Ubar <- Reduce(`+`, lapply(fs, `[[`, "V")) / m; Bm <- cov(B_)
  Tm <- Ubar + (1 + 1 / m) * Bm
  # D1: multivariate Wald, Rubin's rules (Li, Raghunathan, Rubin 1991)
  r1 <- (1 + 1 / m) * sum(diag(Bm %*% solve(Ubar))) / k
  D1 <- drop(t(qbar) %*% solve(Ubar) %*% qbar) / (k * (1 + r1))
  # Wald with Rubin's total variance, chi-square reference (e.g. Hmisc fit.mult.impute + anova)
  W <- drop(t(qbar) %*% solve(Tm) %*% qbar)
  # D2: Li, Meng, Raghunathan, Rubin (1991) from the m chi-squares
  d2 <- function(u) {
    r <- (1 + 1 / m) * var(u)
    st <- (mean(lr) / k - (m + 1) / (m - 1) * r) / (1 + r)
    pf(max(st, 0), k, k^(-3 / m) * (m - 1) * (1 + 1 / r)^2, lower.tail = FALSE)
  }
  # D3: Meng and Rubin (1992), likelihood ratio at the pooled coefficients
  dt <- mean(sapply(fs, function(fo) 2 * (ll_at(fo, qbar) - fo$ll0)))
  r3 <- (m + 1) / (k * (m - 1)) * (mean(lr) - dt)
  D3 <- dt / (k * (1 + r3))
  pv <- pchisq(lr, k, lower.tail = FALSE)
  c(D1 = pf(D1, k, df_li(r1), lower.tail = FALSE),
    Wald_T_chisq = pchisq(W, k, lower.tail = FALSE),
    D2 = d2(sqrt(lr)), D2_var_d = d2(lr),
    D3 = pf(max(D3, 0), k, df_li(max(r3, 1e-12)), lower.tail = FALSE),
    mean_p = mean(pv), median_p = median(pv), max_p = max(pv),
    p_mean_lr = pchisq(mean(lr), k, lower.tail = FALSE),
    p_first_imp = pv[1], p_last_imp = pv[m],
    r_D1 = r1, r_D3 = r3, mean_lr = mean(lr))
}

rows <- list()
for (r in reps) {
  x <- simulate_cohort(1000, pr, seed = misscox:::replicate_seed(r))
  for (lev in c(0.50, 0.75)) {
    xm <- impose_missing(x, "MAR", lev, seed = misscox:::replicate_seed(r, 2, round(100 * lev)))
    for (meth in names(imp)) {
      fs <- lapply(imp[[meth]](xm, misscox:::replicate_seed(r, 2, round(100 * lev),
                                                            meth_code[[meth]])), fit_one)
      rows[[length(rows) + 1]] <- data.frame(rep = r, level = lev, method = meth,
        t(pool_all(fs)))
      write.csv(do.call(rbind, rows), out, row.names = FALSE)
    }
  }
}

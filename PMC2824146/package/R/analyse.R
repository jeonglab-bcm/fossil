# The analysis model and the outcomes of interest (Methods, "Analysis and outcomes of
# interest"; "Combining estimates ... after MI").

coef_names <- c("X1", "X2", "X3", "X4", "X5", "X6", "X7", "X8d1", "X8d2")

#' Analyse one complete dataset
#'
#' Fits the full Cox model and returns the coefficients, standard errors, the likelihood
#' ratio statistic, Nagelkerke's R2, the prognostic separation D statistic (Royston and
#' Sauerbrei 2004) and the predicted survival at `horizon` days at the mean covariates.
#' @param x A complete data frame with X1 to X7, X8g, time and status.
#' @param horizon Time for the predicted survival, in days (2 years = 730.5).
#' @return A list.
#' @export
analyse_complete <- function(x, horizon = 730.5) {
  fit <- fit_full_cox(x)
  n <- nrow(x)
  b <- stats::coef(fit)
  se <- sqrt(diag(stats::vcov(fit)))
  ll0 <- fit$loglik[1]
  ll1 <- fit$loglik[2]
  lr <- 2 * (ll1 - ll0)
  r2 <- (1 - exp(-lr / n)) / (1 - exp(2 * ll0 / n))
  # D: Cox regression on the scaled normal scores of the prognostic index
  pi_ <- as.numeric(fit$x %*% b)
  z <- stats::qnorm((rank(pi_, ties.method = "average") - 3 / 8) / (n + 1 / 4)) /
    sqrt(8 / pi)
  dfit <- survival::coxph(survival::Surv(x$time, x$status) ~ z)
  # At the means of all covariates, binaries included (survival 3.x centres 0/1
  # covariates at 0 by default; the survival package of 2004 used the means).
  nd <- as.data.frame(t(colMeans(fit$x)))
  sf <- summary(survival::survfit(fit, newdata = nd), times = horizon, extend = TRUE)
  s2 <- sf$surv
  # variance of log(-log S) by the delta method from the variance of log S
  var_cll <- (sf$std.err / s2)^2 / log(s2)^2
  list(coef = stats::setNames(as.numeric(b), coef_names),
       se = stats::setNames(as.numeric(se), coef_names),
       lr = lr, r2 = r2, d = as.numeric(stats::coef(dfit)),
       d_se = sqrt(as.numeric(stats::vcov(dfit))), surv = s2,
       cll = log(-log(s2)), cll_var = var_cll, n = n, events = sum(x$status))
}

#' Rubin's rules
#' @param est,var Vectors of the m estimates and their variances.
#' @return A list with the pooled estimate, total variance, degrees of freedom (Rubin
#'   1987) and the fraction of missing information.
#' @export
rubin_pool <- function(est, var) {
  m <- length(est)
  qbar <- mean(est)
  ubar <- mean(var)
  b <- stats::var(est)
  t <- ubar + (1 + 1 / m) * b
  r <- (1 + 1 / m) * b / ubar
  df <- if (b > 0) (m - 1) * (1 + 1 / r)^2 else Inf
  list(est = qbar, var = t, df = df)
}

#' Combine m chi-square statistics (Li, Meng, Raghunathan and Rubin 1991)
#' @param d The m chi-square statistics.
#' @param k Their degrees of freedom.
#' @return A list with the statistic D2, its degrees of freedom and the p-value.
#' @export
pool_chisq <- function(d, k) {
  m <- length(d)
  r <- (1 + 1 / m) * stats::var(sqrt(d))
  d2 <- (mean(d) / k - (m + 1) / (m - 1) * r) / (1 + r)
  df2 <- k^(-3 / m) * (m - 1) * (1 + 1 / r)^2
  list(stat = d2, df1 = k, df2 = df2,
       p = stats::pf(max(d2, 0), k, df2, lower.tail = FALSE))
}

#' Summarise the analysis of one or more completed datasets
#'
#' One completed dataset (CC, SI, full data): Wald tests and intervals on the normal
#' distribution. Several (MI): Rubin's rules for the coefficients, D and survival (after
#' a complementary log-log transformation), Li et al. for the likelihood ratio statistic,
#' and the median of the m R2 values.
#' @param fits A list of results from [analyse_complete()].
#' @return A one-row data frame: est_*, se_*, p_*, lo_*, hi_* for each coefficient, and
#'   lr_p, r2, d, surv, n_analysed.
#' @export
pool_fits <- function(fits) {
  m <- length(fits)
  out <- list()
  for (j in seq_along(coef_names)) {
    v <- coef_names[j]
    est <- vapply(fits, function(f) f$coef[j], 0)
    var <- vapply(fits, function(f) f$se[j]^2, 0)
    if (m == 1) {
      e <- est; s <- sqrt(var); q <- stats::qnorm(0.975); p <- 2 * stats::pnorm(-abs(e / s))
    } else {
      pr <- rubin_pool(est, var)
      e <- pr$est; s <- sqrt(pr$var); q <- stats::qt(0.975, pr$df)
      p <- 2 * stats::pt(-abs(e / s), pr$df)
    }
    out[[paste0("est_", v)]] <- e
    out[[paste0("se_", v)]] <- s
    out[[paste0("p_", v)]] <- p
    out[[paste0("lo_", v)]] <- e - q * s
    out[[paste0("hi_", v)]] <- e + q * s
  }
  lr <- vapply(fits, function(f) f$lr, 0)
  k <- length(coef_names)
  if (m == 1) {
    out$lr <- lr
    out$lr_p <- stats::pchisq(lr, k, lower.tail = FALSE)
    out$r2 <- fits[[1]]$r2
    out$d <- fits[[1]]$d
    out$surv <- fits[[1]]$surv
  } else {
    pc <- pool_chisq(lr, k)
    out$lr <- pc$stat * k
    out$lr_p <- pc$p
    out$r2 <- stats::median(vapply(fits, function(f) f$r2, 0))
    out$d <- rubin_pool(vapply(fits, function(f) f$d, 0),
                        vapply(fits, function(f) f$d_se^2, 0))$est
    cl <- rubin_pool(vapply(fits, function(f) f$cll, 0),
                     vapply(fits, function(f) f$cll_var, 0))$est
    out$surv <- exp(-exp(cl))
  }
  out$n_analysed <- fits[[1]]$n
  as.data.frame(out)
}

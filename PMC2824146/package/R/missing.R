# Imposing missing data (Methods, "Imposing missing data mechanisms"; Tables 2 and 3).

round_half_up <- function(x) floor(x + 0.5)

#' Missingness design for one overall level
#'
#' Cases with each covariate missing and with each pair missing, as whole cases of `n`,
#' rounded half up: X3 70%, X2 55%, X5 20% and X8 10% of the incomplete cases; X2 and X3
#' 35%, X5 and X2 10%, X8 and X3 5%.
#' @param level Overall share of incomplete cases (0.05 to 0.75).
#' @param n Number of cases.
#' @param shares,overlaps Shares of the incomplete cases (the paper's by default).
#' @return A list with the counts, the target probabilities and the Table 3 odds ratios.
#' @export
missing_design <- function(level, n = 1000,
                           shares = c(X3 = 0.70, X2 = 0.55, X5 = 0.20, X8 = 0.10),
                           overlaps = c(X2X3 = 0.35, X5X2 = 0.10, X8X3 = 0.05)) {
  k <- level * n
  a <- round_half_up(shares * k)
  names(a) <- names(shares)
  o <- round_half_up(overlaps * k)
  names(o) <- names(overlaps)
  pair_or <- function(a_dep, a_on, both) both * (n - a_dep - a_on + both) /
    ((a_dep - both) * (a_on - both))
  or <- c(X2_MX3 = pair_or(a["X2"], a["X3"], o["X2X3"]),
          X5_MX2 = pair_or(a["X5"], a["X2"], o["X5X2"]),
          X8_MX3 = pair_or(a["X8"], a["X3"], o["X8X3"]))
  names(or) <- c("X2_MX3", "X5_MX2", "X8_MX3")
  # probability of missingness when the conditioning covariate is observed
  p0 <- c(X3 = unname(a["X3"]) / n,
          X2 = unname(a["X2"] - o["X2X3"]) / (n - unname(a["X3"])),
          X5 = unname(a["X5"] - o["X5X2"]) / (n - unname(a["X2"])),
          X8 = unname(a["X8"] - o["X8X3"]) / (n - unname(a["X3"])))
  list(level = level, n = n, counts = a, overlaps = o, odds_ratios = or, p0 = p0)
}

#' Table 3 of the paper: odds ratios between missingness indicators
#' @param levels Overall shares of incomplete cases.
#' @param n Number of cases.
#' @return A data frame with one row per pair and one column per level.
#' @export
table3_odds_ratios <- function(levels = c(0.05, 0.10, 0.25, 0.50, 0.75), n = 1000) {
  m <- sapply(levels, function(l) missing_design(l, n)$odds_ratios)
  out <- data.frame(pair = c("X2|MX3", "X5|MX2", "X8|MX3"), m, row.names = NULL)
  names(out)[-1] <- paste0("pct", round(100 * levels))
  out
}

mechanism_terms <- function(mechanism, x) {
  sdz <- function(v) v / stats::sd(v)
  lt <- log(sdz(x$time))
  zero <- rep(0, nrow(x))
  switch(mechanism,
    MCAR = list(X3 = zero, X2 = zero, X5 = zero, X8 = zero),
    MAR = list(X3 = log(0.8) * sdz(x$X4), X2 = log(3) * sdz(x$X1),
               X5 = log(0.7) * lt, X8 = log(7) * x$X7),
    MNAR = list(X3 = log(1.3) * sdz(x$X3), X2 = log(0.6) * sdz(x$X2),
                X5 = log(8) * x$X5, X8 = log(0.9) * x$X8g),
    COMBINED = list(X3 = zero, X2 = log(0.7) * lt + log(0.3) * x$X5,
                    X5 = log(3) * sdz(x$X1), X8 = log(0.9) * x$X8g),
    stop("mechanism must be MCAR, MAR, MNAR or COMBINED"))
}

#' Impose multivariate missingness on X3, X2, X5 and X8
#'
#' Logistic models per covariate (Table 2) with the odds ratios of Table 3. Each
#' intercept is solved at the average value of the mechanism's terms; continuous
#' variables (and survival time) enter divided by their standard deviation.
#' @param x A cohort from [simulate_cohort()].
#' @param mechanism "MCAR", "MAR", "MNAR" or "COMBINED".
#' @param level Overall share of incomplete cases.
#' @param seed Optional seed; the random number state is restored afterwards.
#' @return `x` with NA in the deleted values and an attribute `indicators` (a 0/1 matrix).
#' @export
impose_missing <- function(x, mechanism, level, seed = NULL) {
  if (!is.null(seed)) {
    old <- if (exists(".Random.seed", globalenv())) get(".Random.seed", globalenv()) else NULL
    on.exit(if (is.null(old)) rm(".Random.seed", envir = globalenv()) else
      assign(".Random.seed", old, envir = globalenv()))
    set.seed(seed, kind = "Mersenne-Twister", normal.kind = "Inversion")
  }
  n <- nrow(x)
  d <- missing_design(level, n)
  tm <- mechanism_terms(mechanism, x)
  lo <- function(p) log(p / (1 - p))
  prob <- function(b0, term, extra) stats::plogis(b0 - mean(term) + term + extra)
  u <- matrix(stats::runif(4 * n), n, 4)
  m3 <- as.integer(u[, 1] <= prob(lo(d$p0["X3"]), tm$X3, 0))
  m2 <- as.integer(u[, 2] <= prob(lo(d$p0["X2"]), tm$X2, log(d$odds_ratios["X2_MX3"]) * m3))
  m5 <- as.integer(u[, 3] <= prob(lo(d$p0["X5"]), tm$X5, log(d$odds_ratios["X5_MX2"]) * m2))
  m8 <- as.integer(u[, 4] <= prob(lo(d$p0["X8"]), tm$X8, log(d$odds_ratios["X8_MX3"]) * m3))
  out <- x
  out$X3[m3 == 1] <- NA
  out$X2[m2 == 1] <- NA
  out$X5[m5 == 1] <- NA
  out$X8g[m8 == 1] <- NA
  attr(out, "indicators") <- cbind(X3 = m3, X2 = m2, X5 = m5, X8 = m8)
  out
}

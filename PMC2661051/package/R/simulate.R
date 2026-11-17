#' Simulate the data of Ackermann and Strimmer's simulation study
#'
#' 600 genes and 20 samples (10 per class), multivariate normal with unit
#' variances. 520 background genes (no shift, independent) and four blocks of
#' 20 genes: set 1 (shift 0.75, pairwise correlation 0.6), set 2 (shift 0.75,
#' independent), set 6 (10 genes shifted +1 and 10 shifted -1; correlation
#' 0.6 within a direction and -0.6 between) and set 7 (as set 6, independent).
#' Sets 3, 4, 5, 8 and 9 are built from these: 20 background genes; 10 genes
#' of set 1 or 2 with 10 background genes; 5 up- and 5 down-shifted genes of
#' set 6 or 7 with 10 background genes. The background genes of each mixed
#' set are drawn at random, independently for each set.
#'
#' @param seed optional random seed.
#' @param shift the shift of sets 1 and 2 (0.75) and of sets 6 and 7 (1).
#' @param rho the within-block correlation (0.6).
#' @return A list with \code{X} (600 x 20, genes in rows), \code{y} (0/1
#'   labels, 1 is the shifted class) and \code{sets} (the nine index sets).
#' @export
simulate_ackermann <- function(seed = NULL, shift = c(0.75, 1), rho = 0.6) {
  if (!is.null(seed)) set.seed(seed)
  n0 <- 10
  n1 <- 10
  n <- n0 + n1
  y <- rep(c(0, 1), c(n0, n1))
  p <- 600
  X <- matrix(stats::rnorm(p * n), p, n)
  b1 <- 521:540
  b2 <- 541:560
  b6 <- 561:580
  b7 <- 581:600
  # set 1: one common factor per sample
  f <- stats::rnorm(n)
  X[b1, ] <- sqrt(rho) * matrix(f, 20, n, byrow = TRUE) + sqrt(1 - rho) * X[b1, ]
  # set 6: the down-regulated half loads on the factor with the opposite sign
  f <- stats::rnorm(n)
  sgn <- rep(c(1, -1), each = 10)
  X[b6, ] <- sqrt(rho) * outer(sgn, f) + sqrt(1 - rho) * X[b6, ]
  # shifts in class 1
  X[c(b1, b2), y == 1] <- X[c(b1, b2), y == 1] + shift[1]
  X[c(b6, b7), y == 1] <- X[c(b6, b7), y == 1] + shift[2] * c(sgn, sgn)
  bg <- 1:520
  sets <- list(
    set1 = b1,
    set2 = b2,
    set3 = sample(bg, 20),
    set4 = c(b1[1:10], sample(bg, 10)),
    set5 = c(b2[1:10], sample(bg, 10)),
    set6 = b6,
    set7 = b7,
    set8 = c(b6[c(1:5, 11:15)], sample(bg, 10)),
    set9 = c(b7[c(1:5, 11:15)], sample(bg, 10))
  )
  rownames(X) <- sprintf("g%03d", seq_len(p))
  colnames(X) <- sprintf("s%02d", seq_len(n))
  list(X = X, y = y, sets = sets)
}

#' Detection rates over simulated data sets
#'
#' The share of p-values at or below \code{alpha}, per set: the paper's
#' "proportion of significantly enriched gene sets" (Tables 2 to 6).
#'
#' @param p a matrix of p-values, one row per simulated data set and one
#'   column per gene set, or a list of data frames returned by
#'   \code{\link{gsea}}.
#' @param alpha significance level (0.05).
#' @return A named vector of detection rates.
#' @export
detection_rates <- function(p, alpha = 0.05) {
  if (is.list(p) && !is.data.frame(p)) {
    p <- do.call(rbind, lapply(p, function(d) stats::setNames(d$p, d$set)))
  }
  colMeans(as.matrix(p) <= alpha)
}

#' Monte Carlo tolerance for comparing two detection rates
#'
#' Each detection rate of the paper's Tables 2 to 6 is a share of 100
#' simulated data sets, so a rerun with other random numbers cannot give the
#' same value. Two rates are taken to agree when they differ by less than the
#' half-width of a two-sided test of equal proportions at level
#' \code{1 - conf}: \eqn{z \sqrt{2 \bar p (1 - \bar p) / n}}, with
#' \eqn{\bar p = (n p_1 + n p_2 + 1) / (2 n + 2)} (the +1 keeps the band open
#' at rates of 0 or 1), plus half a unit of the printed precision (0.005).
#'
#' @param p1,p2 the two rates (numbers or strings).
#' @param n replicates behind each rate (100).
#' @param conf confidence level (0.99).
#' @return The tolerance for each pair.
#' @export
rate_tolerance <- function(p1, p2, n = 100, conf = 0.99) {
  p1 <- as.numeric(p1)
  p2 <- as.numeric(p2)
  pbar <- (n * p1 + n * p2 + 1) / (2 * n + 2)
  stats::qnorm(1 - (1 - conf) / 2) * sqrt(2 * pbar * (1 - pbar) / n) + 0.005
}

# The B statistic of Zhang and Liu (2007), as printed in Jiang et al. (2009, Methods), and the
# conditional B statistic used by epiForest's hierarchical tests.
#
# For a set of k markers with case counts D and control counts U over the 3^k genotype
# combinations,
#   B = ln[ P_join(D) * P_mix(U) / P_mix(D + U) ],   P_mix = (P_ind + P_join) / 2,
# where P_join is the Dirichlet-multinomial marginal likelihood of the 3^k joint genotype counts
# and P_ind the product of the k single-marker Dirichlet-multinomial likelihoods (pseudo-counts
# 0.5). The paper prints P1/P1; the denominator is P0 (a typo). With equal mixture weights the
# weights cancel in B, so this is the paper's formula.
#
# The conditional B of the markers Omega given a subset omega already reported (t of k markers):
#   B(Omega | omega) = ln[ P_join(D_Omega) P_mix(U_Omega) /
#                         ( P_join(D_omega) P_mix(U_omega) P_mix(D_r + U_r) ) ],
# r = Omega minus omega: under H0 omega keeps its association and the rest is unlinked.
# For one marker P_ind = P_join, so P_mix = P.
#
# Null distribution: 2B - shift ~ chi-squared with 3^k - 3^t degrees of freedom, the shift from
# the Laplace (Stirling) expansion of each Dirichlet-multinomial term (see b_shift).

#' Log Dirichlet-multinomial marginal likelihood
#'
#' @param counts A matrix with one column per test and one row per cell (or a vector).
#' @param a Pseudo-count per cell.
#' @return One log marginal likelihood per column.
#' @export
dm_loglik <- function(counts, a = 0.5) {
  counts <- as.matrix(counts)
  J <- nrow(counts)
  N <- colSums(counts)
  lgamma(J * a) - lgamma(N + J * a) + colSums(lgamma(counts + a)) - J * lgamma(a)
}

.lse2 <- function(x, y) {
  m <- pmax(x, y)
  m + log(exp(x - m) + exp(y - m))
}

# Indicator matrices that sum a 3^k joint table (cells ordered with the first marker fastest)
# down to the margin of the markers in `keep` (positions 1..k); the result has 3^length(keep)
# rows, again with the first kept marker fastest.
.margin_matrix <- function(k, keep) {
  cells <- as.matrix(expand.grid(rep(list(0:2), k)))
  sub <- cells[, keep, drop = FALSE]
  code <- as.vector(sub %*% (3^(seq_along(keep) - 1))) + 1
  m <- matrix(0, 3^length(keep), 3^k)
  m[cbind(code, seq_len(3^k))] <- 1
  m
}

# log P_mix for tables with k markers: columns of a 3^k x T count matrix.
.log_pmix <- function(tab, k, a) {
  lj <- dm_loglik(tab, a)
  if (k == 1) return(lj)
  li <- 0
  for (i in seq_len(k)) li <- li + dm_loglik(.margin_matrix(k, i) %*% tab, a)
  .lse2(li, lj) - log(2)
}

#' B statistic from genotype-combination counts
#'
#' @param cases,controls Count matrices with \code{3^k} rows (genotype combinations, first marker
#'   varying fastest) and one column per test.
#' @param k Number of markers in each test.
#' @param given Positions (within the k markers) of the markers already reported; empty for the
#'   unconditional B.
#' @param a Dirichlet pseudo-count (the paper's alpha = beta = 0.5).
#' @return A data frame with \code{B}, \code{df}, \code{shift} and \code{p}.
#' @export
b_from_counts <- function(cases, controls, k, given = integer(0), a = 0.5) {
  cases <- as.matrix(cases)
  controls <- as.matrix(controls)
  stopifnot(nrow(cases) == 3^k, nrow(controls) == 3^k, ncol(cases) == ncol(controls))
  t <- length(given)
  if (t >= k) stop("conditioning on every marker leaves nothing to test")
  num <- dm_loglik(cases, a) + .log_pmix(controls, k, a)
  if (t == 0) {
    den <- .log_pmix(cases + controls, k, a)
  } else {
    rest <- setdiff(seq_len(k), given)
    mo <- .margin_matrix(k, given)
    mr <- .margin_matrix(k, rest)
    den <- dm_loglik(mo %*% cases, a) + .log_pmix(mo %*% controls, t, a) +
      .log_pmix(mr %*% (cases + controls), k - t, a)
  }
  B <- num - den
  nd <- colSums(cases)
  nu <- colSums(controls)
  shift <- b_shift(k, t, nd, nu)
  df <- 3^k - 3^t
  data.frame(B = B, df = df, shift = shift,
             p = stats::pchisq(pmax(2 * B - shift, 0), df, lower.tail = FALSE))
}

#' Shift of the asymptotic null distribution of 2B
#'
#' Under the null hypothesis, \code{2B - b_shift(k, t, Nd, Nu)} is asymptotically chi-squared with
#' \code{3^k - 3^t} degrees of freedom. The paper says only that 2B follows a "shifted" chi-squared
#' distribution; this shift comes from Stirling's expansion of each Dirichlet-multinomial term
#' (with pseudo-count 0.5 each log marginal likelihood is the maximised log-likelihood minus
#' \code{(J - 1)/2 * log(N / (2 pi))} plus \code{lgamma(J/2) - J/2 * log(pi)}), keeping the dominant
#' (independent-marker) term of each mixture.
#'
#' @param k Number of markers tested.
#' @param t Number of markers conditioned on (0 for the unconditional B).
#' @param nd,nu Numbers of cases and controls.
#' @export
b_shift <- function(k, t, nd, nu) {
  off <- function(J, N) -(J - 1) / 2 * log(N / (2 * pi)) + lgamma(J / 2) - J / 2 * log(pi)
  mixpen <- function(m) if (m >= 2) -log(2) else 0
  n <- nd + nu
  num <- off(3^k, nd) + k * off(3, nu) + mixpen(k)
  if (t == 0) {
    den <- k * off(3, n) + mixpen(k)
  } else {
    den <- off(3^t, nd) + t * off(3, nu) + mixpen(t) + (k - t) * off(3, n) + mixpen(k - t)
  }
  2 * (num - den)
}

# Genotype-combination codes (0 .. 3^k - 1, first marker fastest) for the columns `idx` of g.
.combo_code <- function(g, idx) {
  code <- 0L
  for (i in seq_along(idx)) code <- code + g[, idx[i]] * 3L^(i - 1L)
  code
}

# Count tables (3^k x T) of cases and controls for the marker sets in the rows of `sets`.
.count_tables <- function(g, status, sets) {
  sets <- as.matrix(sets)
  k <- ncol(sets)
  J <- 3L^k
  case <- status == 1
  cd <- matrix(0L, J, nrow(sets))
  cu <- matrix(0L, J, nrow(sets))
  for (s in seq_len(nrow(sets))) {
    code <- .combo_code(g, sets[s, ]) + 1L
    cd[, s] <- tabulate(code[case], J)
    cu[, s] <- tabulate(code[!case], J)
  }
  list(cases = cd, controls = cu)
}

#' B statistic test for sets of markers
#'
#' @param geno Integer matrix of genotypes (individuals in rows, 0, 1 or 2 minor alleles).
#' @param status 1 for cases, 0 for controls.
#' @param sets Matrix of column indices of \code{geno}, one row per test (k columns).
#' @param given Positions within each row to condition on (the same for every row).
#' @param a Dirichlet pseudo-count.
#' @return The data frame of \code{\link{b_from_counts}}.
#' @export
b_test <- function(geno, status, sets, given = integer(0), a = 0.5) {
  .check_geno(geno, status)
  sets <- as.matrix(sets)
  tab <- .count_tables(geno, status, sets)
  b_from_counts(tab$cases, tab$controls, ncol(sets), given, a)
}

.check_geno <- function(geno, status) {
  if (!is.matrix(geno)) stop("geno must be a matrix (individuals x SNPs)")
  if (anyNA(geno)) stop("geno has missing genotypes; impute or drop them first")
  if (!all(geno %in% 0:2)) stop("genotypes must be coded 0, 1 or 2")
  if (length(status) != nrow(geno)) stop("status must have one entry per row of geno")
  if (!all(status %in% 0:1)) stop("status must be 0 (control) or 1 (case)")
  if (length(unique(status)) < 2) stop("need both cases and controls")
  invisible(TRUE)
}

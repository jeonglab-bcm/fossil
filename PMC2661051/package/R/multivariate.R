#' Global and multivariate gene set statistics
#'
#' \code{global_stats} is the score statistic of Goeman et al.'s (2004)
#' globaltest for a 0/1 response without covariates: the sum over the set's
#' genes of the squared covariance between gene and label, divided by the sum
#' of the genes' variances (the normalisation of \code{globaltest::gt}). It
#' equals the \code{gt} statistic up to a factor that depends only on the
#' number of samples and the class sizes.
#'
#' \code{hotelling_stats} is Hotelling's T-squared written as
#' \eqn{t' R^{-1} t}, with \eqn{t} the two-sample t statistics of the set's
#' genes and \eqn{R} the Schafer-Strimmer shrinkage estimate
#' (\code{corpcor::cor.shrink}) of their correlation, computed from the data
#' centred within each class (\code{center = "within"}, the pooled
#' within-class correlation of the textbook statistic) or, with
#' \code{center = "overall"}, centred over all samples, so that the class
#' difference itself adds to the estimated correlation. With
#' \code{shrink = "covariance"} the statistic is instead
#' \eqn{d' (S (1/n_1 + 1/n_0))^{-1} d}{d' (S (1/n1 + 1/n0))^-1 d}, with \eqn{d} the differences of
#' class means and \eqn{S} the shrinkage covariance \code{corpcor::cov.shrink}.
#'
#' @param X expression matrix, genes in rows.
#' @param y a 0/1 label vector, or a matrix with one label vector per column.
#' @param sets a list of integer index vectors (rows of \code{X}).
#' @param center \code{"within"} or \code{"overall"} (Hotelling only).
#' @param shrink \code{"correlation"} or \code{"covariance"} (Hotelling only).
#' @return A matrix with one row per set and one column per label vector.
#' @export
global_stats <- function(X, y, sets) {
  X <- as.matrix(X)
  Y <- if (is.null(dim(y))) matrix(as.numeric(y), ncol = 1) else as.matrix(y) * 1
  n <- ncol(X)
  Yc <- sweep(Y, 2, colMeans(Y))
  C <- (X %*% Yc) / n
  v <- rowMeans((X - rowMeans(X))^2)
  num <- set_stats(C^2, sets, "mean")
  den <- set_stats(v, sets, "mean")[, 1]
  num / den
}

#' @rdname global_stats
#' @export
hotelling_stats <- function(X, y, sets, center = c("within", "overall"), shrink = c("correlation", "covariance")) {
  center <- match.arg(center)
  shrink <- match.arg(shrink)
  X <- as.matrix(X)
  Y <- if (is.null(dim(y))) matrix(as.numeric(y), ncol = 1) else as.matrix(y) * 1
  out <- matrix(NA_real_, length(sets), ncol(Y), dimnames = list(names(sets), colnames(Y)))
  for (b in seq_len(ncol(Y))) {
    yb <- Y[, b]
    tt <- gene_stats(X, yb, "t")
    g1 <- yb == 1
    for (k in seq_along(sets)) {
      idx <- sets[[k]]
      Z <- X[idx, , drop = FALSE]
      if (center == "within") {
        Z[, g1] <- Z[, g1, drop = FALSE] - rowMeans(Z[, g1, drop = FALSE])
        Z[, !g1] <- Z[, !g1, drop = FALSE] - rowMeans(Z[, !g1, drop = FALSE])
      }
      tk <- tt[idx]
      if (length(idx) == 1) {
        out[k, b] <- tk^2
      } else if (shrink == "correlation") {
        R <- unclass(corpcor::cor.shrink(t(Z), verbose = FALSE))
        out[k, b] <- sum(tk * solve(R, tk))
      } else {
        dk <- rowMeans(X[idx, g1, drop = FALSE]) - rowMeans(X[idx, !g1, drop = FALSE])
        S <- unclass(corpcor::cov.shrink(t(Z), verbose = FALSE)) * (1 / sum(g1) + 1 / sum(!g1))
        out[k, b] <- sum(dk * solve(S, dk))
      }
    }
  }
  out
}

#' globaltest p-values from the globaltest package
#'
#' The asymptotic p-value of \code{globaltest::gt} for each set, with the
#' labels as a two-level factor (a logistic model).
#'
#' @inheritParams global_stats
#' @return A vector of p-values, one per set.
#' @export
globaltest_pvalues <- function(X, y, sets) {
  if (!requireNamespace("globaltest", quietly = TRUE)) stop("the globaltest package is needed")
  X <- as.matrix(X)
  if (is.null(rownames(X))) rownames(X) <- paste0("g", seq_len(nrow(X)))
  resp <- factor(y)
  vapply(sets, function(idx) {
    A <- t(X[idx, , drop = FALSE])
    suppressMessages(globaltest::p.value(globaltest::gt(resp, A)))
  }, numeric(1))
}

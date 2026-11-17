#' Gene-level statistics
#'
#' Two-sample t statistic (equal variances), the moderated t statistic of
#' Smyth (2004) as computed by limma, or the Pearson correlation between each
#' gene and the 0/1 class label. Positive values mean higher expression in
#' class 1.
#'
#' @param X numeric matrix, genes in rows and samples in columns.
#' @param y class labels, a 0/1 vector of length \code{ncol(X)}, or a matrix
#'   with one 0/1 label vector per column (for example label permutations).
#' @param stat one of \code{"t"}, \code{"modt"} or \code{"corr"}.
#' @return A matrix with one row per gene and one column per label vector, or
#'   a vector when \code{y} is a vector. Attribute \code{df} holds the degrees
#'   of freedom of each column's reference t distribution (the residual
#'   degrees of freedom for \code{"t"}, limma's \code{df.total} (capped, as in limma, at the pooled residual degrees of freedom) for
#'   \code{"modt"}, \code{n - 2} for \code{"corr"}).
#' @export
gene_stats <- function(X, y, stat = c("t", "modt", "corr")) {
  stat <- match.arg(stat)
  X <- as.matrix(X)
  vec <- is.null(dim(y))
  Y <- if (vec) matrix(as.numeric(y), ncol = 1) else as.matrix(y) * 1
  n <- ncol(X)
  if (nrow(Y) != n) stop("y must have one label per column of X")
  if (any(Y != 0 & Y != 1)) stop("labels must be 0 or 1")
  n1 <- colSums(Y)
  n0 <- n - n1
  if (any(n1 < 2) || any(n0 < 2)) stop("each class needs at least two samples")
  S1 <- X %*% Y                      # sums in class 1
  St <- rowSums(X)
  S0 <- St - S1                      # sums in class 0
  Q1 <- (X * X) %*% Y
  Qt <- rowSums(X * X)
  Q0 <- Qt - Q1
  m1 <- sweep(S1, 2, n1, "/")
  m0 <- sweep(S0, 2, n0, "/")
  ss <- (Q1 - sweep(m1^2, 2, n1, "*")) + (Q0 - sweep(m0^2, 2, n0, "*"))
  ss[ss < 0] <- 0
  dfres <- n - 2
  d <- m1 - m0
  scale <- sqrt(1 / n1 + 1 / n0)
  if (stat == "corr") {
    # Pearson correlation of each gene with the 0/1 label
    sxx <- Qt - St^2 / n
    ybar <- n1 / n
    sxy <- S1 - outer(St, ybar)
    syy <- n1 - n1^2 / n
    out <- sxy / sqrt(outer(sxx, syy))
    df <- rep(dfres, ncol(Y))
  } else {
    s2 <- ss / dfres
    if (stat == "t") {
      out <- d / sweep(sqrt(s2), 2, scale, "*")
      df <- rep(dfres, ncol(Y))
    } else {
      out <- d
      df <- numeric(ncol(Y))
      for (b in seq_len(ncol(Y))) {
        sv <- limma::squeezeVar(s2[, b], df = dfres)
        out[, b] <- d[, b] / (sqrt(sv$var.post) * scale[b])
        df[b] <- min(dfres + sv$df.prior, dfres * nrow(X))
      }
    }
  }
  dimnames(out) <- list(rownames(X), colnames(Y))
  if (vec) out <- stats::setNames(out[, 1], rownames(X))
  attr(out, "df") <- df
  out
}

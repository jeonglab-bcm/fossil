#' Gene set statistics
#'
#' The fourth module: a statistic that summarises the (transformed)
#' gene-level statistics of each gene set. Larger values always mean more
#' enrichment.
#'
#' \describe{
#'   \item{mean, median}{of the scores in the set.}
#'   \item{maxmean}{Efron and Tibshirani (2007): the larger of the means of
#'     the positive parts and of the negative parts of the scores. On
#'     non-negative scores (squared statistics) it equals the mean.}
#'   \item{es}{the weighted (p = 1) GSEA enrichment score of Subramanian et
#'     al. (2005): genes ranked by decreasing score, set members weighted by
#'     the absolute score; the signed maximum deviation of the running sum.}
#'   \item{wilcoxon}{the Wilcoxon rank-sum statistic: the sum of the ranks of
#'     the set's scores among all genes.}
#'   \item{condfdr}{Efron's (2008) conditional local FDR. The probability
#'     \eqn{\pi_S(z)} that a gene with score \eqn{z} belongs to the set is
#'     estimated by a linear logistic regression of set membership on the
#'     score over all genes; the conditional fdr of each gene of the set is
#'     \eqn{fdr_S(z) = fdr(z) (m/N) / \pi_S(z)} (capped at 1), with
#'     \eqn{fdr(z)} the unconditional local fdr given in \code{fdr} and
#'     \eqn{m/N} the set's share of the genes. The statistic is the mean of
#'     \eqn{1 - fdr_S} over the set.}
#'   \item{condslope}{the slope of that logistic regression alone. With a
#'     fixed score vector it is a monotone function of the set's score sum, so
#'     it ranks random sets of one size exactly as the mean does.}
#' }
#'
#' @param S scores: a vector over genes, or a matrix with one column per
#'   label vector.
#' @param sets a list of integer index vectors (rows of \code{S}).
#' @param stat the gene set statistic.
#' @param fdr for \code{condfdr}: the unconditional local fdr of each gene,
#'   with the shape of \code{S}.
#' @return A matrix with one row per set and one column per column of
#'   \code{S}.
#' @export
set_stats <- function(S, sets, stat = c("mean", "median", "maxmean", "es", "wilcoxon", "condfdr", "condslope"),
                      fdr = NULL) {
  stat <- match.arg(stat)
  S <- as.matrix(S)
  if (stat == "condfdr") {
    if (is.null(fdr)) stop("condfdr needs the local fdr of each gene")
    fdr <- as.matrix(fdr)
    if (!all(dim(fdr) == dim(S))) stop("fdr must have the shape of S")
  }
  N <- nrow(S)
  sets <- lapply(sets, as.integer)
  sizes <- lengths(sets)
  if (any(sizes < 1) || any(sizes >= N)) stop("each set needs between 1 and N - 1 genes")
  out <- matrix(NA_real_, length(sets), ncol(S), dimnames = list(names(sets), colnames(S)))
  groups <- split(seq_along(sets), sizes)
  for (g in groups) {
    m <- sizes[g[1]]
    I <- matrix(unlist(sets[g], use.names = FALSE), nrow = m)
    for (b in seq_len(ncol(S))) out[g, b] <- set_stat_group(S[, b], I, stat, if (stat == "condfdr") fdr[, b])
  }
  out
}

# One score vector s, sets of equal size as the columns of index matrix I.
set_stat_group <- function(s, I, stat, f = NULL) {
  m <- nrow(I)
  N <- length(s)
  switch(stat,
    mean = colMeans(matrix(s[I], m)),
    median = apply(matrix(s[I], m), 2, stats::median),
    maxmean = {
      V <- matrix(s[I], m)
      pmax(colMeans(pmax(V, 0)), colMeans(pmax(-V, 0)))
    },
    wilcoxon = {
      r <- rank(s, ties.method = "average")
      colSums(matrix(r[I], m))
    },
    es = es_group(s, I),
    condslope = logistic_fit(s, I)$slope,
    condfdr = {
      fit <- logistic_fit(s, I)
      Z <- matrix(fit$z[I], m)
      pi_s <- stats::plogis(sweep(sweep(Z, 2, fit$b, "*"), 2, fit$a, "+"))
      fS <- pmin(matrix(f[I], m) * (m / N) / pi_s, 1)
      colMeans(1 - fS)
    }
  )
}

es_group <- function(s, I) {
  N <- length(s)
  m <- nrow(I)
  o <- order(s, decreasing = TRUE)
  pos <- integer(N)
  pos[o] <- seq_len(N)
  P <- matrix(pos[I], m)
  W <- matrix(abs(s[I]), m)
  oo <- apply(P, 2, order)
  if (m == 1) oo <- matrix(oo, 1)
  idx <- cbind(as.vector(oo), rep(seq_len(ncol(P)), each = m))
  P <- matrix(P[idx], m)
  W <- matrix(W[idx], m)
  NS <- colSums(W)
  unweighted <- NS <= 0
  if (any(unweighted)) {
    W[, unweighted] <- 1
    NS[unweighted] <- m
  }
  cw <- apply(W, 2, cumsum)
  if (m == 1) cw <- matrix(cw, 1)
  hit <- sweep(cw, 2, NS, "/")
  hit_before <- rbind(0, hit[-m, , drop = FALSE])
  miss <- (P - seq_len(m)) / (N - m)
  dplus <- apply(hit - miss, 2, max)
  dminus <- apply(hit_before - miss, 2, min)
  dplus <- pmax(dplus, 0)
  dminus <- pmin(dminus, 0)
  ifelse(dplus >= -dminus, dplus, dminus)
}

# Logistic regression of membership (I) on the score s, for each column of I.
# Newton-Raphson with step halving on the log-likelihood, on all sets at once, on the
# standardised score z. Under (near) separation the slope grows until the likelihood stops
# improving; it is capped at |b| = 50 on the standardised scale.
logistic_fit <- function(s, I, maxit = 100, tol = 1e-10, bmax = 50) {
  N <- length(s)
  m <- nrow(I)
  K <- ncol(I)
  sd_s <- stats::sd(s)
  if (!is.finite(sd_s) || sd_s == 0) {
    return(list(a = rep(stats::qlogis(m / N), K), b = rep(0, K), z = rep(0, N), slope = rep(0, K)))
  }
  z <- (s - mean(s)) / sd_s
  Y <- matrix(0, N, K)
  Y[cbind(as.vector(I), rep(seq_len(K), each = m))] <- 1
  sz <- crossprod(z, Y)[1, ]
  loglik <- function(a, b, k = seq_len(K)) {
    eta <- outer(z, b) + rep(a, each = N)
    sz[k] * b + m * a - colSums(pmax(eta, 0) + log1p(exp(-abs(eta))))
  }
  a <- rep(stats::qlogis(m / N), K)
  b <- rep(0, K)
  ll <- loglik(a, b)
  active <- rep(TRUE, K)
  for (it in seq_len(maxit)) {
    k <- which(active)
    if (!length(k)) break
    eta <- outer(z, b[k]) + rep(a[k], each = N)
    P <- stats::plogis(eta)
    Wt <- P * (1 - P)
    ua <- m - colSums(P)
    ub <- sz[k] - crossprod(z, P)[1, ]
    iaa <- colSums(Wt)
    iab <- crossprod(z, Wt)[1, ]
    ibb <- crossprod(z^2, Wt)[1, ]
    det <- iaa * ibb - iab^2
    da <- (ibb * ua - iab * ub) / det
    db <- (iaa * ub - iab * ua) / det
    bad <- !is.finite(da) | !is.finite(db)
    da[bad] <- 0
    db[bad] <- 0
    step <- rep(1, length(k))
    for (h in 1:40) {
      bn <- pmax(pmin(b[k] + step * db, bmax), -bmax)
      an <- a[k] + step * da
      lln <- loglik(an, bn, k)
      worse <- !is.finite(lln) | lln < ll[k] - 1e-12
      if (!any(worse)) break
      step[worse] <- step[worse] / 2
    }
    worse <- !is.finite(lln) | lln < ll[k] - 1e-12
    an[worse] <- a[k][worse]
    bn[worse] <- b[k][worse]
    lln[worse] <- ll[k][worse]
    a[k] <- an
    b[k] <- bn
    ll[k] <- lln
    active[k] <- pmax(abs(ua), abs(ub)) > tol & !worse & !bad & abs(bn) < bmax
  }
  list(a = a, b = b, z = z, slope = b / sd_s)
}

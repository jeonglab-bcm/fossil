#' Modular gene set enrichment analysis
#'
#' Runs one combination of the modules of Ackermann and Strimmer (2009):
#' gene-level statistic, transformation, gene set statistic and significance
#' assessment. The global and multivariate tracks (globaltest and Hotelling's
#' T-squared with a shrinkage correlation) are chosen with \code{setstat}
#' and then ignore \code{gene} and \code{transform}.
#'
#' Significance (all tests are one-sided: large statistics are enriched):
#' \describe{
#'   \item{resampling}{gene sampling, the competitive null hypothesis Q1:
#'     \code{B} random gene sets of the same size.}
#'   \item{permutation}{sample label permutation, the self-contained null
#'     hypothesis Q2: \code{B} permutations of \code{y}.}
#'   \item{restandardization}{Efron and Tibshirani (2007): the permutation
#'     statistics standardised by their own mean and standard deviation, then
#'     rescaled with those of the gene sampling statistics.}
#'   \item{parametric}{a null distribution in closed form. Mean of squared
#'     statistics: \eqn{m \cdot \bar s \sim \chi^2_m}{m * mean ~ chisq(m)} (independent
#'     standard normal statistics); mean of untransformed statistics:
#'     \eqn{\sqrt{m}\,\bar s \sim N(0, 1)}{sqrt(m) * mean ~ N(0, 1)}; Wilcoxon: the normal approximation of
#'     the rank-sum test; globaltest: the package's asymptotic p-value.}
#' }
#'
#' @param X expression matrix, genes in rows and samples in columns.
#' @param y 0/1 class labels, one per column of \code{X}.
#' @param sets named list of gene sets, each an integer index vector into
#'   the rows of \code{X} or a character vector of row names.
#' @param gene gene-level statistic, see \code{\link{gene_stats}}.
#' @param transform transformation, see \code{\link{transform_stats}}.
#' @param setstat gene set statistic, see \code{\link{set_stats}} (for
#'   \code{condfdr} the unconditional local fdr comes from \code{fdrtool} on
#'   the untransformed gene-level statistic), or
#'   \code{"globaltest"} or \code{"hotelling"}.
#' @param method significance assessment.
#' @param B number of random gene sets and of label permutations.
#' @param seed optional random seed.
#' @param perms optional matrix of permuted labels (one per column) to use
#'   instead of drawing \code{B} permutations.
#' @param rsets optional list of random gene sets per set size, as returned
#'   by \code{\link{random_sets}}, to use instead of drawing them.
#' @param hotelling_center for \code{setstat = "hotelling"}: how the data are
#'   centred before the correlation is estimated, see
#'   \code{\link{hotelling_stats}}.
#' @param hotelling_shrink for \code{setstat = "hotelling"}: shrink the
#'   correlation (the default) or the covariance matrix.
#' @param ... passed to \code{\link{transform_stats}}.
#' @return A data frame with one row per set: \code{set}, \code{size},
#'   \code{statistic} and \code{p}.
#' @export
gsea <- function(X, y, sets, gene = c("modt", "t", "corr"),
                 transform = c("square", "none", "ranksq", "abs", "binary", "lfdr"),
                 setstat = c("mean", "median", "maxmean", "es", "wilcoxon", "condfdr", "condslope", "globaltest", "hotelling"),
                 method = c("permutation", "resampling", "restandardization", "parametric"),
                 B = 1000, seed = NULL, perms = NULL, rsets = NULL, hotelling_center = "within",
                 hotelling_shrink = "correlation", ...) {
  gene <- match.arg(gene)
  transform <- match.arg(transform)
  setstat <- match.arg(setstat)
  method <- match.arg(method)
  X <- as.matrix(X)
  y <- as.numeric(y)
  if (length(y) != ncol(X)) stop("y needs one label per column of X")
  sets <- index_sets(sets, X)
  if (!is.null(seed)) set.seed(seed)
  N <- nrow(X)
  sizes <- lengths(sets)

  statfun <- function(Y, sets) {
    if (setstat == "globaltest") return(global_stats(X, Y, sets))
    if (setstat == "hotelling") return(hotelling_stats(X, Y, sets, center = hotelling_center, shrink = hotelling_shrink))
    g <- gene_stats(X, Y, gene)
    s <- transform_stats(g, transform, stat = gene, n = ncol(X), ...)
    f <- if (setstat == "condfdr") 1 - transform_stats(g, "lfdr", stat = gene) else NULL
    set_stats(s, sets, setstat, fdr = f)
  }
  obs <- statfun(y, sets)[, 1]

  if (method == "parametric") {
    p <- parametric_p(X, y, sets, obs, gene, transform, setstat, N)
    return(data.frame(set = names(sets), size = sizes, statistic = obs, p = p, row.names = NULL))
  }

  null_resampling <- function() {
    if (is.null(rsets)) rsets <- random_sets(N, unique(sizes), B)
    res <- list()
    for (m in unique(sizes)) {
      key <- as.character(m)
      I <- rsets[[key]]
      if (is.null(I)) stop("rsets has no random sets of size ", m)
      res[[key]] <- statfun(y, lapply(seq_len(ncol(I)), function(j) I[, j]))[, 1]
    }
    res
  }
  null_permutation <- function() {
    if (is.null(perms)) perms <- permute_labels(y, B)
    statfun(perms, sets)
  }

  p <- switch(method,
    resampling = {
      R <- null_resampling()
      vapply(seq_along(sets), function(k) mean(R[[as.character(sizes[k])]] >= obs[k]), numeric(1))
    },
    permutation = {
      P <- null_permutation()
      rowMeans(P >= obs)
    },
    restandardization = {
      R <- null_resampling()
      P <- null_permutation()
      vapply(seq_along(sets), function(k) {
        r <- R[[as.character(sizes[k])]]
        pk <- P[k, ]
        sdp <- stats::sd(pk)
        if (!is.finite(sdp) || sdp == 0) return(mean(r >= obs[k]))
        rs <- mean(r) + stats::sd(r) * (pk - mean(pk)) / sdp
        mean(rs >= obs[k])
      }, numeric(1))
    }
  )
  data.frame(set = names(sets), size = sizes, statistic = obs, p = p, row.names = NULL)
}

#' Random gene sets and label permutations
#'
#' @param N number of genes.
#' @param sizes set sizes.
#' @param B number of random sets per size, or of permutations.
#' @return \code{random_sets}: a list named by size, each an index matrix
#'   with one random set per column. \code{permute_labels}: a matrix with one
#'   permutation of \code{y} per column.
#' @export
random_sets <- function(N, sizes, B) {
  out <- lapply(sizes, function(m) vapply(seq_len(B), function(i) sample.int(N, m), integer(m)))
  out <- lapply(out, function(I) if (is.null(dim(I))) matrix(I, nrow = 1) else I)
  stats::setNames(out, as.character(sizes))
}

#' @rdname random_sets
#' @param y labels to permute.
#' @export
permute_labels <- function(y, B) {
  vapply(seq_len(B), function(i) sample(y), numeric(length(y)))
}

index_sets <- function(sets, X) {
  if (is.null(names(sets))) names(sets) <- paste0("set", seq_along(sets))
  lapply(sets, function(s) {
    if (is.character(s)) {
      idx <- match(s, rownames(X))
      idx <- unique(idx[!is.na(idx)])
    } else {
      idx <- unique(as.integer(s))
    }
    if (length(idx) < 1) stop("a gene set has no genes in X")
    idx
  })
}

parametric_p <- function(X, y, sets, obs, gene, transform, setstat, N) {
  m <- lengths(sets)
  if (setstat == "globaltest") return(globaltest_pvalues(X, y, sets))
  if (setstat == "mean" && transform == "square") {
    return(stats::pchisq(m * obs, df = m, lower.tail = FALSE))
  }
  if (setstat == "mean" && transform == "none") {
    return(stats::pnorm(sqrt(m) * obs, lower.tail = FALSE))
  }
  if (setstat == "wilcoxon") {
    mu <- m * (N + 1) / 2
    sdw <- sqrt(m * (N - m) * (N + 1) / 12)
    return(stats::pnorm((obs - mu) / sdw, lower.tail = FALSE))
  }
  stop("no parametric null for ", setstat, " of ", transform, " statistics")
}

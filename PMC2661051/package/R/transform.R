#' Transform gene-level statistics
#'
#' The second module of the framework: an optional transformation of the
#' gene-level statistics before they are summarised over a gene set.
#'
#' \describe{
#'   \item{none}{the statistics as they are.}
#'   \item{square}{squared values.}
#'   \item{ranksq}{ranks of the squared values (1 = smallest), the paper's
#'     "rank squared".}
#'   \item{abs}{absolute values.}
#'   \item{binary}{1 for genes called differentially expressed, 0 otherwise.
#'     By default a gene is called when its two-sided p-value is at most
#'     \code{binary_cutoff} (0.05): from the t distribution with the
#'     statistic's degrees of freedom for \code{t} and \code{modt}, from
#'     Fisher's z transformation for \code{corr}. With
#'     \code{binary_rule = "lfdr"} a gene is called when its local false
#'     discovery rate (\code{fdrtool}) is at most \code{binary_cutoff}.}
#'   \item{lfdr}{one minus the local false discovery rate estimated with
#'     \code{fdrtool} (the posterior probability of differential expression),
#'     so that, as for the other transformations, large means interesting.}
#' }
#'
#' @param s gene-level statistics: a vector, or a matrix with one column per
#'   label vector as returned by \code{\link{gene_stats}}.
#' @param how the transformation.
#' @param stat the gene-level statistic \code{s} holds (\code{"t"},
#'   \code{"modt"} or \code{"corr"}); used by \code{binary} and \code{lfdr}.
#' @param binary_rule \code{"pvalue"} or \code{"lfdr"}.
#' @param binary_cutoff cutoff for \code{binary}.
#' @param n number of samples (for \code{binary_rule = "pvalue"} with
#'   \code{stat = "corr"}).
#' @return Transformed statistics with the shape of \code{s}.
#' @export
transform_stats <- function(s, how = c("none", "square", "ranksq", "abs", "binary", "lfdr"),
                            stat = c("modt", "t", "corr"), binary_rule = c("pvalue", "lfdr"),
                            binary_cutoff = 0.05, n = NULL) {
  how <- match.arg(how)
  stat <- match.arg(stat)
  binary_rule <- match.arg(binary_rule)
  df <- attr(s, "df")
  vec <- is.null(dim(s))
  S <- if (vec) matrix(s, ncol = 1) else unclass(s)
  attr(S, "df") <- NULL
  out <- switch(how,
    none = S,
    square = S^2,
    abs = abs(S),
    ranksq = apply(S^2, 2, rank, ties.method = "average"),
    lfdr = 1 - apply(S, 2, lfdr_of, stat = stat),
    binary = {
      if (binary_rule == "lfdr") {
        (apply(S, 2, lfdr_of, stat = stat) <= binary_cutoff) * 1
      } else {
        P <- S
        for (b in seq_len(ncol(S))) P[, b] <- pvalue_of(S[, b], stat, df[b], n)
        (P <= binary_cutoff) * 1
      }
    }
  )
  dim(out) <- dim(S)
  dimnames(out) <- dimnames(S)
  if (vec) out <- stats::setNames(out[, 1], names(s))
  out
}

lfdr_of <- function(z, stat) {
  st <- if (stat == "corr") "correlation" else "normal"
  r <- fdrtool::fdrtool(as.numeric(z), statistic = st, plot = FALSE, verbose = FALSE)
  r$lfdr
}

pvalue_of <- function(z, stat, df, n) {
  if (stat == "corr") {
    if (is.null(n)) stop("n is needed for p-values of correlations")
    2 * stats::pnorm(-abs(atanh(z)) * sqrt(n - 3))
  } else {
    2 * stats::pt(-abs(z), df = df)
  }
}

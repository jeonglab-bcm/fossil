# Vandesompele et al. (2002) geNorm M-values, for comparison with Model 1a and Model 2.

#' geNorm M-values
#'
#' M_j is the mean, over the other genes k, of the standard deviation (over samples) of
#' log(y_j / y_k). Natural logarithms, as in Szabo et al.; geNorm itself uses log2, which
#' scales every M by the same factor and leaves the ranking unchanged.
#'
#' @param expr Expression matrix, samples in rows and genes in columns.
#' @return Named vector of M-values.
#' @export
m_values <- function(expr) {
  L <- log(check_expr(expr))
  g <- colnames(L)
  stats::setNames(vapply(g, function(j) mean(vapply(setdiff(g, j), function(k) stats::sd(L[, j] - L[, k]),
                                                   numeric(1))), numeric(1)), g)
}

#' geNorm stepwise ranking
#'
#' Removes the gene with the largest M-value, recomputes the M-values of the rest, and repeats
#' until two genes remain. The last two are the unordered best pair.
#'
#' @param expr Expression matrix, samples in rows and genes in columns.
#' @return Data frame with `gene`, `rank` (1 = most stable; the best pair both get 1.5) and `m`
#'   (the gene's M-value at the step it was removed, or the final pair's M-value), ordered by
#'   rank.
#' @export
genorm <- function(expr) {
  expr <- check_expr(expr)
  genes <- colnames(expr); out <- list()
  while (length(genes) > 2) {
    m <- m_values(expr[, genes, drop = FALSE])
    worst <- names(which.max(m))
    out[[length(out) + 1]] <- data.frame(gene = worst, rank = length(genes), m = max(m))
    genes <- setdiff(genes, worst)
  }
  m <- m_values(expr[, genes, drop = FALSE])
  out[[length(out) + 1]] <- data.frame(gene = genes, rank = 1.5, m = unname(m))
  res <- do.call(rbind, rev(out))
  res <- res[order(res$rank, res$gene), ]
  rownames(res) <- NULL
  res
}

#' geNorm ranks averaged over tissue types
#'
#' Szabo et al. rank the genes by geNorm within each tissue type (the unordered best pair gets
#' rank 1.5) and average the ranks over the tissue types.
#'
#' @param expr Expression matrix, samples in rows and genes in columns.
#' @param tissue Tissue type of each sample.
#' @return Named vector of mean ranks, sorted.
#' @export
genorm_mean_rank <- function(expr, tissue) {
  expr <- check_expr(expr)
  tissue <- factor(tissue)
  r <- sapply(levels(tissue), function(k) {
    g <- genorm(expr[tissue == k, , drop = FALSE])
    stats::setNames(g$rank, g$gene)[colnames(expr)]
  })
  sort(rowMeans(r))
}

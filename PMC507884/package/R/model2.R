# Model 2 of Szabo et al. (2004): several tissue types.
#
#   log y_i(k)j = mu + C_k + T_i(k) + G_j + (CG)_kj + e_i(k)j,  e ~ N(0, varsigma_k^2 sigma_j^2)
#
# with sum-to-zero constraints on every effect and varsigma_1 = 1 (the first tissue type).
# (CG)_kj is the bias of gene j in tissue type k; varsigma_k^2 sigma_j^2 its variance.

#' Fit Model 2 (several tissue types)
#'
#' Sample effects are fixed (they absorb C_k); the tissue-by-gene effects (CG)_kj are coded with
#' sum-to-zero contrasts. Fitted by REML with nlme::gls.
#'
#' @param expr Expression matrix, samples in rows and genes in columns.
#' @param tissue Tissue type of each sample; its first level is the reference (varsigma = 1).
#' @param variance Error variance structure. `"gene_tissue"` (Model 2: sigma_j times varsigma_k),
#'   or the competitors the paper compared it with by BIC: `"common"` (one variance), `"gene"`
#'   (equal for tissue types), `"tissue"` (equal for genes), `"unstructured"` (one variance per
#'   gene and tissue type) and `"exchangeable"` (Model 2's variance with a common correlation
#'   between the genes of a sample).
#' @param method `"REML"` or `"ML"`.
#' @return An `nlme::gls` fit.
#' @export
fit_model2 <- function(expr, tissue, variance = c("gene_tissue", "common", "gene", "tissue",
                                                  "unstructured", "exchangeable"),
                       method = "REML") {
  variance <- match.arg(variance)
  tissue <- factor(tissue)
  if (nlevels(tissue) < 2) stop("Model 2 needs at least two tissue types")
  d <- as_long(expr, tissue)
  Ct <- stats::contr.sum(nlevels(d$tissue))[as.integer(d$tissue), , drop = FALSE]
  Cg <- stats::contr.sum(nlevels(d$gene))[as.integer(d$gene), , drop = FALSE]
  d$TG <- do.call(cbind, lapply(seq_len(ncol(Ct)), function(a) Cg * Ct[, a]))
  d$cell <- interaction(d$gene, d$tissue, drop = TRUE)
  vf <- switch(variance,
               gene_tissue = , exchangeable = nlme::varComb(nlme::varIdent(form = ~ 1 | gene),
                                                            nlme::varIdent(form = ~ 1 | tissue)),
               common = NULL,
               gene = nlme::varIdent(form = ~ 1 | gene),
               tissue = nlme::varIdent(form = ~ 1 | tissue),
               unstructured = nlme::varIdent(form = ~ 1 | cell))
  args <- list(model = y ~ sample + gene + TG, data = d, method = method)
  if (!is.null(vf)) args$weights <- vf
  if (variance == "exchangeable") args$correlation <- nlme::corCompSymm(form = ~ 1 | sample)
  do.call(nlme::gls, args)
}

#' Components of a Model 2 fit
#'
#' @param fit A [fit_model2()] fit with `variance = "gene_tissue"`.
#' @return List with `sigma` (gene standard deviations sigma_j, named), `varsigma` (tissue
#'   multipliers, the first tissue type 1, named), `bias` (matrix of (CG)_kj, tissue types in rows,
#'   genes in columns) and `bic`.
#' @export
model2_components <- function(fit) {
  d <- nlme::getData(fit)
  genes <- levels(d$gene); tis <- levels(d$tissue)
  b <- stats::coef(fit)
  B <- matrix(b[grep("^TG", names(b))], nrow = length(genes) - 1)
  CG <- stats::contr.sum(length(tis)) %*% t(B) %*% t(stats::contr.sum(length(genes)))
  dimnames(CG) <- list(tis, genes)
  r <- variance_ratios(fit)
  if (is.null(r$gene) || is.null(r$tissue)) stop("fit must use variance = \"gene_tissue\"")
  vt <- r$tissue / r$tissue[1]
  list(sigma = stats::setNames(fit$sigma * unname(r$gene) * unname(r$tissue[1]), genes),
       varsigma = stats::setNames(unname(vt), tis), bias = CG, bic = stats::BIC(fit))
}

#' Bias, variance and mean squared error of each gene by tissue type
#'
#' The quantities of the paper's Figure 3: bias (CG)_kj, variance varsigma_k^2 sigma_j^2, their
#' MSE, and the MSE signed by the bias.
#'
#' @param comp [model2_components()] output, or a list with `sigma`, `varsigma` and `bias`.
#' @return Data frame with `gene`, `tissue`, `bias`, `bias2`, `variance`, `mse`, `signed_mse`.
#' @export
gene_mse <- function(comp) {
  CG <- comp$bias
  out <- expand.grid(tissue = rownames(CG), gene = colnames(CG), stringsAsFactors = FALSE)[, 2:1]
  out$bias <- CG[cbind(out$tissue, out$gene)]
  out$bias2 <- out$bias^2
  out$variance <- comp$varsigma[out$tissue]^2 * comp$sigma[out$gene]^2
  out$mse <- out$bias2 + out$variance
  out$signed_mse <- sign(out$bias) * out$mse
  rownames(out) <- NULL
  out
}

#' Mean squared error of a gene set
#'
#' For the log-average of the genes in S, in tissue type k: variance
#' varsigma_k^2 sum_{j in S} sigma_j^2 / |S|^2, plus the squared bias. The paper describes the
#' bias in words only. `bias = "sum"` (sum over S of (CG)_kj) reproduces its Table 4 and its
#' ACTB plus TBP example; `bias = "mean"` (the mean, the bias of a log-average) does not.
#'
#' @inheritParams gene_mse
#' @param set Gene names.
#' @param bias `"sum"` or `"mean"`.
#' @return The largest MSE over tissue types, with the per-tissue MSEs as attribute `by_tissue`.
#' @export
set_mse <- function(comp, set, bias = c("sum", "mean")) {
  bias <- match.arg(bias)
  if (!all(set %in% names(comp$sigma))) stop("unknown genes: ", paste(setdiff(set, names(comp$sigma)), collapse = ", "))
  b <- rowSums(comp$bias[, set, drop = FALSE])
  if (bias == "mean") b <- b / length(set)
  v <- comp$varsigma^2 * sum(comp$sigma[set]^2) / length(set)^2
  m <- b^2 + v[names(b)]
  structure(max(m), by_tissue = m)
}

#' Minimax-MSE gene sets
#'
#' Exhaustive search over all non-empty gene sets for the one whose largest MSE over tissue types
#' ([set_mse()]) is smallest, for each size.
#'
#' @inheritParams set_mse
#' @param nested `TRUE` (the paper's Table 4, "maximum number of members"): the best set with at
#'   most `size` genes. `FALSE`: exactly `size` genes.
#' @return Data frame with `size`, `genes` (comma-separated, in the order of `comp$sigma`) and
#'   `mse`.
#' @export
minimax_sets <- function(comp, bias = c("sum", "mean"), nested = TRUE) {
  bias <- match.arg(bias)
  g <- names(comp$sigma)
  best <- lapply(seq_along(g), function(k) {
    cs <- utils::combn(g, k, simplify = FALSE)
    v <- vapply(cs, function(S) as.numeric(set_mse(comp, S, bias)), numeric(1))
    i <- which.min(v)
    list(set = cs[[i]], mse = v[i])
  })
  if (nested) for (k in seq_along(best)[-1]) if (best[[k - 1]]$mse < best[[k]]$mse) best[[k]] <- best[[k - 1]]
  data.frame(size = seq_along(g), genes = vapply(best, function(b) paste(b$set, collapse = ","), ""),
             mse = vapply(best, `[[`, 0, "mse"))
}

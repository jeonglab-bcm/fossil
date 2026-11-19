# Model 1 of Szabo et al. (2004): one tissue type.
#
#   log y_ij = mu + T_i + G_j + e_ij,   e_ij ~ N(0, sigma_j^2) independent   (Model 1a)
#
# Model 1b has one common variance; Model 1c adds an exchangeable correlation between the genes of
# a sample. All are fitted by REML with nlme::gls, as the paper did.

#' Long table of log expression
#'
#' @param expr Numeric matrix or data frame of expression levels (relative copy numbers), samples
#'   in rows and genes in columns. All values must be positive.
#' @param tissue Optional factor of tissue types, one per sample (row).
#' @return A data frame with columns `sample`, `gene`, `y` (natural log of the expression) and,
#'   when given, `tissue`, one row per measurement, ordered by gene and then sample.
#' @export
as_long <- function(expr, tissue = NULL) {
  expr <- check_expr(expr)
  n <- nrow(expr); g <- ncol(expr)
  out <- data.frame(sample = factor(rep(rownames(expr), g), levels = rownames(expr)),
                    gene = factor(rep(colnames(expr), each = n), levels = colnames(expr)),
                    y = log(as.vector(expr)))
  if (!is.null(tissue)) {
    if (length(tissue) != n) stop("tissue must have one entry per sample (row of expr)")
    out$tissue <- rep(factor(tissue), g)
  }
  out
}

check_expr <- function(expr) {
  expr <- as.matrix(expr)
  if (!is.numeric(expr)) stop("expr must be numeric")
  if (anyNA(expr)) stop("expr has missing values")
  if (any(expr <= 0)) stop("expr must be positive (expression levels, not logs)")
  if (ncol(expr) < 2) stop("expr needs at least two genes (columns)")
  if (nrow(expr) < 3) stop("expr needs at least three samples (rows)")
  if (is.null(colnames(expr))) colnames(expr) <- paste0("gene", seq_len(ncol(expr)))
  if (is.null(rownames(expr))) rownames(expr) <- paste0("s", seq_len(nrow(expr)))
  if (anyDuplicated(colnames(expr))) stop("gene names must be unique")
  if (anyDuplicated(rownames(expr))) stop("sample names must be unique")
  expr
}

#' Fit Model 1 (one tissue type)
#'
#' @param expr Expression matrix, samples in rows and genes in columns (see [as_long()]).
#' @param variance `"gene"` (Model 1a, one error variance per gene), `"common"` (Model 1b,
#'   classical two-way ANOVA) or `"exchangeable"` (Model 1c: one variance per gene and a common
#'   correlation between the errors of the genes of a sample).
#' @param method `"REML"` (the paper's choice, and nlme's default) or `"ML"`.
#' @return An `nlme::gls` fit.
#' @export
fit_model1 <- function(expr, variance = c("gene", "common", "exchangeable"), method = "REML") {
  variance <- match.arg(variance)
  d <- as_long(expr)
  w <- if (variance == "common") NULL else nlme::varIdent(form = ~ 1 | gene)
  cs <- if (variance == "exchangeable") nlme::corCompSymm(form = ~ 1 | sample) else NULL
  # gls evaluates weights and correlation in the data's frame; pass them through do.call.
  args <- list(model = y ~ sample + gene, data = d, method = method)
  if (!is.null(w)) args$weights <- w
  if (!is.null(cs)) args$correlation <- cs
  do.call(nlme::gls, args)
}

#' Error standard deviation of each gene
#'
#' @param fit A Model 1 or Model 2 fit ([fit_model1()], [fit_model2()]).
#' @return Named vector of the error standard deviations sigma_j, in the genes' order. For a
#'   Model 2 fit, the standard deviation in the reference (first) tissue type.
#' @export
gene_sd <- function(fit) {
  genes <- levels(nlme::getData(fit)$gene)
  vs <- fit$modelStruct$varStruct
  if (is.null(vs)) return(stats::setNames(rep(fit$sigma, length(genes)), genes))
  ratio <- variance_ratios(fit)$gene
  if (is.null(ratio)) return(stats::setNames(rep(fit$sigma, length(genes)), genes))
  stats::setNames(fit$sigma * unname(ratio[genes]), genes)
}

# Standard deviation ratios of the variance function, by gene and by tissue (NULL when the fit
# has no such factor). varIdent gives one ratio per level, relative to its reference level;
# varComb(varIdent(gene), varIdent(tissue)) prefixes them with A. and B.
variance_ratios <- function(fit) {
  co <- stats::coef(fit$modelStruct$varStruct, unconstrained = FALSE, allCoef = TRUE)
  d <- nlme::getData(fit)
  pick <- function(prefix, lev) {
    nm <- paste0(prefix, lev)
    if (all(nm %in% names(co))) stats::setNames(co[nm], lev) else NULL
  }
  g <- levels(d$gene); t <- if ("tissue" %in% names(d)) levels(d$tissue) else character(0)
  list(gene = pick("A.", g) %||% pick("", g), tissue = if (length(t)) pick("B.", t) %||% pick("", t))
}

`%||%` <- function(a, b) if (is.null(a)) b else a

# REML log-likelihood of Model 1a as a function of log sigma_j, up to a constant. Equal to
# nlme's REML criterion at its optimum; used for the information matrix only.
reml_model1 <- function(log_sd, X, y, gene_index) {
  w <- exp(-2 * log_sd)[gene_index]
  XtWX <- crossprod(X, X * w)
  b <- solve(XtWX, crossprod(X, y * w))
  r <- y - X %*% b
  0.5 * sum(log(w)) - 0.5 * sum(r^2 * w) - 0.5 * as.numeric(determinant(XtWX)$modulus)
}

#' Gene standard deviations with confidence intervals (Model 1a)
#'
#' Fits Model 1a by REML and gives each gene's error standard deviation with a Wald interval on
#' the log scale. The information matrix is the numerical Hessian (Richardson extrapolation,
#' numDeriv) of the REML log-likelihood in the log standard deviations. nlme's `intervals()`
#' gives the same kind of interval, but from a coarser finite-difference Hessian whose bounds
#' move in the third decimal with the parameterization (the order of the rows, the contrasts).
#'
#' @param expr Expression matrix, samples in rows and genes in columns.
#' @param level Confidence level.
#' @return Data frame with columns `gene`, `sd`, `lower`, `upper`, in the order of `expr`'s
#'   columns.
#' @export
gene_sd_ci <- function(expr, level = 0.95) {
  fit <- fit_model1(expr, "gene")
  sd <- gene_sd(fit)
  d <- nlme::getData(fit)
  X <- stats::model.matrix(~ sample + gene, d)
  H <- numDeriv::hessian(reml_model1, log(sd), X = X, y = d$y, gene_index = as.integer(d$gene))
  se <- sqrt(diag(solve(-H)))
  z <- stats::qnorm(1 - (1 - level) / 2)
  data.frame(gene = names(sd), sd = unname(sd), lower = unname(sd * exp(-z * se)),
             upper = unname(sd * exp(z * se)))
}

#' Standard deviation of the log geometric mean of a gene set
#'
#' Under Model 1a the log geometric mean of the genes in S has variance
#' sum_{j in S} sigma_j^2 / |S|^2. The paper prints the divisor as |S|; its Table 2 is
#' computed with |S|^2, and `divisor = "size"` gives the printed formula for comparison.
#'
#' @param sd Named vector of gene standard deviations ([gene_sd()]).
#' @param set Gene names.
#' @param divisor `"size2"` (|S|^2, the variance of a mean) or `"size"` (|S|, as printed).
#' @export
set_sd <- function(sd, set, divisor = c("size2", "size")) {
  divisor <- match.arg(divisor)
  if (!all(set %in% names(sd))) stop("unknown genes: ", paste(setdiff(set, names(sd)), collapse = ", "))
  k <- length(set)
  sqrt(sum(sd[set]^2) / if (divisor == "size2") k^2 else k)
}

#' Best gene set of each size (Model 1a)
#'
#' Exhaustive search over all subsets of each size for the smallest [set_sd()].
#'
#' @inheritParams set_sd
#' @return Data frame with `size`, `genes` (comma-separated, in the order of `sd`) and `sd`.
#' @export
best_sets <- function(sd, divisor = c("size2", "size")) {
  divisor <- match.arg(divisor)
  g <- names(sd)
  rows <- lapply(seq_along(g), function(k) {
    cs <- utils::combn(g, k, simplify = FALSE)
    v <- vapply(cs, function(S) set_sd(sd, S, divisor), numeric(1))
    i <- which.min(v)
    data.frame(size = k, genes = paste(cs[[i]], collapse = ","), sd = v[i])
  })
  do.call(rbind, rows)
}

#' Likelihood-ratio test of two variance groups
#'
#' Compares Model 1a (one error variance per gene) with the model in which the genes of each
#' group share one variance. Szabo et al. compare the four genes chosen from microarrays with
#' GAPD and ACTB this way (p = 0.0014; the paper does not name its test, and this one gives that
#' value).
#'
#' @param expr Expression matrix, samples in rows and genes in columns.
#' @param group Vector of group labels, one per gene (column of `expr`).
#' @return List with `statistic` (twice the log-likelihood difference, REML), `df` and `p.value`.
#' @export
variance_group_test <- function(expr, group) {
  expr <- check_expr(expr)
  if (length(group) != ncol(expr)) stop("group must have one entry per gene")
  full <- fit_model1(expr, "gene")
  d <- nlme::getData(full)
  d$grp <- factor(group[as.integer(d$gene)])
  red <- nlme::gls(y ~ sample + gene, data = d, weights = nlme::varIdent(form = ~ 1 | grp))
  stat <- as.numeric(2 * (stats::logLik(full) - stats::logLik(red)))
  df <- ncol(expr) - length(unique(group))
  list(statistic = stat, df = df, p.value = stats::pchisq(stat, df, lower.tail = FALSE))
}

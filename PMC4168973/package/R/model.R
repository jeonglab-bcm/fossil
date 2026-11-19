#' Penalties chosen by repeated likelihood cross-validation
#'
#' Run \code{i} draws its fold assignment from seed \code{seeds[i]}, where
#' \code{seeds} are drawn once from \code{seed}; each run returns the
#' \code{lambda1} that maximizes the cross-validated likelihood of
#' \code{penalized::optL1}. Any subset of the runs can be recomputed alone.
#'
#' @param x samples x features numeric matrix (column names are feature names).
#' @param time,event survival time and event indicator (1 = relapse).
#' @param runs number of cross-validation runs.
#' @param fold number of folds of each run.
#' @param seed random seed of the runs.
#' @param which indices of the runs to compute (default: all).
#' @param cores cores for the runs (\code{parallel::mclapply}).
#' @return Numeric vector of the runs' optimal \code{lambda1}.
#' @export
cv_lambdas <- function(x, time, event, runs = 250, fold = 10, seed = 1, which = seq_len(runs),
                       cores = 1) {
  y <- survival::Surv(time, event)
  set.seed(seed)
  seeds <- sample.int(.Machine$integer.max, runs)
  one <- function(s) {
    set.seed(s)
    o <- suppressWarnings(penalized::optL1(y, penalized = x, fold = fold, trace = FALSE))
    o$lambda
  }
  if (cores > 1) unlist(parallel::mclapply(seeds[which], one, mc.cores = cores, mc.preschedule = FALSE))
  else vapply(seeds[which], one, numeric(1))
}

#' Cox model with an L1 (LASSO) penalty, penalty chosen by repeated cross-validation
#'
#' Combines the optimal penalties of the cross-validation runs
#' (\code{\link{cv_lambdas}}) into one, by their median, and fits
#' \code{penalized::penalized} at that penalty on all samples. The paper
#' chose "the optimal lambda ... after running 250 simulations through
#' likelihood cross-validation".
#'
#' @inheritParams cv_lambdas
#' @param summary how the runs' penalties are combined: \code{"median"} or \code{"mean"}.
#' @param lambdas the runs' penalties, when already computed.
#' @return A list with \code{coefficients} (named, nonzero only, largest first),
#'   \code{lambda}, \code{lambdas} and \code{features}.
#' @export
cox_lasso <- function(x, time, event, runs = 250, fold = 10, seed = 1, cores = 1,
                      summary = c("median", "mean"), lambdas = NULL) {
  summary <- match.arg(summary)
  if (is.null(lambdas)) lambdas <- cv_lambdas(x, time, event, runs, fold, seed, cores = cores)
  lambda <- if (summary == "median") stats::median(lambdas) else mean(lambdas)
  y <- survival::Surv(time, event)
  fit <- suppressWarnings(penalized::penalized(y, penalized = x, lambda1 = lambda, trace = FALSE))
  b <- penalized::coefficients(fit, "penalized")
  b <- b[b != 0]
  list(coefficients = b[order(-b)], lambda = lambda, lambdas = lambdas, features = colnames(x))
}

#' Prognostic index
#'
#' The linear predictor of a Cox model: the sum of the features weighted by
#' the coefficients (the log hazard ratio against an all-zero baseline).
#'
#' @param coefficients named coefficient vector.
#' @param x samples x features matrix holding at least the named features.
#' @return Numeric vector, one value per sample.
#' @export
prognostic_index <- function(coefficients, x) {
  if (length(coefficients) == 0) return(rep(0, nrow(x)))
  drop(x[, names(coefficients), drop = FALSE] %*% coefficients)
}

#' Higher and lower risk groups
#'
#' @param pi prognostic index.
#' @param cutoff samples with \code{pi > cutoff} are "higher risk".
#' @return Factor with levels \code{lower} and \code{higher}.
#' @export
risk_groups <- function(pi, cutoff) {
  factor(ifelse(pi > cutoff, "higher", "lower"), levels = c("lower", "higher"))
}

#' Log-rank test between groups
#'
#' @param time,event survival time and event.
#' @param group grouping factor.
#' @param rho 0 for the log-rank test, 1 for the Peto and Peto modification of
#'   the Gehan-Wilcoxon test (\code{survival::survdiff}).
#' @return The p-value.
#' @export
logrank_p <- function(time, event, group, rho = 0) {
  ok <- !is.na(time) & !is.na(event) & !is.na(group)
  group <- droplevels(as.factor(group[ok]))
  if (nlevels(group) < 2) return(NA_real_)
  d <- survival::survdiff(survival::Surv(time[ok], event[ok]) ~ group, rho = rho)
  stats::pchisq(d$chisq, df = length(d$n) - 1, lower.tail = FALSE)
}

#' ROC curve and area under it
#'
#' @param score predictor (higher means relapse is more likely).
#' @param label 1 for relapse, 0 for none.
#' @return A list with \code{auc} and \code{curve} (data frame of
#'   false and true positive rates, one row per threshold).
#' @export
roc_auc <- function(score, label) {
  ok <- !is.na(score) & !is.na(label)
  s <- score[ok]; l <- label[ok]
  np <- sum(l == 1); nn <- sum(l == 0)
  r <- rank(s)
  auc <- (sum(r[l == 1]) - np * (np + 1) / 2) / (np * nn)
  th <- c(Inf, sort(unique(s), decreasing = TRUE))
  tpr <- vapply(th, function(t) sum(s >= t & l == 1) / np, 0)
  fpr <- vapply(th, function(t) sum(s >= t & l == 0) / nn, 0)
  list(auc = auc, curve = data.frame(fpr = fpr, tpr = tpr))
}

#' Univariate Cox models
#'
#' @param x samples x features matrix.
#' @param time,event survival time and event.
#' @return Data frame with \code{feature}, \code{coef}, \code{hr} and \code{p}
#'   (Wald test).
#' @export
univariate_cox <- function(x, time, event) {
  y <- survival::Surv(time, event)
  out <- lapply(colnames(x), function(f) {
    fit <- survival::coxph(y ~ x[, f])
    s <- summary(fit)$coefficients
    data.frame(feature = f, coef = s[1, "coef"], hr = s[1, "exp(coef)"], p = s[1, "Pr(>|z|)"])
  })
  do.call(rbind, out)
}

#' Evaluate a model on a data set
#'
#' Splits the samples at \code{cutoff} of the prognostic index, and returns
#' the log-rank p-value, the AUC of the index against relapse, and the groups.
#'
#' @param pi prognostic index.
#' @param time,event survival time and event.
#' @param cutoff risk cutoff.
#' @param rho passed to \code{\link{logrank_p}}.
#' @return A list with \code{p}, \code{auc}, \code{roc}, \code{group} and \code{n_high}.
#' @export
evaluate_model <- function(pi, time, event, cutoff, rho = 0) {
  g <- risk_groups(pi, cutoff)
  r <- roc_auc(pi, event)
  list(p = logrank_p(time, event, g, rho = rho), auc = r$auc, roc = r$curve, group = g,
       n_high = sum(g == "higher"))
}

#' Cutoff that matches a share of high-risk samples
#'
#' @param pi prognostic index.
#' @param high_share share of samples to call higher risk (0.25 for the
#'   paper's 3rd-quartile cutoff; the relapse share of a data set for Fig. 5).
#' @return The cutoff (a quantile of \code{pi}).
#' @export
share_cutoff <- function(pi, high_share) {
  unname(stats::quantile(pi, 1 - high_share))
}

#' Leave-one-out evaluation without refitting
#'
#' For each sample in turn, the sample is left out, the cutoff is set so that
#' the share of higher-risk samples equals the relapse share of the remaining
#' samples, and the log-rank p-value and the AUC are recomputed, as the paper's
#' Methods describe.
#'
#' @param pi prognostic index.
#' @param time,event survival time and event.
#' @return Data frame with \code{left_out}, \code{p} and \code{auc}.
#' @export
loo_evaluate <- function(pi, time, event) {
  out <- lapply(seq_along(pi), function(i) {
    k <- -i
    cut <- share_cutoff(pi[k], mean(event[k] == 1))
    e <- evaluate_model(pi[k], time[k], event[k], cut)
    data.frame(left_out = i, p = e$p, auc = e$auc)
  })
  do.call(rbind, out)
}

#' NKI 70-gene signature score
#'
#' The correlation of each sample's expression of the signature genes
#' (standardized across samples) with the average good-prognosis profile of
#' van 't Veer et al. (2002), as in genefu's \code{gene70}: the score is minus
#' the Spearman correlation and a sample is "poor" when the score is at least
#' -0.3.
#'
#' @param expr genes x samples log2 expression with gene symbols as row names.
#' @param signature data frame with \code{symbol} and \code{good_profile}.
#' @param cutoff risk cutoff on the score.
#' @return A list with \code{score}, \code{poor} (logical) and \code{genes} (the symbols used).
#' @export
nki70_score <- function(expr, signature, cutoff = -0.3) {
  sig <- signature[!is.na(signature$symbol) & signature$symbol %in% rownames(expr), ]
  sig <- sig[!duplicated(sig$symbol), ]
  z <- t(scale(t(expr[sig$symbol, , drop = FALSE])))
  score <- -apply(z, 2, function(v) stats::cor(v, sig$good_profile, method = "spearman"))
  list(score = score, poor = score >= cutoff, genes = sig$symbol)
}

#' Two groups from hierarchical clustering
#'
#' Clusters the samples (columns) by Euclidean distance with complete linkage,
#' as \code{heatmap} and \code{gplots::heatmap.2} do by default, and cuts the
#' tree into two groups.
#'
#' @param x features x samples matrix.
#' @return Integer vector of groups (1 or 2), and the tree as attribute \code{hclust}.
#' @export
two_clusters <- function(x) {
  h <- stats::hclust(stats::dist(t(x)))
  g <- stats::cutree(h, 2)
  attr(g, "hclust") <- h
  g
}

#' Genes of the selected pathways, counted and weighted
#'
#' For each gene in the selected pathways: how many of them contain it, and
#' the sum of their hazard ratios (the paper's Table 3: "weighted sum of ...
#' occurrences in selected pathways (counts) and weights measured by the
#' hazard ratio of each pathway").
#'
#' @param genesets named list of gene symbol vectors.
#' @param hr named hazard ratios of the selected pathways.
#' @return Data frame with \code{gene}, \code{count} and \code{weighted},
#'   sorted by \code{weighted} (largest first), then by gene.
#' @export
pathway_gene_weights <- function(genesets, hr) {
  sets <- genesets[names(hr)]
  genes <- sort(unique(unlist(sets)))
  count <- vapply(genes, function(g) sum(vapply(sets, function(s) g %in% s, logical(1))), numeric(1))
  w <- vapply(genes, function(g) sum(hr[vapply(sets, function(s) g %in% s, logical(1))]), numeric(1))
  d <- data.frame(gene = genes, count = count, weighted = w, row.names = NULL)
  d[order(-d$weighted, d$gene), ]
}

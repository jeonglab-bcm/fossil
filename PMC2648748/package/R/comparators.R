# The comparators of the paper's simulation study: the single-locus chi-squared test and the
# stepwise (two-stage) logistic regression of Marchini, Donnelly and Cardon (2005), extended by
# the paper to three-way interactions.

#' Single-locus chi-squared test
#'
#' Pearson's chi-squared test of the 2 x 3 table of cases and controls by genotype, with up to 2
#' degrees of freedom (genotypes seen in no one are dropped).
#'
#' @param geno Genotype matrix (individuals x SNPs, 0/1/2).
#' @param status 1 for cases, 0 for controls.
#' @return A data frame with \code{statistic}, \code{df} and \code{p} per SNP.
#' @export
chisq_single <- function(geno, status) {
  .check_geno(geno, status)
  tab <- .count_tables(geno, status, matrix(seq_len(ncol(geno)), ncol = 1))
  d <- tab$cases
  u <- tab$controls
  n <- d + u
  nd <- sum(status == 1)
  nu <- sum(status == 0)
  N <- nd + nu
  ed <- n * nd / N
  eu <- n * nu / N
  keep <- n > 0
  stat <- colSums(ifelse(keep, (d - ed)^2 / ifelse(keep, ed, 1) + (u - eu)^2 / ifelse(keep, eu, 1), 0))
  df <- colSums(keep) - 1
  p <- ifelse(df > 0, stats::pchisq(stat, pmax(df, 1), lower.tail = FALSE), 1)
  data.frame(statistic = stat, df = df, p = p)
}

# Likelihood-ratio statistic of the logistic model with one parameter per observed genotype
# combination (the saturated "full" model) against the intercept-only model: the G statistic of
# the 2 x (observed combinations) table. Columns of the count matrices are tests.
.g_test <- function(d, u) {
  n <- d + u
  nd <- colSums(d)[1]
  nu <- colSums(u)[1]
  N <- nd + nu
  term <- function(o, e) ifelse(o > 0, o * log(o / e), 0)
  ed <- n * nd / N
  eu <- n * nu / N
  stat <- 2 * colSums(term(d, ed) + term(u, eu))
  df <- colSums(n > 0) - 1
  p <- ifelse(df > 0, stats::pchisq(stat, pmax(df, 1), lower.tail = FALSE), 1)
  data.frame(statistic = stat, df = df, p = p)
}

# Likelihood-ratio test of the interaction terms: the full model (one parameter per observed
# genotype combination) against the logistic model with main effects only (a factor per SNP).
# The full model is saturated, so the statistic is the main-effects model's residual deviance on
# the table of genotype combinations.
.interaction_test <- function(d, u, k) {
  cells <- as.matrix(expand.grid(rep(list(0:2), k)))
  stat <- df <- numeric(ncol(d))
  cache <- new.env()
  for (s in seq_len(ncol(d))) {
    keep <- (d[, s] + u[, s]) > 0
    key <- paste(which(keep), collapse = ",")
    mm <- cache[[key]]
    if (is.null(mm)) {
      X <- cells[keep, , drop = FALSE]
      mm <- stats::model.matrix(~ ., data = as.data.frame(lapply(as.data.frame(X), factor)))
      assign(key, mm, envir = cache)
    }
    y <- cbind(d[keep, s], u[keep, s])
    fit <- suppressWarnings(stats::glm.fit(mm, y, family = stats::binomial()))
    stat[s] <- fit$deviance
    df[s] <- sum(keep) - fit$rank
  }
  p <- ifelse(df > 0, stats::pchisq(stat, pmax(df, 1), lower.tail = FALSE), 1)
  data.frame(statistic = stat, df = df, p = p)
}

#' Likelihood-ratio tests of logistic models for sets of SNPs
#'
#' \code{type = "full"}: the model with a parameter for each observed genotype combination (two
#' SNPs: main effects and interaction, 8 degrees of freedom when all nine combinations occur)
#' against the intercept-only model. \code{type = "interaction"}: the same model against the
#' model with main effects only (4 degrees of freedom for two SNPs, 20 for three), so only the
#' interaction is tested.
#'
#' @inheritParams b_test
#' @param type "full" or "interaction".
#' @export
lr_test <- function(geno, status, sets, type = c("full", "interaction")) {
  type <- match.arg(type)
  .check_geno(geno, status)
  sets <- as.matrix(sets)
  tab <- .count_tables(geno, status, sets)
  if (type == "full" || ncol(sets) == 1) .g_test(tab$cases, tab$controls)
  else .interaction_test(tab$cases, tab$controls, ncol(sets))
}

#' Stepwise logistic regression (two-stage strategy)
#'
#' Stage 1 tests every SNP with the single-locus logistic model (2 degrees of freedom) and keeps
#' the most significant fraction \code{eps}. Stage 2 tests every pair (and, as in the paper, every
#' triple) of kept SNPs with the full logistic model. Single-locus results are adjusted by L; by
#' default stage-2 results are adjusted by the number of stage-2 tests of each order, as in the
#' two-stage strategy of Marchini et al. (2005); \code{stage2_correction = "all"} adjusts by
#' L(L-1)/2 and L(L-1)(L-2)/6 instead.
#'
#' @param geno Genotype matrix (individuals x SNPs, 0/1/2).
#' @param status 1 for cases, 0 for controls.
#' @param eps Fraction of SNPs kept after stage 1 (paper: 10\%).
#' @param alpha Significance level.
#' @param max_order Highest order tested in stage 2 (paper: 3).
#' @param stage2_correction "tested" or "all".
#' @param focus Optional SNP columns: only stage-2 tests that include one of them are run (faster
#'   when only some SNPs matter, as in a power study).
#' @param stage2_test "full": stage 2 tests the full model against the null model (main effects
#'   and interaction together); "interaction": only the interaction terms, against the main-effects
#'   model, so a locus with only a marginal effect is found in stage 1 alone (as epiMODE, by the
#'   same group, describes the method).
#' @return A data frame of tests (\code{order}, \code{snps}, \code{statistic}, \code{df}, \code{p},
#'   \code{p_adj}, \code{reported}) with attribute \code{kept} (the stage-1 SNPs).
#' @export
stepwise_lr <- function(geno, status, eps = 0.1, alpha = 0.05, max_order = 3,
                        stage2_correction = c("tested", "all"), focus = NULL,
                        stage2_test = c("full", "interaction")) {
  stage2_correction <- match.arg(stage2_correction)
  stage2_test <- match.arg(stage2_test)
  .check_geno(geno, status)
  L <- ncol(geno)
  one <- lr_test(geno, status, matrix(seq_len(L), ncol = 1))
  one$order <- 1L
  one$snps <- as.character(seq_len(L))
  one$p_adj <- pmin(1, one$p * L)
  out <- list(one)
  n_keep <- ceiling(eps * L)
  kept <- sort(order(one$p, -one$statistic)[seq_len(n_keep)])
  for (k in 2:max_order) {
    if (k > max_order || n_keep < k) break
    sets <- t(utils::combn(kept, k))
    m <- if (stage2_correction == "tested") nrow(sets) else choose(L, k)
    if (!is.null(focus)) sets <- sets[rowSums(matrix(sets %in% focus, ncol = k)) > 0, , drop = FALSE]
    if (!nrow(sets)) next
    r <- lr_test(geno, status, sets, type = stage2_test)
    r$order <- as.integer(k)
    r$snps <- apply(sets, 1, paste, collapse = ",")
    r$p_adj <- pmin(1, r$p * m)
    out[[length(out) + 1]] <- r
  }
  res <- do.call(rbind, out)
  res$reported <- res$p_adj < alpha
  res <- res[, c("order", "snps", "statistic", "df", "p", "p_adj", "reported")]
  rownames(res) <- NULL
  attr(res, "kept") <- kept
  res
}

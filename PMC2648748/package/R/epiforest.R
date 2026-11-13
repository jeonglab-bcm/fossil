# epiForest (Jiang, Tang, Wu and Fu 2009): stage 1, a random forest on all SNPs (categorical
# features) for gini importance and the sliding window sequential forward feature selection
# (SWSFS); stage 2, hierarchical B-statistic tests of up to three-way interactions among the
# candidates, Bonferroni-corrected for the total number of markers L.

.as_factors <- function(geno) {
  df <- as.data.frame(geno)
  for (j in seq_along(df)) df[[j]] <- factor(df[[j]], levels = 0:2)
  df
}

#' Gini importance of every SNP
#'
#' One random forest (R package randomForest) with every SNP as a three-level factor, cases
#' against controls; returns the mean decrease in gini (randomForest's \code{MeanDecreaseGini},
#' the paper's gini importance).
#'
#' @param geno Genotype matrix (individuals x SNPs, 0/1/2).
#' @param status 1 for cases, 0 for controls.
#' @param ntree Number of trees. The paper does not give it for its simulations; 500 is the
#'   randomForest default.
#' @param mtry Features tried at each split; NULL for randomForest's default,
#'   \code{floor(sqrt(ncol(geno)))}.
#' @param x Optional data frame of factors already made from \code{geno}.
#' @export
gini_importance <- function(geno, status, ntree = 500, mtry = NULL, x = NULL) {
  .check_geno(geno, status)
  if (is.null(x)) x <- .as_factors(geno)
  y <- factor(status, levels = c(0, 1))
  args <- list(x = x, y = y, ntree = ntree)
  if (!is.null(mtry)) args$mtry <- mtry
  rf <- do.call(randomForest::randomForest, args)
  g <- rf$importance[, "MeanDecreaseGini"]
  names(g) <- colnames(geno)
  g
}

#' Sliding window sequential forward feature selection (SWSFS)
#'
#' Adds SNPs in the given order, fits a forest on the first i SNPs and records its out-of-bag
#' error; stops at the first i > w for which the error at i - w is the smallest in the window
#' [i - w, i] (the first minimum when tied) and returns k = i - w. As in the paper's pseudocode,
#' k = L if the loop runs out.
#'
#' @param geno,status As in \code{\link{gini_importance}}.
#' @param order Column indices of \code{geno}, most important first.
#' @param window The window w (the paper uses 20).
#' @param ntree Trees per forest.
#' @param x Optional data frame of factors already made from \code{geno}.
#' @return A list with \code{k} (number selected), \code{selected} (columns), \code{errors}
#'   (out-of-bag error of each forest built) and \code{forests} (how many were built).
#' @export
swsfs <- function(geno, status, order, window = 20, ntree = 500, x = NULL) {
  .check_geno(geno, status)
  if (is.null(x)) x <- .as_factors(geno)
  y <- factor(status, levels = c(0, 1))
  L <- length(order)
  err <- numeric(0)
  k <- L
  for (i in seq_len(L)) {
    rf <- randomForest::randomForest(x[, order[seq_len(i)], drop = FALSE], y, ntree = ntree)
    err[i] <- rf$err.rate[ntree, "OOB"]
    if (i > window && which.min(err[(i - window):i]) == 1L) {
      k <- i - window
      break
    }
  }
  list(k = k, selected = order[seq_len(k)], errors = err, forests = length(err))
}

#' Hierarchical B-statistic tests of up to three-way interactions
#'
#' One-way tests of every candidate (reported when the Bonferroni-adjusted p, times L, is below
#' alpha); two-way tests of every pair, skipped when both SNPs were reported and conditional on
#' the reported SNP when one was (adjusted by L(L-1)/2); three-way tests of every triple,
#' conditional on the SNPs of the triple already reported in a one- or two-way test and skipped
#' when all three were (adjusted by L(L-1)(L-2)/6).
#'
#' @param geno Genotypes of the candidates (individuals x candidates).
#' @param status 1 for cases, 0 for controls.
#' @param n_markers L, the total number of markers screened (for the Bonferroni correction).
#' @param alpha Significance level.
#' @param max_order Highest order tested (1, 2 or 3).
#' @param a Dirichlet pseudo-count.
#' @return A data frame with one row per test: \code{order}, \code{snps} (column indices of
#'   \code{geno}, comma-separated), \code{given}, \code{B}, \code{df}, \code{p}, \code{p_adj},
#'   \code{reported}.
#' @export
hierarchical_tests <- function(geno, status, n_markers = ncol(geno), alpha = 0.05, max_order = 3,
                               a = 0.5) {
  .check_geno(geno, status)
  l <- ncol(geno)
  L <- n_markers
  out <- list()
  m1 <- L
  one <- b_test(geno, status, matrix(seq_len(l), ncol = 1), a = a)
  one$order <- 1L
  one$snps <- as.character(seq_len(l))
  one$given <- ""
  one$p_adj <- pmin(1, one$p * m1)
  one$reported <- one$p_adj < alpha
  out[[1]] <- one
  rep1 <- which(one$reported)
  rep2 <- list()
  if (max_order >= 2 && l >= 2) {
    pairs <- t(utils::combn(l, 2))
    m2 <- L * (L - 1) / 2
    n_rep <- (pairs[, 1] %in% rep1) + (pairs[, 2] %in% rep1)
    res <- NULL
    for (case in 0:1) {
      idx <- which(n_rep == case)
      if (!length(idx)) next
      sets <- pairs[idx, , drop = FALSE]
      given <- integer(0)
      if (case == 1) {
        # put the reported SNP first so that the same `given` applies to every row
        swap <- !(sets[, 1] %in% rep1)
        sets[swap, ] <- sets[swap, 2:1]
        given <- 1L
      }
      r <- b_test(geno, status, sets, given = given, a = a)
      r$order <- 2L
      r$snps <- apply(sets, 1, paste, collapse = ",")
      r$given <- if (case == 1) as.character(sets[, 1]) else ""
      res <- rbind(res, r)
    }
    if (!is.null(res)) {
      res$p_adj <- pmin(1, res$p * m2)
      res$reported <- res$p_adj < alpha
      out[[2]] <- res
      rep2 <- lapply(strsplit(res$snps[res$reported], ","), as.integer)
    }
  }
  if (max_order >= 3 && l >= 3) {
    trip <- t(utils::combn(l, 3))
    m3 <- L * (L - 1) * (L - 2) / 6
    # SNPs of each triple already reported (singly or within a reported pair of the triple)
    known <- matrix(trip %in% rep1, ncol = 3)
    for (pr in rep2) {
      inside <- (trip[, 1] %in% pr) + (trip[, 2] %in% pr) + (trip[, 3] %in% pr) == 2
      if (any(inside)) known[inside, ] <- known[inside, ] | matrix(trip[inside, ] %in% pr, ncol = 3)
    }
    nk <- rowSums(known)
    res <- NULL
    for (nt in 0:2) {
      idx <- which(nk == nt)
      if (!length(idx)) next
      sets <- trip[idx, , drop = FALSE]
      kn <- known[idx, , drop = FALSE]
      # reorder each row: known SNPs first
      ord <- t(apply(kn, 1, function(z) order(!z)))
      sets <- t(vapply(seq_len(nrow(sets)), function(s) sets[s, ord[s, ]], numeric(3)))
      given <- seq_len(nt)
      r <- b_test(geno, status, sets, given = given, a = a)
      r$order <- 3L
      r$snps <- apply(sets, 1, paste, collapse = ",")
      r$given <- if (nt > 0) apply(sets[, seq_len(nt), drop = FALSE], 1, paste, collapse = ",") else ""
      res <- rbind(res, r)
    }
    if (!is.null(res)) {
      res$p_adj <- pmin(1, res$p * m3)
      res$reported <- res$p_adj < alpha
      out[[3]] <- res
    }
  }
  res <- do.call(rbind, out)
  res <- res[, c("order", "snps", "given", "B", "df", "shift", "p", "p_adj", "reported")]
  rownames(res) <- NULL
  res
}

#' SNPs identified by a table of tests
#'
#' @param tests Output of \code{\link{hierarchical_tests}} or \code{\link{stepwise_lr}}.
#' @return Sorted column indices of every SNP in a reported test.
#' @export
identified_snps <- function(tests) {
  s <- tests$snps[tests$reported]
  if (!length(s)) return(integer(0))
  sort(unique(as.integer(unlist(strsplit(s, ",")))))
}

#' epiForest
#'
#' Runs both stages: a forest on all SNPs for gini importance, SWSFS for the candidates, and the
#' hierarchical B-statistic tests among the candidates (Bonferroni over all L SNPs).
#'
#' @param geno Genotype matrix (individuals x SNPs, coded 0/1/2 copies of the minor allele).
#' @param status 1 for cases, 0 for controls.
#' @param ntree Trees per forest (paper: not stated for simulations; randomForest default 500).
#' @param window SWSFS window (paper: 20).
#' @param alpha Significance level (paper: 0.05).
#' @param max_order Highest interaction order tested (paper: 3).
#' @param a Dirichlet pseudo-count (paper: 0.5).
#' @param seed Optional seed set before the first forest.
#' @return A list: \code{gini} (per SNP), \code{order}, \code{swsfs} (see \code{\link{swsfs}}),
#'   \code{candidates} (column indices), \code{tests} (with \code{snps} as column indices of
#'   \code{geno}) and \code{identified} (column indices).
#' @export
epiforest <- function(geno, status, ntree = 500, window = 20, alpha = 0.05, max_order = 3,
                      a = 0.5, seed = NULL) {
  .check_geno(geno, status)
  if (!is.null(seed)) set.seed(seed)
  if (is.null(colnames(geno))) colnames(geno) <- paste0("snp", seq_len(ncol(geno)))
  x <- .as_factors(geno)
  gini <- gini_importance(geno, status, ntree = ntree, x = x)
  ord <- order(gini, decreasing = TRUE)
  sel <- swsfs(geno, status, ord, window = window, ntree = ntree, x = x)
  cand <- sel$selected
  tests <- hierarchical_tests(geno[, cand, drop = FALSE], status, n_markers = ncol(geno),
                              alpha = alpha, max_order = max_order, a = a)
  # map candidate positions back to columns of geno
  remap <- function(s) vapply(strsplit(s, ","), function(z)
    if (length(z) == 0 || identical(z, "")) "" else paste(cand[as.integer(z)], collapse = ","), "")
  tests$snps <- remap(tests$snps)
  tests$given <- remap(tests$given)
  list(gini = gini, order = ord, swsfs = sel, candidates = cand, tests = tests,
       identified = identified_snps(tests))
}

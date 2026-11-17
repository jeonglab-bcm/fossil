#' Filter statistics
#'
#' The filter statistics of the paper for a two-group matrix: signal
#' \eqn{W_S = (\bar X + \bar Y)/2}, fold change \eqn{W_{FC} = |\bar X - \bar Y|},
#' variance \eqn{W_V = S_Z^2} (the variance of all samples of the feature),
#' and the absolute t statistic, which Additional File 1 uses for contrast.
#'
#' @param x numeric matrix, features in rows.
#' @param group factor with two levels, one per column.
#' @param t optional vector of t statistics (from \code{row_ttest}).
#' @return A data frame with columns \code{foldchange}, \code{signal},
#'   \code{variance} and \code{tstat}.
filter_statistics <- function(x, group, t = NULL) {
  g <- as.integer(factor(group))
  mx <- rowMeans(x[, g == 1, drop = FALSE])
  my <- rowMeans(x[, g == 2, drop = FALSE])
  mz <- rowMeans(x)
  vz <- rowSums((x - mz)^2) / (ncol(x) - 1)
  if (is.null(t)) t <- row_ttest(x, group)$statistic
  data.frame(foldchange = abs(mx - my), signal = (mx + my) / 2,
             variance = vz, tstat = abs(t))
}

#' Keep the features a filter leaves in
#'
#' Removes the fraction \code{fraction} of features with the smallest filter
#' statistic, cutting at the empirical quantile:
#' \code{stat > quantile(stat, fraction)}. \code{fraction = 0} keeps every
#' feature.
#'
#' @param stat filter statistic, one value per feature.
#' @param fraction fraction to remove, in [0, 1].
#' @return Logical vector, \code{TRUE} for the features kept.
filter_keep <- function(stat, fraction) {
  if (fraction <= 0) return(rep(TRUE, length(stat)))
  if (fraction >= 1) return(rep(FALSE, length(stat)))
  stat > quantile(stat, fraction, names = FALSE)
}

#' Two-sample tests by row
#'
#' Student's two-sample t test with pooled variance, or the Wilcoxon
#' rank-sum test (exact two-sided p-values as \code{wilcox.test} gives them
#' without ties), for every row of a matrix.
#'
#' @param x numeric matrix, features in rows.
#' @param group factor with two levels.
#' @param test \code{"t"} or \code{"wilcoxon"}.
#' @param exact Wilcoxon only: exact p-values (\code{TRUE}) or the normal
#'   approximation with continuity correction (\code{FALSE}), as
#'   \code{wilcox.test(exact = FALSE)}.
#' @return A list with \code{statistic} and \code{p.value}.
row_ttest <- function(x, group, test = c("t", "wilcoxon"), exact = TRUE) {
  test <- match.arg(test)
  g <- as.integer(factor(group))
  n1 <- sum(g == 1)
  n2 <- sum(g == 2)
  x1 <- x[, g == 1, drop = FALSE]
  x2 <- x[, g == 2, drop = FALSE]
  if (test == "t") {
    m1 <- rowMeans(x1)
    m2 <- rowMeans(x2)
    ss <- rowSums((x1 - m1)^2) + rowSums((x2 - m2)^2)
    df <- n1 + n2 - 2
    se <- sqrt(ss / df * (1 / n1 + 1 / n2))
    t <- (m1 - m2) / se
    return(list(statistic = t, p.value = 2 * pt(-abs(t), df)))
  }
  r <- t(apply(x, 1, rank))
  w <- rowSums(r[, g == 1, drop = FALSE]) - n1 * (n1 + 1) / 2
  if (!exact) {
    z <- w - n1 * n2 / 2
    z <- (z - sign(z) * 0.5) / sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    return(list(statistic = w, p.value = pmin(1, 2 * pnorm(-abs(z)))))
  }
  p <- ifelse(w > n1 * n2 / 2, stats::pwilcox(w - 1, n1, n2, lower.tail = FALSE),
              stats::pwilcox(w, n1, n2))
  list(statistic = w, p.value = pmin(1, 2 * p))
}

#' Multiple-testing rejections
#'
#' Rejections at FDR level \code{alpha} with the paper's four methods:
#' Benjamini-Hochberg (\code{"BH"}), Benjamini-Yekutieli (\code{"BY"}),
#' adaptive Benjamini-Hochberg (\code{"aBH"}, multtest's two-stage
#' procedure of Benjamini, Krieger and Yekutieli 2006, \code{"TSBH"}, or its
#' \code{"ABH"} with \code{abh = "ABH"}), Storey's q-value (\code{"qvalue"}),
#' and Bonferroni (\code{"bonferroni"}).
#'
#' @param p vector of p-values.
#' @param method one of the methods above.
#' @param alpha FDR level (a vector is allowed for \code{"BH"}, \code{"BY"}
#'   and \code{"bonferroni"}).
#' @param abh multtest procedure used for \code{"aBH"}.
#' @param ... passed to \code{qvalue::qvalue}.
#' @return Logical vector (or matrix, one column per level) of rejections.
fdr_reject <- function(p, method = c("BH", "BY", "aBH", "qvalue", "bonferroni"),
                       alpha = 0.05, abh = c("TSBH", "ABH"), ...) {
  method <- match.arg(method)
  abh <- match.arg(abh)
  if (length(p) == 0) return(logical(0))
  adj <- fdr_adjust(p, method, alpha = alpha[1], abh = abh, ...)
  if (length(alpha) == 1) return(adj <= alpha)
  sapply(alpha, function(a) adj <= a)
}

#' @rdname fdr_reject
fdr_adjust <- function(p, method = c("BH", "BY", "aBH", "qvalue", "bonferroni"),
                       alpha = 0.05, abh = c("TSBH", "ABH"), ...) {
  method <- match.arg(method)
  abh <- match.arg(abh)
  switch(method,
    BH = p.adjust(p, "BH"),
    BY = p.adjust(p, "BY"),
    bonferroni = p.adjust(p, "bonferroni"),
    aBH = {
      r <- multtest::mt.rawp2adjp(p, proc = abh, alpha = alpha)
      out <- numeric(length(p))
      out[r$index] <- r$adjp[, 2]
      out
    },
    qvalue = qvalue::qvalue(p, ...)$qvalues)
}

#' Achieved FDR and power
#'
#' @param rejected logical, the features declared differentially expressed
#'   (after filtering, over all features: filtered-out features are
#'   \code{FALSE}).
#' @param null logical, \code{TRUE} for the null features.
#' @return Named vector: \code{fdr} (false positives among the rejections, 0
#'   when nothing is rejected), \code{power} (true positives among all
#'   non-null features), \code{rejected}.
achieved_fdr_power <- function(rejected, null) {
  r <- sum(rejected)
  c(fdr = if (r == 0) 0 else sum(rejected & null) / r,
    power = sum(rejected & !null) / sum(!null), rejected = r)
}

#' Achieved FDR, power and pi0 after filtering
#'
#' For one data set: test every feature, filter with each filter statistic
#' and fraction, correct the p-values of the features left in, and record
#' the achieved FDR, the power and the proportion of null features left in.
#' The q-value method is used only with the signal and variance filters, as
#' in the paper (the fold-change and t filters cut the p-value range).
#'
#' @param sim a list with \code{x}, \code{group} and \code{null} (as from
#'   \code{simulate_two_group}).
#' @param fractions fractions removed.
#' @param filters filter statistics to use (columns of
#'   \code{filter_statistics}) plus \code{"best"} (removes null features
#'   first) and \code{"random"}.
#' @param methods correction methods (see \code{fdr_reject}).
#' @param alpha FDR levels.
#' @param test \code{"t"} or \code{"wilcoxon"}.
#' @param abh,lambda multtest procedure for aBH; lambda grid for qvalue
#'   (\code{NULL} for the qvalue default).
#' @param exact passed to \code{row_ttest} for the Wilcoxon test.
#' @return A data frame with one row per filter, fraction, method and level.
filter_curve <- function(sim, fractions = c(seq(0, 0.9, 0.1), 0.99),
                         filters = c("foldchange", "signal", "variance"),
                         methods = c("BH", "BY", "aBH", "qvalue"),
                         alpha = 0.05, test = c("t", "wilcoxon"),
                         abh = "TSBH", lambda = NULL, exact = TRUE) {
  test <- match.arg(test)
  tt <- row_ttest(sim$x, sim$group, test, exact = exact)
  # the test-statistic "filter" uses the statistic of the test in use: |t|, or
  # |W - n1 n2 / 2| for the Wilcoxon rank-sum test
  n1 <- sum(as.integer(factor(sim$group)) == 1)
  tstat <- if (test == "t") tt$statistic else tt$statistic - n1 * (length(sim$group) - n1) / 2
  fs <- filter_statistics(sim$x, sim$group, t = tstat)
  m <- nrow(sim$x)
  out <- list()
  for (f in filters) {
    stat <- switch(f,
      best = ifelse(sim$null, 0, 1) + seq_len(m) / (m + 1) * 1e-3,
      random = stats::runif(m),
      fs[[f]])
    for (x in fractions) {
      keep <- filter_keep(stat, x)
      p <- tt$p.value[keep]
      for (meth in methods) {
        if (meth == "qvalue" && f %in% c("foldchange", "tstat")) next
        rej <- matrix(FALSE, m, length(alpha))
        if (length(p) > 0) {
          # qvalue's pi0 smoother fails when no p-value exceeds the largest lambda
          # (a few dozen features left): such points are skipped, as in the paper
          r <- tryCatch(if (meth == "qvalue" && !is.null(lambda)) {
            fdr_reject(p, meth, alpha, lambda = lambda)
          } else fdr_reject(p, meth, alpha, abh = abh), error = function(e) NULL)
          if (is.null(r)) next
          rej[keep, ] <- r
        }
        nrej <- colSums(rej)
        fp <- colSums(rej & sim$null)
        out[[length(out) + 1]] <- data.frame(
          filter = f, fraction = x, method = meth, alpha = alpha,
          fdr = ifelse(nrej == 0, 0, fp / pmax(nrej, 1)),
          power = (nrej - fp) / sum(!sim$null), rejected = nrej,
          kept = sum(keep), pi0 = if (any(keep)) mean(sim$null[keep]) else 0)
      }
    }
  }
  do.call(rbind, out)
}

#' Permute the columns of each row independently
#'
#' @param x numeric matrix.
#' @return \code{x} with the values of every row in a random order.
permute_rows <- function(x) {
  t(apply(x, 1, sample))
}

#' Test for filtering-induced FDR bias
#'
#' The test of the paper (Methods, and Additional File 1, section 9):
#' permute the column labels independently in each row, test every row,
#' apply the filter to the permuted data, and compare the p-values of the
#' features left in with U[0, 1] by the Benjamini-Hochberg step-up
#' procedure (the smallest BH-adjusted p-value, equivalent to a one-sided
#' Kolmogorov-Smirnov test against super-uniformity). Repeat \code{nperm}
#' times and compare the resulting p-values Q with U[0, 1] by a one-sided
#' Kolmogorov-Smirnov test (alternative: Q stochastically smaller than
#' uniform, i.e. the filter makes the null p-values too small and the FDR
#' too optimistic).
#'
#' @param x numeric matrix, features in rows.
#' @param group factor with two levels.
#' @param filter one or more filter statistics (columns of
#'   \code{filter_statistics}); several filters share the same permutations.
#' @param fractions fractions removed.
#' @param nperm number of permutations.
#' @param test \code{"t"} or \code{"wilcoxon"}.
#' @param alternative passed to \code{ks.test} for the final test:
#'   \code{"greater"} (one-sided, the default) or \code{"two.sided"}.
#' @return For one filter, a list: \code{Q} (nperm x fractions matrix of
#'   per-permutation p-values), \code{p.value} (Kolmogorov-Smirnov p-value
#'   per fraction) and \code{label} (the p-value to one significant digit, or
#'   \code{"***"} below 0.001). For several filters, a named list of these.
fdr_bias_test <- function(x, group, filter = "foldchange",
                          fractions = c(seq(0, 0.9, 0.1), 0.99),
                          nperm = 1000, test = c("t", "wilcoxon"),
                          alternative = c("greater", "two.sided")) {
  test <- match.arg(test)
  alternative <- match.arg(alternative)
  Q <- lapply(filter, function(f) matrix(NA_real_, nperm, length(fractions),
                                         dimnames = list(NULL, format(fractions))))
  names(Q) <- filter
  for (i in seq_len(nperm)) {
    xp <- permute_rows(x)
    tt <- row_ttest(xp, group, test)
    fs <- filter_statistics(xp, group, t = tt$statistic)
    for (f in filter) for (j in seq_along(fractions)) {
      keep <- filter_keep(fs[[f]], fractions[j])
      Q[[f]][i, j] <- min(p.adjust(tt$p.value[keep], "BH"))
    }
  }
  res <- lapply(Q, function(q) {
    pv <- apply(q, 2, function(v) suppressWarnings(ks.test(v, "punif", alternative = alternative)$p.value))
    list(Q = q, p.value = pv,
         label = ifelse(pv < 0.001, "***", vapply(pv, function(v) format(signif(v, 1), scientific = FALSE), "")))
  })
  if (length(filter) == 1) res[[1]] else res
}

#' Path of a bundled example file
#'
#' @param name file name in the package's \code{extdata} folder.
#' @return The full path.
example_path <- function(name = "example_data.csv") {
  p <- system.file("extdata", name, package = "filterfdr")
  if (p == "") stop("no bundled file named ", name)
  p
}

#' Filtering before or after multiple-testing correction
#'
#' Additional File 1, section 13: (A) no filter; (B) a fraction of the
#' features filtered out before the BH correction; (C) a fraction of the
#' features declared differentially expressed (BH over all features)
#' removed afterwards, those with the smallest filter statistic.
#'
#' @param sim a list with \code{x}, \code{group} and \code{null}.
#' @param filter filter statistic.
#' @param pre fractions removed before the correction (situation B).
#' @param post fractions of the selected list removed after it (situation C).
#' @param alpha FDR level.
#' @param post_cut \code{"selected"} (default): situation C drops that
#'   fraction of the selected list itself (smallest filter statistic first);
#'   \code{"all"}: it cuts at the filter's quantile over all features and
#'   drops the selected features below it.
#' @return A data frame with one row per situation: \code{situation},
#'   \code{fraction}, \code{fdr}, \code{power}.
postfilter_compare <- function(sim, filter = "foldchange", pre = c(0.25, 0.5),
                               post = c(0.1, 0.2), alpha = 0.05, post_cut = c("selected", "all")) {
  post_cut <- match.arg(post_cut)
  tt <- row_ttest(sim$x, sim$group)
  stat <- filter_statistics(sim$x, sim$group, t = tt$statistic)[[filter]]
  row <- function(sit, fr, rej) {
    v <- achieved_fdr_power(rej, sim$null)
    data.frame(filter = filter, situation = sit, fraction = fr, fdr = v[["fdr"]], power = v[["power"]])
  }
  selA <- p.adjust(tt$p.value, "BH") <= alpha
  out <- list(row("A", 0, selA))
  for (fr in pre) {
    keep <- filter_keep(stat, fr)
    rej <- rep(FALSE, length(stat))
    rej[keep] <- p.adjust(tt$p.value[keep], "BH") <= alpha
    out[[length(out) + 1]] <- row("B", fr, rej)
  }
  for (fr in post) {
    rej <- selA
    if (any(selA)) {
      if (post_cut == "selected") {
        drop <- which(selA)[!filter_keep(stat[selA], fr)]
        rej[drop] <- FALSE
      } else {
        rej <- selA & filter_keep(stat, fr)
      }
    }
    out[[length(out) + 1]] <- row("C", fr, rej)
  }
  do.call(rbind, out)
}

#' Read a two-group data file
#'
#' Reads a CSV file with one row per feature: a \code{feature} column, an
#' optional logical \code{null} column (the truth, for simulated data), and
#' one numeric column per sample whose name starts with the group label
#' (\code{X1, X2, ..., Y1, Y2, ...}: the text before the first digit is the
#' group).
#'
#' @param file path of the CSV file.
#' @return A list with \code{x} (matrix), \code{group} (factor), \code{null}
#'   (logical or \code{NULL}) and \code{feature}.
read_two_group <- function(file) {
  d <- utils::read.csv(file, check.names = FALSE, stringsAsFactors = FALSE)
  if (!"feature" %in% names(d)) stop("the file needs a 'feature' column")
  cols <- setdiff(names(d), c("feature", "null"))
  group <- factor(sub("[0-9].*$", "", cols), levels = unique(sub("[0-9].*$", "", cols)))
  if (nlevels(group) != 2) stop("the sample columns must name exactly two groups, found: ",
                                paste(levels(group), collapse = ", "))
  x <- as.matrix(d[, cols])
  rownames(x) <- d$feature
  list(x = x, group = group, null = if ("null" %in% names(d)) as.logical(d$null) else NULL,
       feature = d$feature)
}

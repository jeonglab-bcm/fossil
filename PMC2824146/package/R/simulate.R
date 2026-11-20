# One replicate of the simulation, and the summaries over replicates.

replicate_seed <- function(...) {
  # A deterministic seed from integers: dataset, mechanism, level and method codes.
  v <- c(...)
  s <- 0
  for (k in v) s <- (s * 1000003 + k) %% 2147483647
  as.integer(s)
}

#' Run one replicate
#'
#' Simulates one cohort, analyses the full data, then for each mechanism and level imposes
#' missingness (the same cohort for every mechanism and level, different deletion seeds:
#' the paper's moderately independent strategy) and applies each method.
#' @param rep Replicate number (sets every seed).
#' @param params From [generation_parameters()].
#' @param mechanisms Named list: for each mechanism, the methods to run.
#' @param levels Overall shares of incomplete cases.
#' @param n Cases per cohort (paper: 1000).
#' @param m Imputations (paper: 20).
#' @return A data frame with one row per mechanism, level and method (and the full-data
#'   row, mechanism "NONE", level 0, method "FULL").
#' @export
run_replicate <- function(rep, params,
                          mechanisms = list(MAR = method_labels()),
                          levels = c(0.05, 0.10, 0.25, 0.50, 0.75), n = 1000, m = 20) {
  mech_code <- c(MCAR = 1, MAR = 2, MNAR = 3, COMBINED = 4)
  meth_code <- stats::setNames(seq_along(method_labels()), method_labels())
  x <- simulate_cohort(n, params, seed = replicate_seed(rep))
  rows <- list(cbind(data.frame(rep = rep, mechanism = "NONE", level = 0, method = "FULL",
                                stringsAsFactors = FALSE),
                     pool_fits(list(analyse_complete(x))),
                     censored = mean(x$status == 0)))
  for (mech in names(mechanisms)) {
    for (lev in levels) {
      xm <- impose_missing(x, mech, lev,
                           seed = replicate_seed(rep, mech_code[[mech]], round(100 * lev)))
      ind <- attr(xm, "indicators")
      for (meth in mechanisms[[mech]]) {
        res <- handle_missing(xm, meth, m = m,
                              seed = replicate_seed(rep, mech_code[[mech]],
                                                    round(100 * lev), meth_code[[meth]]))
        rows[[length(rows) + 1]] <- cbind(
          data.frame(rep = rep, mechanism = mech, level = lev, method = meth,
                     stringsAsFactors = FALSE),
          res, censored = mean(x$status == 0),
          incomplete = mean(rowSums(ind) > 0),
          miss_X3 = mean(ind[, "X3"]), miss_X2 = mean(ind[, "X2"]),
          miss_X5 = mean(ind[, "X5"]), miss_X8 = mean(ind[, "X8"]),
          both_X2X3 = mean(ind[, "X2"] & ind[, "X3"]),
          both_X5X2 = mean(ind[, "X5"] & ind[, "X2"]),
          both_X8X3 = mean(ind[, "X8"] & ind[, "X3"]))
      }
    }
  }
  out <- do.call(rbind, lapply(rows, function(r) {
    for (k in c("incomplete", "miss_X3", "miss_X2", "miss_X5", "miss_X8", "both_X2X3",
                "both_X5X2", "both_X8X3"))
      if (is.null(r[[k]])) r[[k]] <- NA_real_
    r
  }))
  rownames(out) <- NULL
  out
}

#' True values: complete-data fits over many cohorts
#'
#' The paper's true values are the mean coefficients and the empirical SE (the SD of the
#' estimates) over 20,000 cohorts without missing data.
#' @param reps Replicates, numbered from `first`.
#' @param params From [generation_parameters()].
#' @param n Cases per cohort.
#' @param first First replicate number; the seeds are those of [run_replicate()] shifted
#'   by 10^6, so the true-value cohorts are separate from the main ones.
#' @return A data frame with one row per replicate: the nine coefficients.
#' @export
true_value_fits <- function(reps, params, n = 1000, first = 1) {
  do.call(rbind, lapply(first - 1 + seq_len(reps), function(r) {
    x <- simulate_cohort(n, params, seed = replicate_seed(10^6 + r))
    b <- stats::coef(fit_full_cox(x))
    as.data.frame(as.list(stats::setNames(as.numeric(b), coef_names)))
  }))
}

#' Summarise replicates as in the paper's figures
#'
#' Per mechanism, level and method: the average estimate, bias and percentage bias from
#' the true value, average SE, coverage of the true value by the 95% interval, the mean
#' and median Wald p-value, and the model performance measures.
#' @param results Rows from [run_replicate()].
#' @param truth Named vector of true coefficients.
#' @return A long data frame (one row per group and quantity).
#' @export
summarise_replicates <- function(results, truth) {
  key <- unique(results[, c("mechanism", "level", "method")])
  out <- list()
  for (i in seq_len(nrow(key))) {
    g <- results[results$mechanism == key$mechanism[i] & results$level == key$level[i] &
                   results$method == key$method[i], ]
    add <- function(variable, quantity, value, mcse = NA_real_) {
      out[[length(out) + 1]] <<- data.frame(mechanism = key$mechanism[i],
        level = key$level[i], method = key$method[i], variable = variable,
        quantity = quantity, value = value, mcse = mcse, reps = nrow(g),
        stringsAsFactors = FALSE)
    }
    for (v in coef_names) {
      e <- g[[paste0("est_", v)]]
      s <- g[[paste0("se_", v)]]
      cov <- g[[paste0("lo_", v)]] <= truth[[v]] & truth[[v]] <= g[[paste0("hi_", v)]]
      p <- g[[paste0("p_", v)]]
      add(v, "estimate", mean(e), stats::sd(e) / sqrt(length(e)))
      add(v, "bias", mean(e) - truth[[v]], stats::sd(e) / sqrt(length(e)))
      add(v, "pct_bias", 100 * (mean(e) - truth[[v]]) / abs(truth[[v]]),
          100 * stats::sd(e) / sqrt(length(e)) / abs(truth[[v]]))
      add(v, "se", mean(s), stats::sd(s) / sqrt(length(s)))
      add(v, "coverage", 100 * mean(cov), 100 * sqrt(mean(cov) * (1 - mean(cov)) / length(cov)))
      add(v, "p_mean", mean(p), stats::sd(p) / sqrt(length(p)))
      add(v, "p_median", stats::median(p))
    }
    for (q in c("lr_p", "r2", "d", "surv")) {
      add("model", q, mean(g[[q]]), stats::sd(g[[q]]) / sqrt(nrow(g)))
    }
    add("model", "censored", mean(g$censored))
    if (!all(is.na(g$incomplete))) {
      for (q in c("incomplete", "miss_X3", "miss_X2", "miss_X5", "miss_X8", "both_X2X3",
                  "both_X5X2", "both_X8X3"))
        add("design", q, mean(g[[q]]), stats::sd(g[[q]]) / sqrt(nrow(g)))
    }
  }
  do.call(rbind, out)
}

#' Path of a bundled example file
#' @param name File name in `inst/extdata`.
#' @return The full path.
#' @export
example_path <- function(name) {
  p <- system.file("extdata", name, package = "misscox")
  if (!nzchar(p)) stop("no example file named ", name)
  p
}

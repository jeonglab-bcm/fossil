seed_of <- function(name) {
  codes <- utf8ToInt(name)
  # A stable integer from the setting name; each replicate adds its number.
  (sum(codes * seq_along(codes) * 131L) %% 200000L) * 10000L
}

#' A simulation setting
#'
#' @param name unique name; it sets the random seeds.
#' @param p,p_de,mu2 see [simulate_data()].
#' @param k1train proportion of Class 1 in the training set.
#' @param ntrain training-set size (80 in the paper).
#' @param tests list of test designs, each `list(id, ntest, k1test)`.
#' @param G variables selected (40, or `p` for no selection).
#' @param center "samples", "variables" or "none".
#' @param correction "none", "over", "down" or "multds".
#' @param methods classifier names.
#' @param B down-sized sets for MultDS.
#' @export
simulation_settings <- function(name, p, k1train, p_de = 0, mu2 = 0, ntrain = 80,
                                tests = list(list(id = "bal20", ntest = 20, k1test = 0.5)),
                                G = 40, center = "samples", correction = "none",
                                methods = classifier_names(), B = 101) {
  list(name = name, p = p, p_de = p_de, mu2 = mu2, k1train = k1train, ntrain = ntrain,
       tests = tests, G = G, center = center, correction = correction, methods = methods, B = B)
}

#' One replicate of a simulation setting
#'
#' Draws a training set and every test set, centers each separately, applies the correction,
#' selects variables on the training set, trains the classifiers once and evaluates them on each
#' test set. The seed is set from the setting's name and the replicate number, so any replicate can
#' be rerun on its own.
#'
#' @param s a setting from [simulation_settings()].
#' @param rep replicate number.
#' @return A data frame with one row per test design and classifier: PA, PA1, PA2, PV1, PV2, AUC,
#'   and `nsel_de`, the number of selected variables that truly differ.
#' @export
run_replicate <- function(s, rep) {
  set.seed(seed_of(s$name) + rep, kind = "Mersenne-Twister", normal.kind = "Inversion",
           sample.kind = "Rejection")
  n1 <- round(s$ntrain * s$k1train)
  tr <- simulate_data(n1, s$ntrain - n1, s$p, s$p_de, s$mu2)
  tests <- lapply(s$tests, function(d) {
    m1 <- round(d$ntest * d$k1test)
    simulate_data(m1, d$ntest - m1, s$p, s$p_de, s$mu2)
  })
  sample_center <- if (s$center == "samples") "samples" else "none"
  xtr <- center_data(tr$x, sample_center)
  ytr <- tr$y
  xte <- do.call(rbind, lapply(tests, function(d) center_data(d$x, s$center)))
  yte <- unlist(lapply(tests, `[[`, "y"))
  grp <- rep(seq_along(tests), vapply(tests, function(d) length(d$y), 1L))

  if (s$correction == "multds") {
    fp <- multds_predict(s$methods, xtr, ytr, xte, G = s$G, B = s$B,
                         center = if (s$center == "variables") "variables" else "none")
    nsel <- NA_integer_
  } else {
    idx <- switch(s$correction, none = seq_along(ytr), over = oversample(ytr),
                  down = downsize(ytr), stop("unknown correction"))
    xc <- xtr[idx, , drop = FALSE]
    yc <- ytr[idx]
    if (s$center == "variables") xc <- center_data(xc, "variables")
    sel <- select_variables(xc, yc, s$G)
    nsel <- sum(sel <= s$p_de)
    fp <- fit_predict(s$methods, xc[, sel, drop = FALSE], yc, xte[, sel, drop = FALSE])
  }
  kappa1 <- n1 / s$ntrain
  rows <- list()
  for (g in seq_along(tests)) {
    i <- grp == g
    for (m in s$methods) {
      ev <- evaluate(yte[i], fp[[m]]$pred[i], fp[[m]]$score[i], kappa1)
      rows[[length(rows) + 1]] <- data.frame(test = s$tests[[g]]$id, method = m, rep = rep,
                                             t(ev), nsel_de = nsel, check.names = FALSE)
    }
  }
  do.call(rbind, rows)
}

#' Run every replicate of a setting
#' @param s a setting.
#' @param reps replicate numbers.
#' @param cores parallel workers (forked; 1 on Windows).
#' @export
run_setting <- function(s, reps, cores = 1) {
  f <- function(r) run_replicate(s, r)
  res <- if (cores > 1 && .Platform$OS.type == "unix") {
    parallel::mclapply(reps, f, mc.cores = cores, mc.preschedule = TRUE)
  } else {
    lapply(reps, f)
  }
  bad <- vapply(res, inherits, TRUE, what = "try-error")
  if (any(bad)) stop(as.character(res[[which(bad)[1]]]))
  out <- do.call(rbind, res)
  out$setting <- s$name
  out
}

#' Mean, SD and 95\% prediction interval over replicates
#'
#' Means keep NA when any replicate is NA (as the paper's tables show NA for PV1), and
#' `mean_avail` averages the replicates where the value exists.
#' @param runs output of [run_setting()].
#' @export
summarize_runs <- function(runs) {
  metrics <- c("PA", "PA1", "PA2", "PV1", "PV2", "AUC")
  keys <- unique(runs[, c("setting", "test", "method")])
  out <- list()
  for (k in seq_len(nrow(keys))) {
    r <- runs[runs$setting == keys$setting[k] & runs$test == keys$test[k] &
                runs$method == keys$method[k], ]
    for (m in metrics) {
      v <- r[[m]]
      out[[length(out) + 1]] <- data.frame(
        setting = keys$setting[k], test = keys$test[k], method = keys$method[k], metric = m,
        n = length(v), n_na = sum(is.na(v)), mean = mean(v), mean_avail = mean(v, na.rm = TRUE),
        sd = sd(v, na.rm = TRUE),
        q025 = unname(quantile(v, 0.025, na.rm = TRUE, type = 7)),
        q975 = unname(quantile(v, 0.975, na.rm = TRUE, type = 7)))
    }
  }
  do.call(rbind, out)
}

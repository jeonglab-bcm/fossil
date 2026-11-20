# Missing data methods (Table 4).

#' The missing data methods of Table 4
#' @return A character vector of method labels.
#' @export
method_labels <- function() {
  c("CC", "SI", "NORM", "MIX", "MIX_notrunc", "MICE", "MICE_PMM", "MICE_PMM_notrans",
    "AREG")
}

prepare_imputation <- function(x, transform = TRUE) {
  data.frame(X1 = x$X1,
             X2t = if (transform) log(x$X2) else x$X2,
             X3t = if (transform) log(x$X3 + 1) else x$X3,
             X4 = x$X4, X5 = x$X5, X6 = x$X6, X7 = x$X7, X8g = x$X8g,
             logt = log(x$time), status = x$status)
}

# Back-transform an imputed frame to the analysis scale; clip the incomplete continuous
# covariates to the range observed in the incomplete data when `truncate`, and round the
# binary and categorical covariates to the nearest valid code.
complete_from <- function(imp, x, transform = TRUE, truncate = TRUE) {
  x2 <- if (transform) exp(imp$X2t) else imp$X2t
  x3 <- if (transform) exp(imp$X3t) - 1 else imp$X3t
  if (truncate) {
    r2 <- range(x$X2, na.rm = TRUE)
    r3 <- range(x$X3, na.rm = TRUE)
    x2 <- pmin(pmax(x2, r2[1]), r2[2])
    x3 <- pmin(pmax(x3, r3[1]), r3[2])
  }
  x5 <- as.numeric(as.character(imp$X5))
  x8 <- as.numeric(as.character(imp$X8g))
  data.frame(X1 = x$X1, X2 = x2, X3 = x3, X4 = x$X4,
             X5 = pmin(pmax(round(x5), 0), 1), X6 = x$X6, X7 = x$X7,
             X8g = pmin(pmax(round(x8), 1), 3), time = x$time, status = x$status)
}

impute_mice <- function(x, m, maxit, method, transform, seed) {
  d <- prepare_imputation(x, transform)
  meth <- c(X2t = "pmm", X3t = "pmm", X5 = "pmm", X8g = "pmm")
  if (method == "norm") {
    d$X5 <- factor(d$X5, levels = 0:1)
    d$X8g <- factor(d$X8g, levels = 1:3)
    meth <- c(X2t = "norm", X3t = "norm", X5 = "logreg", X8g = "polyreg")
  }
  mv <- stats::setNames(rep("", ncol(d)), names(d))
  mv[names(meth)] <- meth
  mv[colSums(is.na(d)) == 0] <- ""
  imp <- mice::mice(d, m = m, maxit = maxit, method = mv, seed = seed, printFlag = FALSE)
  lapply(seq_len(m), function(i) complete_from(mice::complete(imp, i), x, transform,
                                               truncate = method == "norm"))
}

impute_areg <- function(x, m, burnin, seed) {
  d <- prepare_imputation(x, TRUE)
  d$X5 <- factor(d$X5, levels = 0:1)
  d$X8g <- factor(d$X8g, levels = 1:3)
  set.seed(seed, kind = "Mersenne-Twister", normal.kind = "Inversion")
  a <- Hmisc::aregImpute(~ X1 + X2t + X3t + X4 + X5 + X6 + X7 + X8g + logt + status,
                         data = d, n.impute = m, burnin = burnin, type = "pmm",
                         pr = FALSE)
  lapply(seq_len(m), function(i) {
    di <- d
    for (v in names(a$imputed)) {
      ii <- a$imputed[[v]]
      if (is.null(ii) || length(ii) == 0) next
      rows <- as.integer(rownames(ii))
      vals <- ii[, i]
      if (is.factor(d[[v]])) vals <- levels(d[[v]])[vals]
      if (is.factor(di[[v]])) di[[v]] <- as.character(di[[v]])
      di[[v]][rows] <- vals
    }
    complete_from(di, x, TRUE, truncate = TRUE)
  })
}

impute_norm <- function(x, m, steps, seed) {
  d <- as.matrix(prepare_imputation(x, TRUE))
  s <- norm::prelim.norm(d)
  th <- norm::em.norm(s, showits = FALSE)
  norm::rngseed(seed)
  lapply(seq_len(m), function(i) {
    th <<- norm::da.norm(s, th, steps = steps, showits = FALSE, return.ymis = FALSE)
    complete_from(as.data.frame(norm::imp.norm(s, th, d)), x, TRUE, truncate = TRUE)
  })
}

impute_mix <- function(x, m, steps, seed, truncate) {
  p <- prepare_imputation(x, TRUE)
  d <- cbind(X5 = p$X5 + 1, X6 = p$X6 + 1, X7 = p$X7 + 1, X8g = p$X8g,
             status = p$status + 1, X1 = p$X1, X2t = p$X2t, X3t = p$X3t, X4 = p$X4,
             logt = p$logt)
  s <- mix::prelim.mix(d, 5)
  # Restricted general location model (Schafer 1997, ch. 9): a loglinear model with all
  # two-way associations among the five categorical variables, and continuous means
  # additive in them. The unrestricted model leaves empty cells with improper posteriors.
  cells <- expand.grid(X5 = 1:2, X6 = 1:2, X7 = 1:2, X8g = 1:3, status = 1:2)
  design <- stats::model.matrix(~ factor(X5) + factor(X6) + factor(X7) + factor(X8g) +
                                  factor(status), cells)
  pairs <- utils::combn(5, 2)
  margins <- as.vector(rbind(pairs, 0))
  margins <- margins[-length(margins)]
  th <- mix::ecm.mix(s, margins, design, showits = FALSE)
  mix::rngseed(seed)
  lapply(seq_len(m), function(i) {
    th <<- mix::dabipf.mix(s, margins, design, th, steps = steps, showits = FALSE)
    im <- as.data.frame(mix::imp.mix(s, th, d))
    im$X5 <- im$X5 - 1
    im$X6 <- im$X6 - 1
    im$X7 <- im$X7 - 1
    im$status <- im$status - 1
    complete_from(im, x, TRUE, truncate = truncate)
  })
}

#' Handle the missing data with one method and analyse
#'
#' @param x Incomplete data from [impose_missing()].
#' @param method One of [method_labels()].
#' @param m Number of imputations (paper: 20).
#' @param seed Seed for the imputation.
#' @param iterations Named iterations per method (Table 4 by default).
#' @return A one-row data frame from [pool_fits()].
#' @export
handle_missing <- function(x, method, m = 20, seed = 1,
                           iterations = c(SI = 20, NORM = 100, MIX = 100, MICE = 20,
                                          AREG = 1)) {
  fits <- switch(method,
    CC = list(x[stats::complete.cases(x[, c("X2", "X3", "X5", "X8g")]), ]),
    SI = impute_mice(x, 1, iterations[["SI"]], "pmm", TRUE, seed),
    NORM = impute_norm(x, m, iterations[["NORM"]], seed),
    MIX = impute_mix(x, m, iterations[["MIX"]], seed, truncate = TRUE),
    MIX_notrunc = impute_mix(x, m, iterations[["MIX"]], seed, truncate = FALSE),
    MICE = impute_mice(x, m, iterations[["MICE"]], "norm", TRUE, seed),
    MICE_PMM = impute_mice(x, m, iterations[["MICE"]], "pmm", TRUE, seed),
    MICE_PMM_notrans = impute_mice(x, m, iterations[["MICE"]], "pmm", FALSE, seed),
    AREG = impute_areg(x, m, iterations[["AREG"]], seed),
    stop("unknown method: ", method))
  pool_fits(lapply(fits, analyse_complete))
}

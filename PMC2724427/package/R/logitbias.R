#' logitbias: small-sample bias of logistic regression coefficients
#'
#' Rebuilds the simulation study of Nemes S, Jonasson JM, Genell A, Steineck G. Bias in odds
#' ratios by logistic regression modelling and sample size. BMC Medical Research Methodology
#' 9:56 (2009), doi:10.1186/1471-2288-9-56. The authors released no code; the population
#' generator follows the R lines of the paper's Additional file 1, and the rest is implemented
#' from the paper's text.
#'
#' @name logitbias
#' @keywords internal
#' @importFrom stats rnorm rbinom runif plogis glm.fit binomial quantile sd pt var
"_PACKAGE"

#' Simulate the study population of Nemes et al. (2009)
#'
#' Runs the R lines of the paper's Additional file 1, in their order: x is normal, z is
#' Bernoulli with a probability that depends on whether x exceeds a cut, and y is 1 when a
#' uniform draw falls below plogis(theta). With the defaults, this is the paper's population.
#'
#' @param N population size.
#' @param seed integer seed for set.seed(), or NULL to use the current RNG state.
#' @param intercept,beta_x,beta_z coefficients of the linear predictor theta.
#' @param x_mean,x_sd mean and standard deviation of x.
#' @param x_cut,p_z z ~ Bernoulli(p_z[2]) when x > x_cut, else Bernoulli(p_z[1]).
#' @return a data frame with columns y, x and z.
#' @export
simulate_population <- function(N = 100000, seed = NULL, intercept = 0.1, beta_x = 2,
                                beta_z = -0.9, x_mean = 2, x_sd = 0.7, x_cut = 2.5,
                                p_z = c(0.4, 0.6)) {
  if (!is.numeric(N) || length(N) != 1 || N < 10) stop("N must be a number of at least 10")
  if (!is.null(seed)) set.seed(seed)
  x <- rnorm(N, x_mean, x_sd)
  z <- ifelse(x > x_cut, rbinom(N, 1, p_z[2]), rbinom(N, 1, p_z[1]))
  theta <- intercept + beta_x * x + beta_z * z
  y <- ifelse(runif(N) < plogis(theta), 1, 0)
  data.frame(y = y, x = x, z = z)
}

#' Fit a logistic regression and flag samples without a finite estimate
#'
#' Calls glm.fit() with the binomial family and its default control. The status is, in this
#' order of precedence: "not_converged" when the iterations did not converge; "separated" when
#' R warns that fitted probabilities numerically 0 or 1 occurred; "boundary" when a fitted
#' probability lies within `boundary` of 0 or 1 without that warning (quasi-complete separation,
#' where the coefficients are still growing when the iterations stop); "ok" otherwise. In the
#' first three cases the maximum likelihood estimate does not exist or was not reached.
#'
#' @param X model matrix with an intercept column.
#' @param y 0/1 outcome.
#' @param boundary distance from 0 or 1 below which a fitted probability flags the sample.
#' @return a list with coefficients and status.
#' @export
fit_logistic <- function(X, y, boundary = 1e-8) {
  if (!is.matrix(X) || nrow(X) != length(y)) stop("X must be a matrix with one row per outcome")
  if (!all(y %in% c(0, 1))) stop("y must be 0 or 1")
  sep <- FALSE
  conv <- TRUE
  fit <- withCallingHandlers(
    glm.fit(X, y, family = binomial()),
    warning = function(w) {
      msg <- conditionMessage(w)
      if (grepl("fitted probabilities numerically 0 or 1", msg)) sep <<- TRUE
      if (grepl("did not converge", msg)) conv <<- FALSE
      invokeRestart("muffleWarning")
    })
  p <- fit$fitted.values
  status <- if (!conv || !isTRUE(fit$converged)) "not_converged" else if (sep) "separated" else
    if (any(p < boundary | p > 1 - boundary)) "boundary" else "ok"
  list(coefficients = fit$coefficients, status = status)
}

.skew <- function(v) {
  m <- mean(v)
  s2 <- mean((v - m)^2)
  if (s2 == 0) return(NA_real_)
  mean((v - m)^3) / s2^1.5
}

#' Estimate logistic regression coefficients over repeated samples of each size
#'
#' For each sample size n, draws `reps` simple random samples without replacement from the
#' population (sample(nrow(population), n), as in Additional file 1), fits y on the other
#' columns, and summarises each coefficient. Each sample size gets its own seed, derived from
#' `seed` and n, so the result does not depend on the number of cores.
#'
#' @param population data frame with a 0/1 column y and the covariates.
#' @param sizes sample sizes.
#' @param reps samples per size.
#' @param seed integer seed.
#' @param drop which fits to leave out (see fit_logistic()): "boundary" leaves out every fit
#'   whose status is not "ok"; "warning" only those for which R warned (separated or
#'   not_converged); "none" keeps every fit.
#' @param boundary passed to fit_logistic().
#' @param keep sample sizes whose individual estimates are returned, or TRUE for all.
#' @param cores number of processes (parallel::mclapply).
#' @return a list: `summary` (one row per size and coefficient: mean, sd, var, median, q1, q3,
#'   skewness, used, dropped and the count of each status; mean_warning and mean_all, the mean
#'   under the other two rules) and `samples` (individual estimates for `keep`).
#' @export
bias_simulation <- function(population, sizes = seq(100, 1500, 5), reps = 1000, seed = 1,
                            drop = c("boundary", "warning", "none"), keep = NULL, cores = 1,
                            boundary = 1e-8) {
  drop <- match.arg(drop)
  if (!"y" %in% names(population)) stop("population needs a 0/1 column y")
  N <- nrow(population)
  if (any(sizes > N) || any(sizes < 3)) stop("sizes must lie between 3 and nrow(population)")
  X <- cbind(`(Intercept)` = 1, as.matrix(population[setdiff(names(population), "y")]))
  y <- population$y
  terms <- colnames(X)[-1]
  one <- function(n) {
    old <- RNGkind("Mersenne-Twister", "Inversion", "Rejection")
    on.exit(RNGkind(old[1], old[2], old[3]))
    set.seed(as.integer((as.numeric(seed) * 10007 + n) %% 2147483647))
    est <- matrix(NA_real_, reps, length(terms), dimnames = list(NULL, terms))
    status <- character(reps)
    for (r in seq_len(reps)) {
      i <- sample(N, n)
      f <- fit_logistic(X[i, , drop = FALSE], y[i], boundary)
      est[r, ] <- f$coefficients[-1]
      status[r] <- f$status
    }
    warned <- status %in% c("separated", "not_converged")
    ok <- switch(drop, boundary = status == "ok", warning = !warned, none = rep(TRUE, reps))
    rows <- lapply(terms, function(tm) {
      v <- est[ok, tm]
      q <- quantile(v, c(0.25, 0.5, 0.75), names = FALSE, type = 7)
      data.frame(n = n, term = tm, mean = mean(v), sd = sd(v), var = var(v), median = q[2],
                 q1 = q[1], q3 = q[3], skewness = .skew(v), used = sum(ok),
                 dropped = sum(!ok), boundary = sum(status == "boundary"),
                 separated = sum(status == "separated"),
                 not_converged = sum(status == "not_converged"),
                 mean_warning = mean(est[!warned, tm]), mean_all = mean(est[, tm]))
    })
    smp <- NULL
    if (isTRUE(keep) || n %in% keep) {
      smp <- data.frame(n = n, rep = seq_len(reps), status = status, est, check.names = FALSE)
    }
    list(summary = do.call(rbind, rows), samples = smp)
  }
  res <- if (cores > 1) parallel::mclapply(sizes, one, mc.cores = cores) else lapply(sizes, one)
  bad <- vapply(res, inherits, logical(1), "try-error")
  if (any(bad)) stop("a worker failed: ", as.character(res[bad][[1]]))
  out <- list(summary = do.call(rbind, lapply(res, `[[`, "summary")),
              samples = do.call(rbind, lapply(res, `[[`, "samples")))
  rownames(out$summary) <- NULL
  if (!is.null(out$samples)) rownames(out$samples) <- NULL
  out
}

#' Fit the first-order bias curve: mean estimate = beta + b1 / n
#'
#' Ordinary least squares of each coefficient on 1/n (Equation 2 of the paper). With
#' `data = "means"` the points are the per-size mean estimates; with `data = "all"` they are
#' all individual estimates, computed exactly from the per-size count, mean and variance.
#'
#' @param summary the `summary` of bias_simulation(), or any data frame with columns n, term,
#'   mean (and used and var for data = "all").
#' @param data "means" or "all".
#' @return a data frame with one row per term and parameter (intercept, inv_n): estimate, se,
#'   t, p, r2, df.
#' @export
fit_bias_curve <- function(summary, data = c("means", "all")) {
  data <- match.arg(data)
  need <- c("n", "term", "mean", if (data == "all") c("used", "var"))
  miss <- setdiff(need, names(summary))
  if (length(miss)) stop("summary lacks column(s): ", paste(miss, collapse = ", "))
  out <- lapply(unique(summary$term), function(tm) {
    d <- summary[summary$term == tm, ]
    if (nrow(d) < 3) stop("need at least three sample sizes")
    u <- 1 / d$n
    m <- if (data == "all") d$used else rep(1, nrow(d))
    U <- cbind(1, u)
    A <- crossprod(U * m, U)
    b <- solve(A, crossprod(U * m, d$mean))
    fitted <- drop(U %*% b)
    within <- if (data == "all") sum((d$used - 1) * d$var) else 0
    ssres <- sum(m * (d$mean - fitted)^2) + within
    grand <- sum(m * d$mean) / sum(m)
    sstot <- sum(m * (d$mean - grand)^2) + within
    df <- sum(m) - 2
    se <- sqrt(diag(solve(A)) * ssres / df)
    tval <- drop(b) / se
    data.frame(term = tm, param = c("intercept", "inv_n"), estimate = drop(b), se = se,
               t = tval, p = 2 * pt(-abs(tval), df), r2 = 1 - ssres / sstot, df = df,
               points = if (data == "all") "all" else "means")
  })
  res <- do.call(rbind, out)
  rownames(res) <- NULL
  res
}

#' Analytic first-order bias of the logistic regression coefficients
#'
#' The O(1/n) bias of the maximum likelihood estimator (Cordeiro and McCullagh 1991; Firth
#' 1993) for samples drawn at random from a population: bias = b1 / n with
#' b1 = M^-1 E[x w (x' M^-1 x) (p - 1/2)], M = E[w x x'], w = p (1 - p).
#'
#' @param population data frame with y and the covariates.
#' @param beta coefficients (intercept first) at which to evaluate p; NULL uses the logistic
#'   fit to the whole population.
#' @return a named vector b1 (intercept and covariates).
#' @export
analytic_bias <- function(population, beta = NULL) {
  X <- cbind(`(Intercept)` = 1, as.matrix(population[setdiff(names(population), "y")]))
  if (is.null(beta)) beta <- glm.fit(X, population$y, family = binomial())$coefficients
  if (length(beta) != ncol(X)) stop("beta needs one value per column of the model matrix")
  p <- plogis(drop(X %*% beta))
  w <- p * (1 - p)
  M <- crossprod(X * w, X) / nrow(X)
  Mi <- solve(M)
  q <- rowSums((X %*% Mi) * X)
  b1 <- drop(Mi %*% colMeans(X * (w * q * (p - 0.5))))
  names(b1) <- colnames(X)
  b1
}

#' Bias-corrected estimate: estimate - b1 / n
#'
#' @param estimate coefficient estimate(s).
#' @param b1 first-order bias coefficient(s).
#' @param n sample size(s).
#' @return the corrected estimate(s).
#' @export
bias_correct <- function(estimate, b1, n) {
  if (any(n <= 0)) stop("n must be positive")
  estimate - b1 / n
}

#' Path to a file bundled with the package
#'
#' @param name file name in inst/extdata; NULL lists the files.
#' @return a file path, or the bundled file names.
#' @export
example_path <- function(name = NULL) {
  if (is.null(name)) return(dir(system.file("extdata", package = "logitbias")))
  p <- system.file("extdata", name, package = "logitbias")
  if (p == "") stop("no bundled file ", name)
  p
}

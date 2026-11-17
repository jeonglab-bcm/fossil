# Data generation (Methods, "Generating the datasets").

#' The paper's linear predictor coefficients
#'
#' From the Methods equation of Marshall et al. (2010): the full Cox model fitted to the
#' breast cancer data, printed to two significant figures.
#' @return A named numeric vector (X1 to X7, X8d1, X8d2).
#' @export
paper_coefficients <- function() {
  c(X1 = -0.0088, X2 = 0.051, X3 = -0.0023, X4 = 0.00015, X5 = -0.349, X6 = 0.225,
    X7 = 0.67, X8d1 = 0.223, X8d2 = 0.331)
}

#' Parameters of the data generation
#'
#' Means and covariance of the transformed covariates of the motivating data, the
#' observed upper limits used for truncation, the coefficients and the hazards.
#' @param covariates A data frame from [gbsg_covariates()].
#' @param coefficients Linear predictor coefficients; the paper's by default.
#' @param event_hazard,censor_hazard Exponential hazards per day (paper: 0.00027 and 0.0002).
#' @param lower_zero Set back-transformed X3 and X4 below 0 to 0 (an assumption: the
#'   paper states upper limits only, and log(X + 1) can return values in (-1, 0)).
#' @param binaries "cut" (the paper's text: the binary covariates are the multivariate
#'   normal draw cut at 0.5, which weakens their correlations with the other covariates)
#'   or "preserve" (the covariances of the binaries are divided by the attenuation of
#'   the cut, so the generated binaries keep about the observed correlations; a
#'   sensitivity variant, not stated in the paper).
#' @return A list used by [simulate_cohort()].
#' @export
generation_parameters <- function(covariates, coefficients = paper_coefficients(),
                                  event_hazard = 0.00027, censor_hazard = 0.0002,
                                  lower_zero = TRUE, binaries = c("cut", "preserve")) {
  binaries <- match.arg(binaries)
  tr <- as.matrix(transform_covariates(covariates))
  s <- stats::cov(tr)
  mu <- colMeans(tr)
  if (binaries == "preserve") {
    for (j in c("X5", "X6", "X7")) {
      k <- match(j, colnames(s))
      z <- (0.5 - mu[[j]]) / sqrt(s[k, k])
      p <- 1 - stats::pnorm(z)
      a <- stats::dnorm(z) / sqrt(p * (1 - p))
      s[k, -k] <- s[k, -k] / a
      s[-k, k] <- s[-k, k] / a
    }
  }
  list(mean = mu, cov = s,
       upper = c(X1 = max(covariates$X1), X2 = max(covariates$X2),
                 X3 = max(covariates$X3), X4 = max(covariates$X4),
                 X8 = max(covariates$X8)),
       coefficients = coefficients, event_hazard = event_hazard,
       censor_hazard = censor_hazard, lower_zero = lower_zero)
}

#' Simulate one cohort
#'
#' Multivariate normal covariates on the transformed scale, back-transformed, truncated at
#' the observed upper limits, binaries cut at 0.5, tumour size grouped at 20 and 30 mm;
#' exponential event and censoring times (Bender et al. 2005).
#' @param n Number of cases (paper: 1000).
#' @param params From [generation_parameters()].
#' @param seed Optional seed; the random number state is restored afterwards.
#' @return A data frame with X1 to X7, X8g (group 1 to 3), time, status and the linear
#'   predictor `lp`.
#' @export
simulate_cohort <- function(n, params, seed = NULL) {
  if (!is.null(seed)) {
    old <- if (exists(".Random.seed", globalenv())) get(".Random.seed", globalenv()) else NULL
    on.exit(if (is.null(old)) rm(".Random.seed", envir = globalenv()) else
      assign(".Random.seed", old, envir = globalenv()))
    set.seed(seed, kind = "Mersenne-Twister", normal.kind = "Inversion")
  }
  p <- length(params$mean)
  z <- matrix(stats::rnorm(n * p), n, p) %*% chol(params$cov)
  z <- sweep(z, 2, params$mean, "+")
  colnames(z) <- names(params$mean)
  up <- params$upper
  x <- data.frame(
    X1 = pmin(z[, "X1"], up["X1"]),
    X2 = pmin(exp(z[, "X2"]), up["X2"]),
    X3 = pmin(exp(z[, "X3"]) - 1, up["X3"]),
    X4 = pmin(exp(z[, "X4"]) - 1, up["X4"]),
    X5 = as.integer(z[, "X5"] > 0.5),
    X6 = as.integer(z[, "X6"] > 0.5),
    X7 = as.integer(z[, "X7"] > 0.5),
    X8g = size_group(pmin(exp(z[, "X8"]), up["X8"]))
  )
  if (isTRUE(params$lower_zero)) {
    x$X3 <- pmax(x$X3, 0)
    x$X4 <- pmax(x$X4, 0)
  }
  b <- params$coefficients
  lp <- b["X1"] * x$X1 + b["X2"] * x$X2 + b["X3"] * x$X3 + b["X4"] * x$X4 +
    b["X5"] * x$X5 + b["X6"] * x$X6 + b["X7"] * x$X7 +
    b["X8d1"] * (x$X8g == 2) + b["X8d2"] * (x$X8g == 3)
  lp <- as.numeric(lp)
  t_event <- -log(stats::runif(n)) / (params$event_hazard * exp(lp))
  t_cens <- -log(stats::runif(n)) / params$censor_hazard
  x$time <- pmin(t_event, t_cens)
  x$status <- as.integer(t_event <= t_cens)
  x$lp <- lp
  x
}

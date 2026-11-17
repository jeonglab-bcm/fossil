#' Bitriangular distribution
#'
#' The symmetric bitriangular effect-size distribution of Langaas, Lindqvist
#' and Ferkingstad (2005): on each side of zero a triangle on \code{[a, b]}
#' with its mode at \code{m}, each side holding half of the mass. The
#' defaults are the values the first author's SSPA package uses for the
#' same simulation design (\code{log2(1.2)}, \code{log2(4)}, \code{log2(2)}).
#'
#' @param x,q vector of values.
#' @param p vector of probabilities.
#' @param n number of draws.
#' @param a,b inner and outer end of each triangle (0 < a < m < b).
#' @param m mode of each triangle.
#' @return \code{dbitri} the density, \code{pbitri} the distribution
#'   function, \code{qbitri} the quantile function, \code{rbitri} random
#'   draws (by inversion of \code{runif(n)}).
#' @name bitriangular
#' @examples
#' curve(dbitri, -2.5, 2.5, n = 1001)
#' mean(abs(rbitri(1000)))
NULL

#' @rdname bitriangular
dbitri <- function(x, a = log2(1.2), b = log2(4), m = log2(2)) {
  ax <- abs(x)
  y <- numeric(length(x))
  i <- ax >= a & ax < m
  y[i] <- (ax[i] - a) / ((b - a) * (m - a))
  i <- ax >= m & ax <= b
  y[i] <- (b - ax[i]) / ((b - a) * (b - m))
  y  # each triangle holds mass 1/2, so its peak height is 1/(b - a)
}

#' @rdname bitriangular
pbitri <- function(q, a = log2(1.2), b = log2(4), m = log2(2)) {
  half <- function(x) {                       # mass of (0, x] on the positive side, x >= 0
    out <- numeric(length(x))
    i <- x >= a & x < m
    out[i] <- (x[i] - a)^2 / (2 * (b - a) * (m - a))
    i <- x >= m & x < b
    out[i] <- 0.5 - (b - x[i])^2 / (2 * (b - a) * (b - m))
    out[x >= b] <- 0.5
    out
  }
  ifelse(q >= 0, 0.5 + half(q), 0.5 - half(-q))
}

#' @rdname bitriangular
qbitri <- function(p, a = log2(1.2), b = log2(4), m = log2(2)) {
  y <- numeric(length(p))
  lo <- (b - m) / (2 * (b - a))               # pbitri(-m)
  hi <- 1 - lo                                # pbitri(m)
  i <- p >= 0 & p < lo
  y[i] <- -b + sqrt(p[i] * 2 * (b - a) * (b - m))
  i <- p >= lo & p < 0.5
  y[i] <- -a - sqrt((0.5 - p[i]) * 2 * (b - a) * (m - a))
  i <- p > 0.5 & p <= hi
  y[i] <- a + sqrt((p[i] - 0.5) * 2 * (b - a) * (m - a))
  i <- p > hi & p < 1
  y[i] <- b - sqrt((1 - p[i]) * 2 * (b - a) * (b - m))
  y[p >= 1] <- b
  y
}

#' @rdname bitriangular
rbitri <- function(n, a = log2(1.2), b = log2(4), m = log2(2)) {
  qbitri(runif(n), a = a, b = b, m = m)
}

#' Simulate two-group expression data
#'
#' The simulation of Additional File 1, section 8: \code{m} features,
#' \code{n} samples per group; the first \code{m0 = as.integer(m * pi0)}
#' features are null, the others have a group difference \code{mu} drawn
#' from the bitriangular distribution. Group X is
#' \code{log(exp(R) + exp(eps))} with \code{R ~ N(mu/2, 1)}, group Y the same
#' with \code{-mu/2}. The draws follow the order of the first author's
#' \code{SSPA::simdat}, so the same seed gives the same data.
#'
#' @param m number of features.
#' @param pi0 proportion of null features.
#' @param n samples per group.
#' @param noise_sd standard deviation of the additive noise \code{eps};
#'   \code{NULL} or 0 for none. The paper writes \code{N(0, 0.01)}; 0.1
#'   reads 0.01 as the variance.
#' @param noise \code{"feature"}: one noise draw per feature and group,
#'   shared by the samples of the group (as in \code{SSPA::simdat});
#'   \code{"value"}: one draw per measured value.
#' @param mu effect sizes of the non-null features (default: bitriangular
#'   draws).
#' @param ... passed to \code{rbitri}.
#' @return A list with \code{x} (m x 2n matrix, columns X then Y),
#'   \code{group} (factor), \code{null} (logical) and \code{mu}.
simulate_two_group <- function(m = 5000, pi0 = 0.8, n = 10, noise_sd = 0.1,
                               noise = c("feature", "value"), mu = NULL, ...) {
  noise <- match.arg(noise)
  m0 <- as.integer(m * pi0)
  m1 <- m - m0
  if (is.null(mu)) mu <- rbitri(m1, ...)
  stopifnot(length(mu) == m1)
  X0 <- matrix(rnorm(m0 * n), ncol = n)
  Y0 <- matrix(rnorm(m0 * n), ncol = n)
  X1 <- matrix(0, m1, n)
  Y1 <- matrix(0, m1, n)
  for (k in seq_len(m1)) {
    X1[k, ] <- mu[k] / 2 + rnorm(n)
    Y1[k, ] <- -mu[k] / 2 + rnorm(n)
  }
  X <- rbind(X0, X1)
  Y <- rbind(Y0, Y1)
  if (!is.null(noise_sd) && noise_sd > 0) {
    k <- if (noise == "feature") m else m * n
    X <- log(exp(rnorm(k, 0, noise_sd)) + exp(X))
    Y <- log(exp(rnorm(k, 0, noise_sd)) + exp(Y))
  }
  list(x = cbind(X, Y), group = factor(rep(c("X", "Y"), each = n)),
       null = rep(c(TRUE, FALSE), c(m0, m1)), mu = c(numeric(m0), mu))
}

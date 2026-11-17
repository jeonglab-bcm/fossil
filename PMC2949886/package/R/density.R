#' P-value density of the t test after filtering
#'
#' The density of the two-sided p-value of Student's two-sample t test
#' (\eqn{\nu = 2n - 2} degrees of freedom, unit variance) after removing a
#' fraction of the features with a fold-change or variance filter, by
#' numerical integration over the pooled variance (Additional File 1,
#' equations 17 to 21).
#'
#' The variance filter can be the pooled within-group variance \eqn{S_p^2}
#' (\code{"variance"}, the reading that reproduces the published Fig. 1) or the
#' variance of all samples \eqn{S_Z^2} (\code{"total_variance"}, the text's
#' \eqn{W_V}); under the null, \eqn{S_Z^2} is independent of T and leaves the
#' p-values uniform.
#'
#' @param u p-values at which to evaluate the density (in (0, 1)).
#' @param nu degrees of freedom (n per group is \code{nu/2 + 1}).
#' @param delta noncentrality of the t statistic under the alternative
#'   (0 for the null): the group difference is
#'   \code{delta * sqrt(2 / n)}.
#' @param filter \code{"none"}, \code{"foldchange"}, \code{"variance"} or
#'   \code{"total_variance"}.
#' @param removed fraction of the features removed.
#' @param threshold \code{"null"}: the threshold removes the fraction
#'   \code{removed} of the null features and is used under both hypotheses;
#'   \code{"own"}: it removes that fraction under the hypothesis evaluated.
#' @return The density at \code{u}.
pvalue_density_filtered <- function(u, nu = 8, delta = 0,
                                    filter = c("none", "foldchange", "variance"),
                                    removed = 0.25, threshold = c("null", "own")) {
  filter <- match.arg(filter, c("none", "foldchange", "variance", "total_variance"))
  threshold <- match.arg(threshold)
  n <- nu / 2 + 1
  sd_d <- sqrt(2 / n)
  mean_d <- delta * sd_d
  th_d <- if (threshold == "null") 0 else mean_d    # group difference used to set the threshold
  # lower limit on the pooled variance v for a feature with |T| = t to be kept
  vmin <- switch(filter,
    none = function(t) 0,
    foldchange = {
      # P(|D| < w) = removed, D ~ N(mean_d, 2/n)
      f <- function(w) pnorm(w, th_d, sd_d) - pnorm(-w, th_d, sd_d) - removed
      w <- uniroot(f, c(0, 20), tol = 1e-12)$root
      function(t) n * w^2 / (2 * t^2)
    },
    variance = {
      # nu Sp^2 ~ chi-square(nu) under both hypotheses
      w <- stats::qchisq(removed, nu) / nu
      function(t) w
    },
    total_variance = {
      # (2n - 1) S_Z^2 = nu v + (n/2) D^2 ~ chi-square(2n - 1, ncp = (n/2) th_d^2)
      w <- stats::qchisq(removed, 2 * n - 1, ncp = n / 2 * th_d^2)
      function(t) w / (nu + t^2)
    })
  ft <- function(t) {                          # density of T (kept part, unnormalized)
    g <- function(v) {
      s <- sqrt(2 * v / n)
      nu * dchisq(nu * v, nu) * s * (dnorm(t * s, mean_d, sd_d))
    }
    lo <- vmin(abs(t))
    if (!is.finite(lo)) return(0)
    integrate(g, lo, Inf, rel.tol = 1e-10, abs.tol = 0, subdivisions = 1000L)$value
  }
  dens <- vapply(u, function(ui) {
    t <- qt(1 - ui / 2, nu)
    (ft(t) + ft(-t)) / (2 * stats::dt(t, nu))
  }, numeric(1))
  # normalise by the probability of being kept under the hypothesis evaluated
  keep <- integrate(function(uu) vapply(uu, function(ui) {
    t <- qt(1 - ui / 2, nu); (ft(t) + ft(-t)) / (2 * stats::dt(t, nu))
  }, numeric(1)), 0, 1, rel.tol = 1e-8, subdivisions = 2000L)$value
  dens / keep
}

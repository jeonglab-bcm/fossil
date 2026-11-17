# Fig. 1: p-value densities of the t test with 8 degrees of freedom under the
# null (delta = 0) and the alternative (delta = 1), with no filter and with
# 25% of the features removed by the fold-change or the variance filter.
#
# Usage: Rscript fig1.R <out.json>
suppressMessages({library(filterfdr); library(jsonlite)})
out <- commandArgs(TRUE)[1]
u <- seq(0.001, 0.999, length.out = 999)
res <- list(u = u)
for (h in c(null = 0, alternative = 1)) {
  nm <- if (h == 0) "null" else "alternative"
  res[[nm]] <- lapply(c(none = "none", foldchange = "foldchange", variance = "variance"),
                      function(f) pvalue_density_filtered(u, nu = 8, delta = h, filter = f, removed = 0.25))
}
# near miss: the group difference read as delta itself (noncentrality delta * sqrt(n/2))
# near misses: the threshold set under each hypothesis; the variance filter on S_Z^2
res$alternative_own <- lapply(c(none = "none", foldchange = "foldchange", variance = "variance"),
                              function(f) pvalue_density_filtered(u, nu = 8, delta = 1, filter = f, removed = 0.25,
                                                                  threshold = "own"))
res$total_variance <- list(null = pvalue_density_filtered(u, 8, 0, "total_variance"),
                           alternative = pvalue_density_filtered(u, 8, 1, "total_variance"))
res$alternative_mean1 <- lapply(c(none = "none", foldchange = "foldchange", variance = "variance"),
                                function(f) pvalue_density_filtered(u, nu = 8, delta = sqrt(5 / 2), filter = f,
                                                                    removed = 0.25))
writeLines(toJSON(res, digits = NA, auto_unbox = TRUE), out)

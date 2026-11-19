# Write the example data of logitbias (run from the package folder):
#   Rscript scripts/make_example_data.R
# inst/extdata/means_example.csv: synthetic per-size mean coefficients, one row per sample size
# (100 to 1500 by 5) and coefficient, drawn as mean = beta + b1/n + Normal(0, sigma) with the
# values of Table 1 of Nemes et al. (2009) as beta and b1.
# inst/extdata/means_example_expected.csv: those generating values, with a tolerance of four
# standard errors of the OLS fit (closed form, from sigma and the sizes; not from the package).
set.seed(20090727)
sizes <- seq(100, 1500, 5)
truth <- data.frame(term = c("x", "x", "z", "z"), param = c("intercept", "inv_n", "intercept", "inv_n"),
                    value = c(2.011, 23.9, -0.898, -9.524))
sigma <- c(x = 0.006, z = 0.006)
rows <- lapply(c("x", "z"), function(tm) {
  b <- truth$value[truth$term == tm]
  data.frame(n = sizes, term = tm, mean = round(b[1] + b[2] / sizes + rnorm(length(sizes), 0, sigma[[tm]]), 6))
})
write.csv(do.call(rbind, rows), "inst/extdata/means_example.csv", row.names = FALSE)
u <- 1 / sizes
sxx <- sum((u - mean(u))^2)
se <- function(tm) sigma[[tm]] * c(sqrt(1 / length(u) + mean(u)^2 / sxx), sqrt(1 / sxx))
truth$tolerance <- signif(4 * c(se("x"), se("z")), 3)
write.csv(truth, "inst/extdata/means_example_expected.csv", row.names = FALSE)
print(truth)

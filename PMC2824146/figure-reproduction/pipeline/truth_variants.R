# Hypothesis tests for the true values and empirical SEs (Figs 2 and 3 reference lines): the
# complete-data Cox fit over 2000 cohorts under variants of the data generation.
#   Rscript truth_variants.R truth_variants.json [REPS]
suppressMessages(library(misscox))
a <- commandArgs(TRUE)
reps <- if (length(a) >= 2) as.integer(a[2]) else 2000L
cv <- gbsg_covariates()
gb <- coef(fit_full_cox(cv)); names(gb) <- names(paper_coefficients())
variants <- list(
  text = generation_parameters(cv),
  unrounded_coefficients = generation_parameters(cv, coefficients = gb),
  binaries_keep_correlation = generation_parameters(cv, binaries = "preserve"),
  binaries_keep_correlation_unrounded = generation_parameters(cv, coefficients = gb, binaries = "preserve"),
  no_floor_at_zero = generation_parameters(cv, lower_zero = FALSE))
res <- lapply(names(variants), function(v) {
  b <- true_value_fits(reps, variants[[v]])
  x <- simulate_cohort(20000, variants[[v]], seed = 4242L)
  list(variant = v, reps = reps, mean = as.list(colMeans(b)), empirical_se = as.list(apply(b, 2, sd)),
       cor_X1_X6 = cor(x$X1, x$X6), cor_X3_X4 = cor(x$X3, x$X4), censored = mean(x$status == 0))
})
writeLines(jsonlite::toJSON(list(gbsg_coefficients = as.list(gb), variants = res), auto_unbox = TRUE,
                            digits = 10, pretty = TRUE), a[1])

printed_ok <- function(observed, printed) {
  d <- nchar(sub("^[^.]*\\.?", "", printed))
  abs(observed - as.numeric(printed)) <= 0.5 * 10^(-d) + 1e-12
}

test_that("Table 3 comes back at printed precision", {
  exp <- utils::read.csv(example_path("table3_expected.csv"), colClasses = "character")
  got <- table3_odds_ratios()
  for (k in c("pct5", "pct10", "pct25", "pct50", "pct75"))
    expect_true(all(printed_ok(got[[k]], exp[[k]])), info = k)
})

test_that("the full Cox model on GBSG2 gives the printed linear predictor", {
  skip_if_not_installed("TH.data")
  exp <- utils::read.csv(example_path("lp_expected.csv"), colClasses = "character")
  b <- stats::coef(fit_full_cox(gbsg_covariates()))
  expect_true(all(printed_ok(unname(b), exp$printed)))
})

test_that("skewness b1 gives the text's values", {
  skip_if_not_installed("TH.data")
  cv <- gbsg_covariates()
  expect_true(all(printed_ok(vapply(cv[c("X2", "X3", "X4", "X8")], skewness, 0),
                             c("2.87", "4.77", "3.07", "1.77"))))
})

test_that("the design hits its shares under MCAR", {
  skip_if_not_installed("TH.data")
  pr <- generation_parameters(gbsg_covariates())
  x <- simulate_cohort(20000, pr, seed = 1L)
  xm <- impose_missing(x, "MCAR", 0.5, seed = 2L)
  ind <- attr(xm, "indicators")
  inc <- mean(rowSums(ind) > 0)
  expect_equal(inc, 0.5, tolerance = 0.03)
  expect_equal(mean(ind[, "X3"]) / inc, 0.70, tolerance = 0.05)
  expect_equal(mean(ind[, "X2"] & ind[, "X3"]) / inc, 0.35, tolerance = 0.05)
})

test_that("Rubin's rules", {
  r <- rubin_pool(c(1, 2, 3), c(1, 1, 1))
  expect_equal(r$est, 2)
  expect_equal(r$var, 1 + 4 / 3)
})

test_that("methods run on the example cohort", {
  x <- utils::read.csv(example_path("example_cohort_mar25.csv"))
  cc <- handle_missing(x, "CC")
  expect_equal(nrow(cc), 1L)
  expect_lt(cc$n_analysed, nrow(x))
  pm <- handle_missing(x, "MICE_PMM_notrans", m = 2, seed = 1)
  expect_equal(pm$n_analysed, nrow(x))
  expect_true(all(is.finite(unlist(pm))))
})

test_that("bad input fails clearly", {
  x <- utils::read.csv(example_path("example_cohort_mar25.csv"))
  expect_error(handle_missing(x, "LOCF"), "unknown method")
  expect_error(impose_missing(x, "MAYBE", 0.25), "mechanism must be")
  expect_error(example_path("nothing.csv"), "no example file")
})

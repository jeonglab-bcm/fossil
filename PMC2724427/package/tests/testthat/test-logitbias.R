test_that("the example means give back the values they were drawn from", {
  m <- read.csv(example_path("means_example.csv"))
  e <- read.csv(example_path("means_example_expected.csv"))
  f <- fit_bias_curve(m)
  got <- merge(f, e, by = c("term", "param"))
  expect_equal(nrow(got), 4)
  expect_true(all(abs(got$estimate - got$value) <= got$tolerance))
})

test_that("simulate_population runs the R lines of Additional file 1", {
  set.seed(42)
  x <- rnorm(5000, 2, 0.7)
  z <- ifelse(x>2.5, rbinom(5000, 1, 0.6), rbinom(5000, 1, 0.4))
  theta <- 0.1 + 2*x - 0.9*z
  y <- ifelse(runif(5000) < plogis(theta), 1, 0)
  expect_identical(simulate_population(5000, seed = 42), data.frame(y = y, x = x, z = z))
})

test_that("fit_bias_curve agrees with lm on the means and on every estimate", {
  pop <- simulate_population(20000, seed = 3)
  sim <- bias_simulation(pop, sizes = c(200, 300, 500, 800), reps = 30, seed = 3, keep = TRUE)
  ok <- sim$samples[sim$samples$status == "ok", ]
  for (tm in c("x", "z")) {
    d <- sim$summary[sim$summary$term == tm, ]
    l1 <- summary(lm(mean ~ I(1 / n), data = d))
    f1 <- fit_bias_curve(sim$summary, "means")
    f1 <- f1[f1$term == tm, ]
    expect_equal(f1$estimate, unname(l1$coefficients[, 1]), tolerance = 1e-10)
    expect_equal(f1$se, unname(l1$coefficients[, 2]), tolerance = 1e-8)
    expect_lt(abs(f1$r2[1] - l1$r.squared), 1e-12)
    l2 <- summary(lm(ok[[tm]] ~ I(1 / ok$n)))
    f2 <- fit_bias_curve(sim$summary, "all")
    f2 <- f2[f2$term == tm, ]
    expect_equal(f2$estimate, unname(l2$coefficients[, 1]), tolerance = 1e-10)
    expect_equal(f2$se, unname(l2$coefficients[, 2]), tolerance = 1e-8)
    expect_lt(abs(f2$r2[1] - l2$r.squared), 1e-12)
  }
})

test_that("bias_simulation does not depend on the number of cores", {
  skip_on_os("windows")
  pop <- simulate_population(10000, seed = 5)
  a <- bias_simulation(pop, sizes = c(150, 400), reps = 20, seed = 9, cores = 1)
  b <- bias_simulation(pop, sizes = c(150, 400), reps = 20, seed = 9, cores = 2)
  expect_identical(a$summary, b$summary)
})

test_that("analytic_bias gives the closed form for an intercept-only model", {
  # logit of a sample proportion: first-order bias (2p - 1) / (2 p (1 - p)) / n
  pop <- data.frame(y = rep(c(1, 0), c(800, 200)))
  p <- 0.8
  expect_equal(unname(analytic_bias(pop)), (2 * p - 1) / (2 * p * (1 - p)), tolerance = 1e-10)
})

test_that("separated samples are flagged and bad input is refused", {
  X <- cbind(1, c(1, 2, 3, 4, 5, 6))
  expect_false(fit_logistic(X, c(0, 0, 0, 1, 1, 1))$status == "ok")
  expect_equal(fit_logistic(X, c(0, 1, 0, 1, 0, 1))$status, "ok")
  expect_error(fit_logistic(X, c(0, 1, 2, 1, 0, 1)), "0 or 1")
  expect_error(bias_simulation(data.frame(x = 1:10), sizes = 5), "column y")
  expect_error(fit_bias_curve(data.frame(n = 1:3)), "lacks")
  expect_equal(bias_correct(2.2, 20, 100), 2)
})

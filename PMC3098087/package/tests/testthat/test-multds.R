read_example <- function(name) utils::read.csv(example_path(name))

test_that("variable selection matches stats::t.test on the example", {
  tr <- read_example("train.csv")
  x <- center_data(as.matrix(tr[, -1]), "samples")
  sel <- select_variables(x, tr$class, 40)
  expected <- read_example("expected_selected.csv")
  expect_setequal(colnames(x)[sel], expected$variable)
  expect_equal(unname(t_statistics(x, tr$class)[sel]), expected$t, tolerance = 1e-5)
})

test_that("DLDA and DQDA give the predictions of sma::stat.diag.da", {
  tr <- read_example("train.csv")
  te <- read_example("test.csv")
  x <- center_data(as.matrix(tr[, -1]), "samples")
  xt <- center_data(as.matrix(te[, -1]), "samples")
  sel <- select_variables(x, tr$class, 40)
  expected <- read_example("expected_predictions.csv")
  expect_equal(dlda(x[, sel], tr$class, xt[, sel])$pred, expected$DLDA)
  expect_equal(dqda(x[, sel], tr$class, xt[, sel])$pred, expected$DQDA)
})

test_that("the metrics follow Eq. 5 and 6", {
  truth <- c(1, 1, 1, 1, 2, 2, 2, 2)
  pred <- c(1, 1, 1, 2, 2, 2, 1, 1)
  ev <- evaluate(truth, pred, score = c(4, 3, 2, 1, 0, -1, 2.5, 5), kappa1 = 0.2)
  expect_equal(unname(ev["PA1"]), 0.75)
  expect_equal(unname(ev["PA2"]), 0.5)
  expect_equal(unname(ev["PA"]), 0.75 * 0.5 + 0.5 * 0.5)
  expect_equal(unname(ev["PV1"]), 0.2 * 0.75 / (0.2 * 0.75 + 0.8 * 0.5))
  expect_equal(unname(ev["AUC"]), 10 / 16)
  expect_true(is.na(predictive_values(0, 1, 0.1)[["PV1"]]))
})

test_that("corrections balance the training set", {
  y <- c(rep(1L, 4), rep(2L, 16))
  set.seed(1)
  expect_equal(as.vector(table(y[downsize(y)])), c(4, 4))
  expect_equal(as.vector(table(y[oversample(y)])), c(16, 16))
  expect_equal(downsize(c(1L, 1L, 2L, 2L)), 1:4)
})

test_that("MultDS gives every test sample a class and a vote share", {
  tr <- read_example("train.csv")
  te <- read_example("test.csv")
  x <- center_data(as.matrix(tr[, -1]), "samples")
  xt <- center_data(as.matrix(te[, -1]), "samples")
  set.seed(2)
  fp <- multds_predict(c("DLDA", "1-NN"), x, tr$class, xt, G = 40, B = 11)
  expect_named(fp, c("DLDA", "1-NN"))
  expect_true(all(fp$DLDA$pred %in% 1:2))
  expect_true(all(fp$DLDA$score >= 0 & fp$DLDA$score <= 1))
})

test_that("every classifier runs and replicates are reproducible", {
  s <- simulation_settings("test", p = 60, k1train = 0.25, p_de = 10, mu2 = 1, G = 20,
                           methods = classifier_names(thr = TRUE))
  a <- run_replicate(s, 3)
  b <- run_replicate(s, 3)
  expect_equal(a, b)
  expect_equal(sort(unique(a$method)), sort(classifier_names(thr = TRUE)))
})

test_that("invalid input stops with a clear error", {
  expect_error(t_statistics(matrix(rnorm(10), 5), c(1, 2, 2, 2, 2)), "at least two samples")
  expect_error(fit_predict("DLDA", matrix(rnorm(10), 5), rep(1, 5), matrix(rnorm(4), 2)), "both classes")
  expect_error(fit_predict("LDA", matrix(rnorm(10), 5), c(1, 1, 2, 2, 2), matrix(rnorm(4), 2)), "unknown classifier")
})

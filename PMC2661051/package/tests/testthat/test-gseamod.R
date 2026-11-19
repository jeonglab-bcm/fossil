example_data <- function() {
  x <- read.csv(example_path("sim_expression.csv"), row.names = 1, check.names = FALSE)
  y <- read.csv(example_path("sim_labels.csv"))$class
  list(X = as.matrix(x), y = y, sets = read_gmt(example_path("sim_sets.gmt")))
}

test_that("moderated t equals limma's eBayes", {
  d <- example_data()
  fit <- limma::eBayes(limma::lmFit(d$X, cbind(1, d$y)))
  expect_equal(as.numeric(gene_stats(d$X, d$y, "modt")), as.numeric(fit$t[, 2]), tolerance = 1e-10)
  expect_equal(as.numeric(gene_stats(d$X, d$y, "corr")), as.numeric(cor(t(d$X), d$y)[, 1]), tolerance = 1e-12)
})

test_that("the enrichment score matches a direct running sum", {
  d <- example_data()
  s <- gene_stats(d$X, d$y, "modt")^2
  idx <- match(d$sets$set1, rownames(d$X))
  o <- order(s, decreasing = TRUE)
  hit <- o %in% idx
  run <- cumsum(abs(s[o]) * hit) / sum(abs(s[idx])) - cumsum(!hit) / (length(s) - length(idx))
  expect_equal(unname(set_stats(s, list(idx), "es")[1, 1]), unname(run[which.max(abs(run))]))
})

test_that("the logistic slope equals glm and ranks like the mean", {
  d <- example_data()
  s <- gene_stats(d$X, d$y, "modt")^2
  idx <- match(d$sets$set4, rownames(d$X))
  mem <- as.numeric(seq_along(s) %in% idx)
  g <- unname(coef(glm(mem ~ s, family = binomial))[2])
  expect_equal(unname(set_stats(s, list(idx), "condslope")[1, 1]), g, tolerance = 1e-6)
  a <- gsea(d$X, d$y, d$sets, setstat = "condslope", method = "resampling", B = 200, seed = 1)$p
  b <- gsea(d$X, d$y, d$sets, setstat = "mean", method = "resampling", B = 200, seed = 1)$p
  expect_equal(a, b)
})

test_that("the example data set finds the pure differentially expressed sets", {
  d <- example_data()
  r <- gsea(d$X, d$y, d$sets, gene = "modt", transform = "square", setstat = "mean",
            method = "permutation", B = 200, seed = 1)
  expect_true(all(r$p[r$set %in% c("set2", "set7")] <= 0.05))
  expect_gt(r$p[r$set == "set3"], 0.05)
})

test_that("detection rates over 100 simulated data sets agree with Table 4 of the paper", {
  expected <- read.csv(example_path("paper_table4_resampling.csv"), colClasses = "character")
  p <- t(vapply(1:100, function(r) {
    d <- simulate_ackermann(seed = 2009 + r)
    gsea(d$X, d$y, d$sets, gene = "modt", transform = "square", setstat = "mean",
         method = "resampling", B = 1000, seed = r)$p
  }, numeric(9)))
  colnames(p) <- paste0("set", 1:9)
  ours <- detection_rates(p)
  tol <- rate_tolerance(expected$detection_rate, ours[expected$set])
  expect_true(all(abs(as.numeric(expected$detection_rate) - ours[expected$set]) <= tol))
})

test_that("bad input gives a clear error", {
  expect_error(gene_stats(matrix(1:6, 2), c(0, 1, 1)), "at least two samples")
  expect_error(gsea(matrix(rnorm(20), 2), rep(0:1, 5), list(a = "nope")), "no genes")
})

test_that("the globaltest statistic equals globaltest::gt up to one constant", {
  skip_if_not_installed("globaltest")
  d <- example_data()
  idx <- lapply(d$sets, match, rownames(d$X))
  g <- vapply(idx, function(i) {
    A <- t(d$X[i, ])
    globaltest::result(globaltest::gt(factor(d$y), A))[, "Statistic"]
  }, numeric(1))
  ratio <- g / global_stats(d$X, d$y, idx)[, 1]
  expect_equal(unname(ratio), rep(unname(ratio[1]), length(ratio)), tolerance = 1e-8)
})

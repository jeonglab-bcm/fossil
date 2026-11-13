ex <- read_genotypes(example_path())
expected <- read.csv(example_path("example_expected.csv"), stringsAsFactors = FALSE)
disease <- match(strsplit(expected$snps[expected$test == "disease_snps"], ";")[[1]], colnames(ex$geno))

test_that("the example input is as described", {
  expect_equal(dim(ex$geno), c(600L, 60L))
  expect_equal(sum(ex$status == 1), 300L)
  expect_equal(colnames(ex$geno)[disease], c("snp17", "snp44"))
})

test_that("the B statistic matches the expected output", {
  rows <- expected[expected$test == "B", ]
  for (i in seq_len(nrow(rows))) {
    cols <- match(strsplit(rows$snps[i], ";")[[1]], colnames(ex$geno))
    b <- b_test(ex$geno, ex$status, matrix(cols, nrow = 1))
    expect_equal(b$B, rows$statistic[i], tolerance = 1e-8)
    expect_equal(b$df, rows$df[i])
    expect_equal(b$shift, as.numeric(rows$shift[i]), tolerance = 1e-8)
    expect_equal(b$p, rows$p[i], tolerance = 1e-8)
  }
})

test_that("the chi-squared test matches the expected output", {
  rows <- expected[expected$test == "chisq", ]
  cs <- chisq_single(ex$geno, ex$status)
  cols <- match(rows$snps, colnames(ex$geno))
  expect_equal(cs$statistic[cols], rows$statistic, tolerance = 1e-8)
  expect_equal(cs$p[cols], rows$p, tolerance = 1e-8)
})

test_that("epiForest identifies both disease SNPs of the example", {
  fit <- epiforest(ex$geno, ex$status, seed = 1)
  expect_true(all(disease %in% fit$identified))
  expect_true(all(disease %in% fit$candidates))
  expect_equal(fit$swsfs$forests, fit$swsfs$k + 20)
})

test_that("the conditional B statistic has 3^k - 3^t degrees of freedom", {
  b <- b_test(ex$geno, ex$status, matrix(disease, nrow = 1), given = 1L)
  b1 <- b_test(ex$geno, ex$status, matrix(disease[2], nrow = 1))
  expect_equal(b$df, 6)
  expect_true(b$B < b_test(ex$geno, ex$status, matrix(disease, nrow = 1))$B)
  expect_true(is.finite(b$p) && is.finite(b1$p))
})

test_that("the disease models reach the requested prevalence and marginal effect", {
  for (m in 1:3) for (q in c(0.05, 0.1, 0.2, 0.5)) {
    d <- disease_model(m, c(0.3, 0.5, 1.0)[m], q, 0.1)
    expect_equal(d$prevalence, 0.1, tolerance = 1e-8)
    expect_equal(d$lambda, c(0.3, 0.5, 1.0)[m], tolerance = 1e-6)
    expect_true(all(d$penetrance <= 1))
  }
  expect_error(disease_model(2, 0.5, 0.05, 0.1, scale = "risk", table = "marchini"))
})

test_that("ld_transition gives the requested r^2", {
  for (q in c(0.05, 0.2, 0.5)) {
    t <- ld_transition(q, 0.7)
    D <- q * t[["q_minor"]] - q * q          # P(minor, minor) - p^2
    expect_equal(D^2 / (q * (1 - q))^2, 0.7, tolerance = 1e-12)
  }
})

test_that("bad input gives a clear error", {
  expect_error(b_test(ex$geno + 1L, ex$status, matrix(1)), "0, 1 or 2")
  expect_error(epiforest(ex$geno, rep(1L, nrow(ex$geno))), "both cases and controls")
  g <- ex$geno
  g[1, 1] <- NA
  expect_error(chisq_single(g, ex$status), "missing")
})

test_that("the example gives the expected achieved FDR and power (base R reference)", {
  d <- read_two_group(example_path("example_data.csv"))
  expect_equal(dim(d$x), c(1000L, 20L))
  ref <- read.csv(example_path("expected_fdr_power.csv"))
  got <- filter_curve(d, fractions = c(0, 0.25, 0.5, 0.75), methods = "BH")
  m <- merge(ref, got, by = c("filter", "fraction"), suffixes = c(".ref", ".got"))
  expect_equal(nrow(m), nrow(ref))
  expect_equal(m$rejected.got, m$rejected.ref)
  expect_equal(m$fdr.got, m$fdr.ref, tolerance = 1e-12)
  expect_equal(m$power.got, m$power.ref, tolerance = 1e-12)
})

test_that("the p-value densities match the published Fig. 1", {
  pub <- read.csv(example_path("fig1_published.csv"))
  for (i in seq_len(nrow(pub))) {
    got <- pvalue_density_filtered(pub$p[i], nu = 8, delta = if (pub$hypothesis[i] == "null") 0 else 1,
                                   filter = pub$filter[i], removed = 0.25)
    expect_lt(abs(got - pub$density[i]), 0.01)
  }
})

test_that("the t test and the Wilcoxon test agree with stats", {
  set.seed(1)
  x <- matrix(rnorm(40), 2)
  g <- factor(rep(c("a", "b"), each = 10))
  r <- row_ttest(x, g)
  expect_equal(r$p.value[1], t.test(x[1, 1:10], x[1, 11:20], var.equal = TRUE)$p.value)
  w <- row_ttest(x, g, "wilcoxon")
  expect_equal(w$p.value[2], wilcox.test(x[2, 1:10], x[2, 11:20])$p.value)
})

test_that("the bitriangular distribution is a distribution", {
  expect_equal(integrate(dbitri, -3, 3)$value, 1, tolerance = 1e-6)
  p <- c(0.01, 0.2, 0.49, 0.51, 0.9, 0.999)
  expect_equal(pbitri(qbitri(p)), p, tolerance = 1e-12)
  expect_true(all(abs(rbitri(100)) >= log2(1.2)))
})

test_that("the FDR-bias test flags the fold-change filter and not the signal filter", {
  d <- read_two_group(example_path("example_data.csv"))
  set.seed(3)
  fc <- fdr_bias_test(d$x, d$group, "foldchange", fractions = c(0, 0.5), nperm = 60)
  expect_lt(fc$p.value[2], 0.001)
  sg <- fdr_bias_test(d$x, d$group, "signal", fractions = 0.5, nperm = 60)
  expect_gt(sg$p.value[1], 0.001)
})

test_that("bad input gives a clear error", {
  f <- tempfile(fileext = ".csv")
  write.csv(data.frame(feature = "a", A1 = 1, B1 = 2, C1 = 3), f, row.names = FALSE)
  expect_error(read_two_group(f), "exactly two groups")
  expect_error(example_path("nope.csv"), "no bundled file")
})

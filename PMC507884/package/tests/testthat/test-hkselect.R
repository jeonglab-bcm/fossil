breast <- read_expression(example_path("szabo2004_breast.csv"))
expected <- utils::read.csv(example_path("szabo2004_expected.csv"), stringsAsFactors = FALSE)
same_set <- function(a, b) setequal(strsplit(a, "[,;]")[[1]], strsplit(b, "[,;]")[[1]])

test_that("Model 1a gives Table 1 of Szabo et al. (2004) at the printed precision", {
  sd <- gene_sd(fit_model1(breast$expr))
  t1 <- expected[expected$table == "table1", ]
  expect_true(all(abs(sd[t1$key] - t1$value) <= 0.0005 + 1e-12))
})

test_that("best sets give every Table 2 gene set, and values within one unit in the last digit", {
  b <- best_sets(gene_sd(fit_model1(breast$expr)))
  t2 <- expected[expected$table == "table2", ]
  expect_true(all(mapply(same_set, b$genes, t2$genes)))
  expect_true(all(abs(b$sd - t2$value) <= 0.0001 + 1e-12))
})

test_that("the printed set-variance formula (divide by |S|) does not give Table 2", {
  b <- best_sets(gene_sd(fit_model1(breast$expr)), divisor = "size")
  expect_gt(b$sd[2], 0.2)   # Table 2 prints 0.1718 for the best pair
})

test_that("Wald intervals bracket the estimates and come within 0.0025 of Table 1's", {
  ci <- gene_sd_ci(breast$expr)
  expect_true(all(ci$lower < ci$sd & ci$sd < ci$upper))
  t1 <- data.frame(gene = c("MRPL19", "PUM1", "PSMC4", "SF3A1", "ACTB", "GAPD"),
                   lower = c(0.168, 0.215, 0.235, 0.327, 0.376, 0.439),
                   upper = c(0.284, 0.328, 0.352, 0.472, 0.533, 0.613))
  ci <- ci[match(t1$gene, ci$gene), ]
  expect_lte(max(abs(c(ci$lower - t1$lower, ci$upper - t1$upper))), 0.0025)
})

test_that("geNorm leaves MRPL19 and PSMC4 as the best pair and drops GAPD first", {
  g <- genorm(breast$expr)
  expect_setequal(g$gene[g$rank == 1.5], c("MRPL19", "PSMC4"))
  expect_equal(g$gene[g$rank == 6], "GAPD")
  m <- m_values(breast$expr[, c("MRPL19", "PSMC4")])
  expect_equal(unname(m[1]), sd(log(breast$expr[, "MRPL19"] / breast$expr[, "PSMC4"])))
})

test_that("the variance-group test gives p = 0.0014", {
  p <- variance_group_test(breast$expr, c("a", "a", "a", "a", "c", "c"))$p.value
  expect_equal(round(p, 4), 0.0014)
})

synth <- read_expression(example_path("synthetic_tissues.csv"))
truth <- utils::read.csv(example_path("synthetic_truth.csv"), stringsAsFactors = FALSE)

test_that("Model 2 recovers the parameters the synthetic data were drawn from", {
  comp <- model2_components(fit_model2(synth$expr, synth$tissue))
  s <- truth[truth$parameter == "sigma", ]; v <- truth[truth$parameter == "varsigma", ]
  b <- truth[truth$parameter == "bias", ]; kg <- do.call(rbind, strsplit(b$key, ":"))
  expect_true(all(abs(comp$sigma[s$key] / s$value - 1) <= 0.15))
  expect_true(all(abs(comp$varsigma[v$key] / v$value - 1) <= 0.15))
  expect_true(all(abs(comp$bias[kg] - b$value) <= 0.25))
  expect_equal(unname(colSums(comp$bias)), rep(0, 5), tolerance = 1e-10)
  expect_equal(unname(rowSums(comp$bias)), rep(0, 3), tolerance = 1e-10)
})

test_that("set MSE: one gene is its own MSE, and the full set has no bias", {
  comp <- list(sigma = c(a = 0.2, b = 0.3), varsigma = c(X = 1, Y = 2),
               bias = matrix(c(0.5, -0.5, -0.5, 0.5), 2, dimnames = list(c("X", "Y"), c("a", "b"))))
  m <- gene_mse(comp)
  expect_equal(as.numeric(set_mse(comp, "a")), max(m$mse[m$gene == "a"]))
  expect_equal(as.numeric(set_mse(comp, c("a", "b"))), 4 * (0.04 + 0.09) / 4)
  expect_equal(as.numeric(set_mse(comp, c("a", "b"), bias = "mean")), 4 * (0.04 + 0.09) / 4)
  ms <- minimax_sets(comp)
  expect_equal(ms$genes[2], "a,b")
})

test_that("bad input gives a clear error", {
  expect_error(fit_model1(matrix(c(1, -1, 2, 3, 4, 5), 3)), "positive")
  expect_error(fit_model1(matrix(1:6 + 0.5, 3, dimnames = list(NULL, c("a", "a")))), "unique")
  expect_error(fit_model2(synth$expr, rep("A", nrow(synth$expr))), "two tissue types")
  expect_error(set_sd(c(a = 1), "b"), "unknown genes")
})

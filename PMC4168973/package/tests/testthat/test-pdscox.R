clinical <- function() {
  m <- read.csv(example_path("miller_clinical.csv"))
  m$time[is.na(m$time)] <- 0
  m$p53[is.na(m$p53)] <- 0
  m
}
expected <- function() read.csv(example_path("paper_values.csv"), colClasses = c("character", "character", "character"))
printed_ok <- function(observed, printed) {
  s <- tolower(printed)
  dec <- if (grepl("e", s)) {
    parts <- strsplit(s, "e")[[1]]
    nchar(sub("^[^.]*\\.?", "", parts[1])) - as.integer(parts[2])
  } else nchar(sub("^[^.]*\\.?", "", s))
  abs(observed - as.numeric(printed)) <= 0.5 * 10^(-dec) + 1e-15
}

test_that("Fig. 1 log-rank p-values come back as printed", {
  m <- clinical(); e <- expected(); e <- e[e$item == "fig1_logrank", ]
  obs <- c(LN = logrank_p(m$time, m$event, m$node), grade = logrank_p(m$time, m$event, m$grade),
           p53 = logrank_p(m$time, m$event, m$p53), ER = logrank_p(m$time, m$event, m$er),
           PG = logrank_p(m$time, m$event, m$pgr))
  for (i in seq_len(nrow(e))) expect_true(printed_ok(obs[[e$feature[i]]], e$value[i]), info = e$feature[i])
})

test_that("Table 2 univariate Cox p-values come back as printed", {
  m <- clinical(); e <- expected(); e <- e[e$item == "table2_univariate", ]
  u <- univariate_cox(cbind(LN = m$node, size = m$size_mm, grade = m$grade, p53 = m$p53), m$time, m$event)
  for (i in seq_len(nrow(e))) expect_true(printed_ok(u$p[u$feature == e$feature[i]], e$value[i]), info = e$feature[i])
})

test_that("deregulation scores follow the synthetic activities and the model ranks the sets", {
  x <- as.matrix(read.csv(example_path("synthetic_expression.csv"), row.names = 1, check.names = FALSE))
  sv <- read.csv(example_path("synthetic_survival.csv"))
  truth <- read.csv(example_path("synthetic_truth.csv"))
  eff <- read.csv(example_path("synthetic_effects.csv"))
  gs <- read_gmt(example_path("synthetic_sets.gmt"))
  pds <- suppressMessages(capture.output(s <- pathway_scores(x, gs, attempts = 20)))
  for (k in names(gs)) expect_gt(cor(s[k, ], truth[[k]]), 0.9)
  m <- cox_lasso(t(s), sv$time, sv$event, runs = 10)
  b <- m$coefficients[eff$set]; b[is.na(b)] <- 0
  expect_identical(order(-b), order(-eff$log_hazard_ratio))
})

test_that("cross-validation runs can be recomputed one at a time", {
  x <- as.matrix(read.csv(example_path("synthetic_expression.csv"), row.names = 1, check.names = FALSE))[1:36, ]
  sv <- read.csv(example_path("synthetic_survival.csv"))
  all <- cv_lambdas(t(x), sv$time, sv$event, runs = 3, seed = 7)
  expect_equal(cv_lambdas(t(x), sv$time, sv$event, runs = 3, seed = 7, which = 2), all[2])
})

test_that("bad input gives clear errors", {
  expect_error(example_path("no_such_file.csv"), "no example file")
  expect_true(is.na(logrank_p(c(1, 2, 3), c(1, 0, 1), factor(c("a", "a", "a")))))
  r <- roc_auc(c(0.1, 0.4, 0.35, 0.8), c(0, 0, 1, 1))
  expect_equal(r$auc, 0.75)
})

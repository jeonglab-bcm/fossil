# Check multds against the code the paper used, on the free R runtime.
#   Rscript port_check.R SMA_TARBALL OUT.json
# - DLDA and DQDA: multds::dlda/dqda against sma::stat.diag.da (pool = 1 / 0) from the archived
#   sma 0.5.15 sources (sma no longer installs on current R; its two R files that define
#   stat.diag.da and its helpers are sourced unchanged).
# - AUC: multds::auc_score against Hmisc::somers2 (the paper computed the AUC with Hmisc).
# - t statistics: multds::t_statistics against stats::t.test(var.equal = TRUE).
suppressPackageStartupMessages({ library(multds); library(jsonlite) })
args <- commandArgs(trailingOnly = TRUE)
tmp <- tempfile()
dir.create(tmp)
utils::untar(args[1], files = c("sma/R/Rdisc.R", "sma/R/Rna.R"), exdir = tmp)
sma <- new.env()
sys.source(file.path(tmp, "sma/R/Rna.R"), envir = sma)
sys.source(file.path(tmp, "sma/R/Rdisc.R"), envir = sma)

set.seed(20101020)
designs <- expand.grid(n1 = c(4, 8, 20, 40), n2 = c(4, 40, 76), mu = c(0, 0.5, 1))
agree <- c(DLDA = 0, DQDA = 0)
total <- 0
datasets <- 0
for (i in seq_len(nrow(designs))) for (r in 1:25) {
  d <- designs[i, ]
  tr <- simulate_data(d$n1, d$n2, 1000, 20, d$mu)
  te <- simulate_data(10, 10, 1000, 20, d$mu)
  x <- center_data(tr$x, "samples")
  xt <- center_data(te$x, "samples")
  sel <- select_variables(x, tr$y, 40)
  ls <- x[, sel]
  ts <- xt[, sel]
  a <- sma$stat.diag.da(ls, tr$y, ts, pool = 1)$pred
  b <- sma$stat.diag.da(ls, tr$y, ts, pool = 0)$pred
  agree["DLDA"] <- agree["DLDA"] + sum(a == dlda(ls, tr$y, ts)$pred)
  agree["DQDA"] <- agree["DQDA"] + sum(b == dqda(ls, tr$y, ts)$pred)
  total <- total + length(a)
  datasets <- datasets + 1
}
auc_max <- 0
for (r in 1:500) {
  n1 <- sample(2:30, 1)
  n2 <- sample(2:30, 1)
  y <- c(rep(1L, n1), rep(2L, n2))
  s <- if (r %% 2) round(rnorm(n1 + n2), 1) else sample(0:3, n1 + n2, TRUE)  # with ties
  h <- Hmisc::somers2(s, as.integer(y == 1))[["C"]]
  auc_max <- max(auc_max, abs(h - auc_score(s, y)))
}
t_max <- 0
for (r in 1:50) {
  x <- matrix(rnorm(30 * 5), 30)
  n1 <- sample(3:27, 1)
  y <- c(rep(1L, n1), rep(2L, 30 - n1))
  tt <- apply(x, 2, function(v) t.test(v[y == 1], v[y == 2], var.equal = TRUE)$statistic)
  t_max <- max(t_max, max(abs(tt - t_statistics(x, y))))
}
out <- list(
  sma_version = "0.5.15",
  datasets = datasets, test_samples = total,
  dlda_agree = unname(agree["DLDA"]), dqda_agree = unname(agree["DQDA"]),
  auc_comparisons = 500, auc_max_abs_diff = auc_max,
  t_comparisons = 250, t_max_abs_diff = t_max,
  hmisc_version = as.character(packageVersion("Hmisc")),
  passed = agree[["DLDA"]] == total && agree[["DQDA"]] == total && auc_max < 1e-12 && t_max < 1e-10)
writeLines(toJSON(out, auto_unbox = TRUE, pretty = TRUE, digits = NA), args[2])
cat(sprintf("DLDA %d/%d, DQDA %d/%d identical; AUC max diff %.2g; t max diff %.2g\n",
            out$dlda_agree, total, out$dqda_agree, total, auc_max, t_max))

# Hypothesis tests for the SVM differences: the paper gives no cost and says the class weights were
# "the proportion of samples from each class". For each cost and weighting, rerun the SVM alone on
# the same data as our runs (the same seeds) and record the minority-class PA.
#   Rscript svm_hypotheses.R SOTIRIOU.rds OUT.json [--reps 200]
suppressPackageStartupMessages({ library(multds); library(jsonlite) })
args <- commandArgs(trailingOnly = TRUE)
here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE))))
source(file.path(here, "settings.R"))
opt <- function(flag, default) { i <- match(flag, args); if (is.na(i)) default else args[i + 1] }
reps <- seq_len(as.integer(opt("--reps", "200")))
dat <- readRDS(args[1])
S <- all_settings()
costs <- c(1, 0.1, 0.03, 0.01, 0.003, 0.001)
weights <- c("proportion", "inverse", "none")

svm_pa <- function(xtr, ytr, xte, yte, cost, w) {
  n <- length(ytr)
  p <- c("1" = sum(ytr == 1) / n, "2" = sum(ytr == 2) / n)
  cw <- switch(w, proportion = p, inverse = rev(p) |> setNames(c("1", "2")), none = NULL)
  fit <- e1071::svm(xtr, factor(ytr, levels = 1:2), kernel = "linear", scale = FALSE, cost = cost, class.weights = cw)
  pr <- as.integer(as.character(predict(fit, xte)))
  c(PA1 = mean(pr[yte == 1] == 1), PA2 = mean(pr[yte == 2] == 2))
}

sim_case <- function(name, test_id) {
  s <- S[[name]]
  res <- array(0, c(length(costs), length(weights), 2), dimnames = list(costs, weights, c("PA1", "PA2")))
  for (r in reps) {
    # The same data as run_replicate(s, r): same seed, same draws, same order.
    set.seed(multds:::seed_of(s$name) + r, kind = "Mersenne-Twister", normal.kind = "Inversion", sample.kind = "Rejection")
    n1 <- round(s$ntrain * s$k1train)
    tr <- simulate_data(n1, s$ntrain - n1, s$p, s$p_de, s$mu2)
    tests <- lapply(s$tests, function(d) { m1 <- round(d$ntest * d$k1test); simulate_data(m1, d$ntest - m1, s$p, s$p_de, s$mu2) })
    g <- match(test_id, vapply(s$tests, `[[`, "", "id"))
    xtr <- center_data(tr$x, "samples")
    xte <- center_data(tests[[g]]$x, "samples")
    sel <- select_variables(xtr, tr$y, s$G)
    for (i in seq_along(costs)) for (j in seq_along(weights))
      res[i, j, ] <- res[i, j, ] + svm_pa(xtr[, sel], tr$y, xte[, sel], tests[[g]]$y, costs[i], weights[j]) / length(reps)
  }
  res
}

er_case <- function(n_neg, n_pos) {
  res <- array(0, c(length(costs), length(weights), 2), dimnames = list(costs, weights, c("PA1", "PA2")))
  for (r in reps) {
    set.seed(r * 7919L + n_pos, kind = "Mersenne-Twister", normal.kind = "Inversion", sample.kind = "Rejection")
    pos <- which(dat$er == 1); neg <- which(dat$er == 0)
    p <- pos[sample.int(length(pos), n_pos + 20)]; q <- neg[sample.int(length(neg), n_neg + 20)]
    tr <- c(p[seq_len(n_pos)], q[seq_len(n_neg)]); te <- c(p[n_pos + 1:20], q[n_neg + 1:20])
    y <- ifelse(dat$er == 1, 1L, 2L)
    xtr <- center_data(dat$x[tr, ], "samples"); xte <- center_data(dat$x[te, ], "samples")
    sel <- select_variables(xtr, y[tr], 40)
    for (i in seq_along(costs)) for (j in seq_along(weights))
      res[i, j, ] <- res[i, j, ] + svm_pa(xtr[, sel], y[tr], xte[, sel], y[te], costs[i], weights[j]) / length(reps)
  }
  res
}

tidy <- function(a) lapply(dimnames(a)[[1]], function(cst) lapply(setNames(dimnames(a)[[2]], dimnames(a)[[2]]),
                                                                   function(w) round(a[cst, w, ], 4))) |> setNames(dimnames(a)[[1]])
out <- list(
  replicates = length(reps), costs = costs, weights = weights,
  af3_k0.1 = list(paper = c(PA1 = 0.03, PA2 = 1), grid = tidy(sim_case("alt20_p1000_k0.10", "bal20"))),
  af3_k0.2 = list(paper = c(PA1 = 0.51, PA2 = 1), grid = tidy(sim_case("alt20_p1000_k0.20", "bal20"))),
  null_k0.2 = list(paper_fig2 = c(PA1 = 0.038), grid = tidy(sim_case("null_p40_k0.20", "bal20"))),
  er_20_5 = list(paper = c(PA1 = 0.94, PA2 = 0.6), grid = tidy(er_case(5, 20))),
  er_45_5 = list(paper = c(PA1 = 0.96, PA2 = 0.49), grid = tidy(er_case(5, 45))))
writeLines(toJSON(out, auto_unbox = TRUE, pretty = TRUE, digits = NA), args[2])
cat("svm hypotheses written\n")

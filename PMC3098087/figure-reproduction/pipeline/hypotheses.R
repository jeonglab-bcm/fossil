# Hypothesis tests for the differences that are not Monte Carlo error.
#   Rscript hypotheses.R SOTIRIOU.rds OUT.json [--reps 200] [--cores 1]
# SVM: the paper gives no cost and says the class weights were "the proportion of samples from each
# class". For each cost and weighting, rerun the SVM alone on the same simulated data as our runs (the
# same seeds; the breast cancer draws use their own seeds) and record the class-specific PA.
# DQDA's AUC: the paper does not say which score it ranked. Rerun DQDA on the same simulated data and
# compute the AUC from several scores.
suppressPackageStartupMessages({ library(multds); library(jsonlite) })
args <- commandArgs(trailingOnly = TRUE)
here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE))))
source(file.path(here, "settings.R"))
opt <- function(flag, default) { i <- match(flag, args); if (is.na(i)) default else args[i + 1] }
reps <- seq_len(as.integer(opt("--reps", "200")))
cores <- as.integer(opt("--cores", "1"))
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

dqda_auc <- function(name) {
  s <- S[[name]]
  scores <- c("difference of the discriminants (ours)", "ratio of the discriminants",
              "distance to Class 1 only", "DLDA's pooled-variance score", "the predicted class (0/1)",
              "DLDA: difference (ours)", "DLDA: ratio")
  acc <- setNames(numeric(length(scores)), scores)
  for (r in reps) {
    set.seed(multds:::seed_of(s$name) + r, kind = "Mersenne-Twister", normal.kind = "Inversion", sample.kind = "Rejection")
    n1 <- round(s$ntrain * s$k1train)
    tr <- simulate_data(n1, s$ntrain - n1, s$p, s$p_de, s$mu2)
    tests <- lapply(s$tests, function(d) { m1 <- round(d$ntest * d$k1test); simulate_data(m1, d$ntest - m1, s$p, s$p_de, s$mu2) })
    xtr <- center_data(tr$x, "samples"); te <- tests[[1]]; xte <- center_data(te$x, "samples")
    sel <- select_variables(xtr, tr$y, s$G)
    a <- xtr[tr$y == 1, sel]; b <- xtr[tr$y == 2, sel]; z <- xte[, sel]
    m1 <- colMeans(a); m2 <- colMeans(b); v1 <- apply(a, 2, var); v2 <- apply(b, 2, var)
    q1 <- colSums((t(z) - m1)^2 / v1) + sum(log(v1)); q2 <- colSums((t(z) - m2)^2 / v2) + sum(log(v2))
    vp <- ((nrow(a) - 1) * v1 + (nrow(b) - 1) * v2) / (nrow(a) + nrow(b) - 2)
    l1 <- colSums((t(z) - m1)^2 / vp); l2 <- colSums((t(z) - m2)^2 / vp)
    sc <- list(q2 - q1, q2 / q1, -q1, dlda(xtr[, sel], tr$y, z)$score,
               as.numeric(dqda(xtr[, sel], tr$y, z)$pred == 1), l2 - l1, l2 / l1)
    for (i in seq_along(sc)) acc[i] <- acc[i] + auc_score(sc[[i]], te$y) / length(reps)
  }
  round(acc, 4)
}


# PAM, SVM and the order of over-sampling and selection: on the same data as our runs (same seeds,
# same draws, same over-sampling), refit with the alternatives below and record PA, PA1 and PA2.
#   PAM: our rule (pamr's default prior, i.e. the class shares of the training set it is given, and the
#   largest threshold with the smallest training error); the prior of the original training set (it
#   differs only after over- or down-sizing); equal priors; the smallest such threshold; 10-fold CV.
#   SVM: weights from the over-sampled set (ours) or from the original training set.
#   Order: variables selected on the over-sampled set (ours) or on the original training set.
pam_variants <- function(xtr, ytr, xte, prior0) {
  dat <- list(x = t(xtr), y = factor(ytr, levels = 1:2))
  pr <- function(fit, thr) as.integer(as.character(pamr::pamr.predict(fit, t(xte), thr, type = "class")))
  utils::capture.output(fit <- pamr::pamr.train(dat))
  best <- fit$threshold[fit$errors == min(fit$errors)]
  utils::capture.output(fit0 <- pamr::pamr.train(dat, prior = prior0))
  best0 <- fit0$threshold[fit0$errors == min(fit0$errors)]
  utils::capture.output(fite <- pamr::pamr.train(dat, prior = c(0.5, 0.5)))
  beste <- fite$threshold[fite$errors == min(fite$errors)]
  utils::capture.output(cv <- pamr::pamr.cv(fit, dat, nfold = min(10, min(table(ytr)))))
  bestcv <- cv$threshold[cv$error == min(cv$error)]
  list("ours" = pr(fit, max(best)), "original prior" = pr(fit0, max(best0)), "equal priors" = pr(fite, max(beste)),
       "smallest threshold" = pr(fit, min(best)), "10-fold CV" = pr(fit, max(bestcv)))
}
pa3 <- function(pred, y) c(PA = mean(pred == y), PA1 = mean(pred[y == 1] == 1), PA2 = mean(pred[y == 2] == 2))
avg <- function(L) { m <- Reduce(`+`, L) / length(L); lapply(m, function(v) round(v, 4)) }

alt_case <- function(name, test_id, which = c("pam", "svm", "order")) {
  s <- S[[name]]
  one <- function(r) {
    set.seed(multds:::seed_of(s$name) + r, kind = "Mersenne-Twister", normal.kind = "Inversion", sample.kind = "Rejection")
    n1 <- round(s$ntrain * s$k1train)
    tr <- simulate_data(n1, s$ntrain - n1, s$p, s$p_de, s$mu2)
    tests <- lapply(s$tests, function(d) { m1 <- round(d$ntest * d$k1test); simulate_data(m1, d$ntest - m1, s$p, s$p_de, s$mu2) })
    g <- match(test_id, vapply(s$tests, `[[`, "", "id"))
    xtr <- center_data(tr$x, if (s$center == "samples") "samples" else "none")
    xte <- center_data(tests[[g]]$x, s$center); yte <- tests[[g]]$y
    idx <- switch(s$correction, none = seq_along(tr$y), over = oversample(tr$y), down = downsize(tr$y))
    xc <- xtr[idx, , drop = FALSE]; yc <- tr$y[idx]
    if (s$center == "variables") xc <- center_data(xc, "variables")
    sel <- select_variables(xc, yc, s$G)
    prior0 <- c(mean(tr$y == 1), mean(tr$y == 2))
    out <- list()
    if ("pam" %in% which) for (v in names(pv <- pam_variants(xc[, sel], yc, xte[, sel], prior0)))
      out[[paste("PAM", v, sep = ": ")]] <- pa3(pv[[v]], yte)
    if ("svm" %in% which) for (w in c("over-sampled set", "original set")) {
      pw <- if (w == "original set") prior0 else c(mean(yc == 1), mean(yc == 2))
      fit <- e1071::svm(xc[, sel], factor(yc, levels = 1:2), kernel = "linear", scale = FALSE, class.weights = c("1" = pw[1], "2" = pw[2]))
      out[[paste("SVM weights from the", w)]] <- pa3(as.integer(as.character(predict(fit, xte[, sel]))), yte)
    }
    if ("order" %in% which) {
      x0 <- if (s$center == "variables") center_data(xtr, "variables") else xtr
      sel0 <- select_variables(x0, tr$y, s$G)
      a <- fit_predict(c("3-NN", "5-NN", "DLDA", "DQDA"), xc[, sel], yc, xte[, sel])
      b <- fit_predict(c("3-NN", "5-NN", "DLDA", "DQDA"), xc[, sel0], yc, xte[, sel0])
      for (m in names(a)) {
        out[[paste(m, "selection after over-sampling (ours)")]] <- pa3(a[[m]]$pred, yte)
        out[[paste(m, "selection before over-sampling")]] <- pa3(b[[m]]$pred, yte)
      }
    }
    out
  }
  res <- parallel::mclapply(reps, one, mc.cores = cores)
  keys <- names(res[[1]])
  setNames(lapply(keys, function(k) avg(lapply(res, `[[`, k))), keys)
}

er_pam <- function(n_neg, n_pos) {
  one <- function(r) {
    set.seed(r * 7919L + n_pos, kind = "Mersenne-Twister", normal.kind = "Inversion", sample.kind = "Rejection")
    pos <- which(dat$er == 1); neg <- which(dat$er == 0)
    p <- pos[sample.int(length(pos), n_pos + 20)]; q <- neg[sample.int(length(neg), n_neg + 20)]
    tr <- c(p[seq_len(n_pos)], q[seq_len(n_neg)]); te <- c(p[n_pos + 1:20], q[n_neg + 1:20])
    y <- ifelse(dat$er == 1, 1L, 2L)
    xtr <- center_data(dat$x[tr, ], "samples"); xte <- center_data(dat$x[te, ], "samples")
    sel <- select_variables(xtr, y[tr], 40)
    pv <- pam_variants(xtr[, sel], y[tr], xte[, sel], c(mean(y[tr] == 1), mean(y[tr] == 2)))
    lapply(pv, pa3, y = y[te])
  }
  res <- parallel::mclapply(reps, one, mc.cores = cores)
  keys <- names(res[[1]])
  setNames(lapply(keys, function(k) avg(lapply(res, `[[`, k))), paste("PAM", keys, sep = ": "))
}

tidy <- function(a) lapply(dimnames(a)[[1]], function(cst) lapply(setNames(dimnames(a)[[2]], dimnames(a)[[2]]),
                                                                   function(w) round(a[cst, w, ], 4))) |> setNames(dimnames(a)[[1]])
out <- list(
  replicates = length(reps), costs = costs, weights = weights,
  af3_k0.1 = list(paper = c(PA1 = 0.03, PA2 = 1), grid = tidy(sim_case("alt20_p1000_k0.10", "bal20"))),
  af3_k0.2 = list(paper = c(PA1 = 0.51, PA2 = 1), grid = tidy(sim_case("alt20_p1000_k0.20", "bal20"))),
  null_k0.2 = list(paper_fig2 = c(PA1 = 0.038), grid = tidy(sim_case("null_p40_k0.20", "bal20"))),
  er_20_5 = list(paper = c(PA1 = 0.94, PA2 = 0.6), grid = tidy(er_case(5, 20))),
  er_45_5 = list(paper = c(PA1 = 0.96, PA2 = 0.49), grid = tidy(er_case(5, 45))),
  dqda_auc = lapply(setNames(c(0.1, 0.2, 0.3, 0.4, 0.5), sprintf("k1train %.1f", c(0.1, 0.2, 0.3, 0.4, 0.5))), function(k)
    list(setting = sprintf("alt20_p1000_k%.2f", k), by_score = as.list(dqda_auc(sprintf("alt20_p1000_k%.2f", k))))),
  dqda_auc_paper = list(DQDA = c(0.91, 0.98, 0.99, 0.99, 0.99), DLDA = c(0.94, 0.98, 0.99, 0.99, 0.99)),
  pam_null_k0.45 = list(paper_fig1 = c(PA1 = 0.2661), res = alt_case("null_p40_k0.45", "bal20", "pam")),
  pam_null_k0.55 = list(paper_fig1 = c(PA1 = 0.7357), res = alt_case("null_p40_k0.55", "bal20", "pam")),
  pam_er_45_5 = list(paper_af13 = c(PA = 0.74, PA_ERpos = 0.95, PA_ERneg = 0.53), res = er_pam(5, 45)),
  over_k0.10 = list(paper_af8 = c(PAM_PA = 0.5077), res = alt_case("over_p1000_k0.10", "bal20", c("pam", "svm"))),
  over_k0.20 = list(res = alt_case("over_p1000_k0.20", "bal20", c("pam", "svm", "order"))),
  af9_k0.05 = list(paper_af9 = c(PAM_PA1 = 0.0231, SVM_PA = 0.5567), res = alt_case("af9_p1000_k0.05", "bal20", c("pam", "svm"))),
  af9_k0.25 = list(res = alt_case("af9_p1000_k0.25", "bal20", c("order"))))
writeLines(toJSON(out, auto_unbox = TRUE, pretty = TRUE, digits = NA), args[2])
cat("hypotheses written\n")

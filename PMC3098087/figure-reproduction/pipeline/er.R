# The breast cancer application (Fig. 6, Additional files 12-14): ER+ against ER- on the
# Sotiriou et al. (2003) data, 500 random training and test sets per setting.
#   Rscript er.R SOTIRIOU.rds OUTDIR [--reps 1:500] [--cores 4] [--only REGEX]
# Class 1 is ER+. Training sets hold n_neg ER- and n_pos ER+ samples; the test set holds 20 of each,
# drawn from the remaining samples. Variables are the 40 probes with the largest |t| on the training
# set. The predictive values use the training proportion of ER+ (kER+), as in the tables.
suppressPackageStartupMessages(library(multds))
args <- commandArgs(trailingOnly = TRUE)
opt <- function(flag, default) { i <- match(flag, args); if (is.na(i)) default else args[i + 1] }
dat <- readRDS(args[1])
outdir <- args[2]
reps <- eval(parse(text = opt("--reps", "1:500")))
cores <- as.integer(opt("--cores", "1"))
only <- opt("--only", NA)
dir.create(outdir, showWarnings = FALSE, recursive = TRUE)

er_settings <- function() {
  s <- list()
  designs <- rbind(data.frame(n_neg = 5, n_pos = c(5, 10, 20, 30, 45)),
                   data.frame(n_neg = 10, n_pos = c(10, 20, 30, 45)))
  for (ctr in c("samples", "variables")) for (i in seq_len(nrow(designs))) {
    d <- designs[i, ]
    corrs <- if (d$n_pos == d$n_neg) "none" else c("none", "over", "down", "multds")
    for (corr in corrs) {
      methods <- classifier_names()
      if (corr == "multds" && ctr == "variables") methods <- c("3-NN", "DLDA", "PLR")
      nm <- sprintf("er_%s_%s_neg%d_pos%d", ctr, corr, d$n_neg, d$n_pos)
      s[[nm]] <- list(name = nm, n_neg = d$n_neg, n_pos = d$n_pos, center = ctr, correction = corr,
                      methods = methods)
    }
  }
  s
}

seed_of <- function(name) {
  codes <- utf8ToInt(name)
  (sum(codes * seq_along(codes) * 131L) %% 200000L) * 10000L
}

er_replicate <- function(s, rep) {
  set.seed(seed_of(s$name) + rep, kind = "Mersenne-Twister", normal.kind = "Inversion",
           sample.kind = "Rejection")
  pos <- which(dat$er == 1)
  neg <- which(dat$er == 0)
  p <- pos[sample.int(length(pos), s$n_pos + 20)]
  q <- neg[sample.int(length(neg), s$n_neg + 20)]
  tr <- c(p[seq_len(s$n_pos)], q[seq_len(s$n_neg)])
  te <- c(p[s$n_pos + 1:20], q[s$n_neg + 1:20])
  y <- ifelse(dat$er == 1, 1L, 2L)
  xtr <- dat$x[tr, , drop = FALSE]
  xte <- dat$x[te, , drop = FALSE]
  if (s$center == "samples") {
    xtr <- center_data(xtr, "samples")
    xte <- center_data(xte, "samples")
  } else {
    xte <- center_data(xte, "variables")
  }
  ytr <- y[tr]
  yte <- y[te]
  if (s$correction == "multds") {
    fp <- multds_predict(s$methods, xtr, ytr, xte, G = 40, B = 101,
                         center = if (s$center == "variables") "variables" else "none")
  } else {
    idx <- switch(s$correction, none = seq_along(ytr), over = oversample(ytr), down = downsize(ytr))
    xc <- xtr[idx, , drop = FALSE]
    yc <- ytr[idx]
    if (s$center == "variables") xc <- center_data(xc, "variables")
    sel <- select_variables(xc, yc, 40)
    fp <- fit_predict(s$methods, xc[, sel, drop = FALSE], yc, xte[, sel, drop = FALSE])
  }
  k <- s$n_pos / (s$n_pos + s$n_neg)
  do.call(rbind, lapply(s$methods, function(m) {
    ev <- evaluate(yte, fp[[m]]$pred, fp[[m]]$score, k)
    data.frame(test = "bal40", method = m, rep = rep, t(ev), check.names = FALSE)
  }))
}

S <- er_settings()
if (!is.na(only)) S <- S[grepl(only, names(S))]
for (nm in names(S)) {
  f <- file.path(outdir, paste0(nm, ".rds"))
  if (file.exists(f) && setequal(unique(readRDS(f)$rep), reps)) next
  t0 <- Sys.time()
  res <- parallel::mclapply(reps, function(r) er_replicate(S[[nm]], r), mc.cores = cores)
  bad <- vapply(res, inherits, TRUE, what = "try-error")
  if (any(bad)) stop(as.character(res[[which(bad)[1]]]))
  r <- do.call(rbind, res)
  r$setting <- nm
  saveRDS(r, f)
  cat(sprintf("%s %d reps %.1f s\n", nm, length(reps), as.numeric(Sys.time() - t0, units = "secs")))
}

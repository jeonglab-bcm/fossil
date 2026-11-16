# Which definition of SWSFS's Error(i) gives the paper's Fig. 3 counts? (hypothesis test)
#
# usage: Rscript error_variants.R MODEL MAF R2 FIRST LAST OUT.json
#
# Regenerates the study's data sets (same seeds) and the study's first forest (so the SNP order is
# the study's), then runs the SWSFS loop (w = 20) with Error(i) defined as
#   oob_final   the out-of-bag error after the last tree (the study's definition)
#   oob_mean    the out-of-bag error averaged over the forest's growth (err.rate's OOB column, mean)
#   bagging     the final out-of-bag error with mtry = i (every SNP tried at every split)
#   balanced    the mean of the two classes' out-of-bag errors after the last tree
# and records k = i - w for each.
suppressPackageStartupMessages({ library(epiforest); library(jsonlite); library(randomForest) })
args <- commandArgs(trailingOnly = TRUE)
model <- as.integer(args[1]); maf <- as.numeric(args[2]); r2 <- as.numeric(args[3])
first <- as.integer(args[4]); last <- as.integer(args[5]); out <- args[6]
LAMBDA <- c(0.3, 0.5, 1.0); MAFS <- c(0.05, 0.1, 0.2, 0.5); R2S <- c(0.7, 1.0); W <- 20
recs <- list()
for (rep in first:last) {
  seed <- model * 100000 + match(maf, MAFS) * 10000 + match(r2, R2S) * 1000 + rep
  set.seed(seed, kind = "Mersenne-Twister", normal.kind = "Inversion", sample.kind = "Rejection")
  d <- simulate_dataset(model, LAMBDA[model], maf, r2, prevalence = 0.1, n_markers = 1000)
  x <- as.data.frame(lapply(as.data.frame(d$geno), factor, levels = 0:2))
  y <- factor(d$status, levels = c(0, 1))
  g <- gini_importance(d$geno, d$status, ntree = 500, x = x)
  o <- order(-g)
  ks <- list()
  for (v in c("oob_final", "oob_mean", "bagging", "balanced")) {
    err <- numeric(0); i <- 0; k <- NA
    repeat {
      i <- i + 1
      xi <- x[, o[seq_len(i)], drop = FALSE]
      rf <- randomForest(xi, y, ntree = 500, mtry = if (v == "bagging") i else max(floor(sqrt(i)), 1))
      e <- switch(v, oob_final = rf$err.rate[500, "OOB"], oob_mean = mean(rf$err.rate[, "OOB"]),
                  bagging = rf$err.rate[500, "OOB"], balanced = mean(rf$err.rate[500, c("0", "1")]))
      err[i] <- e
      if (i > W && which.min(err[(i - W):i]) == 1) { k <- i - W; break }
      if (i >= 300) { k <- NA; break }
    }
    ks[[v]] <- k
  }
  recs[[length(recs) + 1]] <- list(model = model, maf = maf, r2 = r2, rep = rep, seed = seed,
                                   disease_rank = match(d$disease, o), k = ks)
  cat(rep, unlist(ks), "\n")
}
writeLines(toJSON(recs, auto_unbox = TRUE), out)

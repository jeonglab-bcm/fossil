# Why does SWSFS keep fewer SNPs than in the paper's Fig. 3? (hypothesis tests)
#
# usage: Rscript swsfs_variants.R OUT_JSON MODEL MAF R2 REPS [--variant NAME]
#
# For each data set (the same seeds as sim_study.R), grow the full out-of-bag error curve for the
# top 1..100 SNPs instead of stopping at the window rule, then apply each candidate stopping rule
# to the curve:
#   paper            the first i > w whose window [i - w, i] has its first minimum at i - w (ours)
#   last_min         the same, but with the last minimum of the window (ties go to the right)
#   global_min       the minimum of the whole curve (1..100), as the naive greedy SFS would give
# and each forest setting:
#   ntree500         randomForest's default, as in our study (curve identical to the study's
#                    first k + 20 forests: the same random numbers are drawn in the same order)
#   ntree2000        four times as many trees in every forest
#   mtry31           every SWSFS forest tries floor(sqrt(1000)) = 31 SNPs per split (all of them
#                    when there are fewer), as if mtry were set once for the whole data
suppressPackageStartupMessages({ library(epiforest); library(jsonlite); library(randomForest) })
args <- commandArgs(trailingOnly = TRUE)
out <- args[1]; model <- as.integer(args[2]); maf <- as.numeric(args[3]); r2 <- as.numeric(args[4])
reps <- eval(parse(text = args[5]))
variant <- if (length(args) >= 7 && args[6] == "--variant") args[7] else "ntree500"
LAMBDA <- c(0.3, 0.5, 1.0); MAFS <- c(0.05, 0.1, 0.2, 0.5); R2S <- c(0.7, 1.0)
W <- 20; IMAX <- 100

rules <- function(err) {
  first_window <- function(tie_last) {
    for (i in seq_along(err)) if (i > W) {
      win <- err[(i - W):i]
      pos <- if (tie_last) max(which(win == min(win))) else which.min(win)
      if (pos == 1) return(i - W)
    }
    NA_integer_
  }
  list(paper = first_window(FALSE), last_min = first_window(TRUE), global_min = which.min(err))
}

recs <- list()
for (rep in reps) {
  seed <- model * 100000 + match(maf, MAFS) * 10000 + match(r2, R2S) * 1000 + rep
  set.seed(seed, kind = "Mersenne-Twister", normal.kind = "Inversion", sample.kind = "Rejection")
  d <- simulate_dataset(model, LAMBDA[model], maf, r2, prevalence = 0.1, n_markers = 1000)
  ntree <- if (variant == "ntree2000") 2000 else 500
  x <- as.data.frame(lapply(as.data.frame(d$geno), factor, levels = 0:2))
  y <- factor(d$status, levels = c(0, 1))
  gini <- gini_importance(d$geno, d$status, ntree = ntree, x = x)
  ord <- order(gini, decreasing = TRUE)
  err <- numeric(IMAX)
  for (i in seq_len(IMAX)) {
    xi <- x[, ord[seq_len(i)], drop = FALSE]
    rf <- if (variant == "mtry31") randomForest(xi, y, ntree = ntree, mtry = min(i, 31))
          else randomForest(xi, y, ntree = ntree)
    err[i] <- rf$err.rate[ntree, "OOB"]
  }
  recs[[length(recs) + 1]] <- list(model = model, maf = maf, r2 = r2, rep = rep, seed = seed,
                                   variant = variant, rank = match(d$disease, ord),
                                   errors = round(err, 6), k = rules(err))
  cat(sprintf("%s rep %d: k paper %d, last_min %d, global_min %d\n", variant, rep,
              recs[[length(recs)]]$k$paper, recs[[length(recs)]]$k$last_min, recs[[length(recs)]]$k$global_min))
}
writeLines(toJSON(recs, auto_unbox = TRUE, digits = NA), out)

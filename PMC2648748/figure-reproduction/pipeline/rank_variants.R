# Does another setting of the first forest rank the disease markers higher? (hypothesis test)
#
# usage: Rscript rank_variants.R MODEL MAF R2 FIRST LAST OUT.json
#
# Where our epiForest power is below the paper's (models 2 and 3, r2 = 1, small MAF), the disease
# markers are rarely among the candidates, even among the top i = k + w. This regenerates the
# study's data sets (same seeds) and refits only the first forest under each setting the paper
# leaves open, recording the disease markers' gini ranks:
#   factor_ntree500   the study's setting (three-level factors, 500 trees); the first data set
#                     must give the study's ranks (same random numbers in the same order)
#   numeric_ntree500  genotypes as numbers 0/1/2 instead of factors
#   factor_ntree2000  2000 trees
#   factor_mtry100    mtry = 100 instead of floor(sqrt(1000)) = 31
suppressPackageStartupMessages({ library(epiforest); library(jsonlite) })
args <- commandArgs(trailingOnly = TRUE)
model <- as.integer(args[1]); maf <- as.numeric(args[2]); r2 <- as.numeric(args[3])
first <- as.integer(args[4]); last <- as.integer(args[5]); out <- args[6]
LAMBDA <- c(0.3, 0.5, 1.0)
MAFS <- c(0.05, 0.1, 0.2, 0.5)
R2S <- c(0.7, 1.0)

variants <- list(
  factor_ntree500 = list(numeric = FALSE, ntree = 500, mtry = NULL),
  numeric_ntree500 = list(numeric = TRUE, ntree = 500, mtry = NULL),
  factor_ntree2000 = list(numeric = FALSE, ntree = 2000, mtry = NULL),
  factor_mtry100 = list(numeric = FALSE, ntree = 500, mtry = 100)
)

recs <- list()
for (rep in first:last) {
  seed <- model * 100000 + match(maf, MAFS) * 10000 + match(r2, R2S) * 1000 + rep
  set.seed(seed, kind = "Mersenne-Twister", normal.kind = "Inversion", sample.kind = "Rejection")
  d <- simulate_dataset(model, LAMBDA[model], maf, r2, prevalence = 0.1, n_markers = 1000)
  ranks <- list()
  for (v in names(variants)) {
    s <- variants[[v]]
    x <- if (s$numeric) as.data.frame(d$geno) else NULL
    g <- gini_importance(d$geno, d$status, ntree = s$ntree, mtry = s$mtry, x = x)
    o <- order(-g)
    ranks[[v]] <- match(d$disease, o)
  }
  recs[[length(recs) + 1]] <- list(model = model, maf = maf, r2 = r2, rep = rep, seed = seed, rank = ranks)
}
writeLines(toJSON(recs, auto_unbox = TRUE), out)

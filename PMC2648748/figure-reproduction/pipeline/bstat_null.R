# Check of the B statistic's null distribution (our derivation of the "shifted chi-squared").
#
# usage: Rscript bstat_null.R OUT_JSON [REPS]
#
# The paper says only that 2B follows a shifted chi-squared distribution with 3^k - 1 degrees of
# freedom (3^k - 3^t for the conditional B). The package derives the shift from Stirling's
# expansion of each Dirichlet-multinomial term (b_shift). Here we simulate data with no
# association (1000 cases, 1000 controls, 60 independent SNPs with MAF from U(0.05, 0.5), as in
# the paper's null markers), compute 2B - shift for single SNPs, pairs and triples, with and
# without conditioning, and compare the mean, the variance and the 5% and 1% tails with the
# chi-squared distribution. The check passes when, for one- and two-way tests, the mean is within
# 5% of the degrees of freedom and the share of p < 0.05 is within [0.04, 0.06]; three-way tests
# (27 cells, many of them sparse) are reported, not required.
suppressPackageStartupMessages({ library(epiforest); library(jsonlite) })
args <- commandArgs(trailingOnly = TRUE)
reps <- if (length(args) >= 2) as.integer(args[2]) else 200
set.seed(20090130, kind = "Mersenne-Twister", normal.kind = "Inversion", sample.kind = "Rejection")
n <- 2000; L <- 60
res <- list()
for (rep in seq_len(reps)) {
  maf <- runif(L, 0.05, 0.5)
  g <- matrix(rbinom(n * L, 2, rep(maf, each = n)), n)
  storage.mode(g) <- "integer"
  st <- rep(1:0, each = n / 2)
  pr <- t(combn(L, 2))[sample(choose(L, 2), 200), ]
  tr <- t(combn(L, 3))[sample(choose(L, 3), 200), ]
  add <- function(nm, x) res[[nm]] <<- rbind(res[[nm]], x)
  add("one-way", b_test(g, st, matrix(1:L, ncol = 1)))
  add("two-way", b_test(g, st, pr))
  add("two-way given 1", b_test(g, st, pr, given = 1L))
  add("three-way", b_test(g, st, tr))
  add("three-way given 1", b_test(g, st, tr, given = 1L))
  add("three-way given 2", b_test(g, st, tr, given = 1:2))
}
rows <- lapply(names(res), function(nm) {
  r <- res[[nm]]
  x <- 2 * r$B - r$shift
  list(test = nm, df = r$df[1], n = nrow(r), mean = round(mean(x), 4), var = round(var(x), 4),
       share_p_below_0.05 = round(mean(r$p < 0.05), 4), share_p_below_0.01 = round(mean(r$p < 0.01), 4))
})
req <- Filter(function(r) !grepl("three", r$test), rows)
passed <- all(vapply(req, function(r) abs(r$mean - r$df) / r$df < 0.05 &&
                       r$share_p_below_0.05 >= 0.04 && r$share_p_below_0.05 <= 0.06, TRUE))
detail <- paste0(paste(vapply(rows, function(r) sprintf("%s: mean %.2f (df %d), p<0.05 in %.1f%%",
                                                        r$test, r$mean, r$df, 100 * r$share_p_below_0.05), ""),
                       collapse = "; "), " (", reps, " null data sets)")
writeLines(toJSON(list(passed = passed, detail = detail, reps = reps, rows = rows), auto_unbox = TRUE,
                  pretty = TRUE, digits = NA), args[1])
cat(detail, "\npassed:", passed, "\n")

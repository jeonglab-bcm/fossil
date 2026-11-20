# Writes the bundled example files of misscox (inst/extdata). Run from the package folder:
#   Rscript scripts/make_example_data.R
# The expected outputs are the paper's printed values, typed from the article, not computed here.
suppressMessages(library(misscox))
ext <- "inst/extdata"
# The paper's missingness design (Methods): shares of the incomplete cases.
write.csv(data.frame(
  term = c("X3", "X2", "X5", "X8", "X2 and X3", "X5 and X2", "X8 and X3"),
  share = c(0.70, 0.55, 0.20, 0.10, 0.35, 0.10, 0.05)), file.path(ext, "missing_shares.csv"),
  row.names = FALSE)
# Table 3 of the paper, as printed.
write.csv(data.frame(pair = c("X2|MX3", "X5|MX2", "X8|MX3"),
  pct5 = c("101.12", "42.04", "45.14"), pct10 = c("45.5", "20.78", "14.23"),
  pct25 = c("15.68", "7.41", "5.44"), pct50 = c("5.50", "3.00", "1.92"),
  pct75 = c("2.17", "1.51", "0.92")), file.path(ext, "table3_expected.csv"), row.names = FALSE)
# The linear predictor of the paper's Methods (the full Cox model on GBSG2), as printed.
pc <- c(X1 = "-0.0088", X2 = "0.051", X3 = "-0.0023", X4 = "0.00015", X5 = "-0.349", X6 = "0.225",
        X7 = "0.67", X8d1 = "0.223", X8d2 = "0.331")
write.csv(data.frame(term = names(pc), printed = unname(pc)), file.path(ext, "lp_expected.csv"),
          row.names = FALSE)
# One simulated cohort of 1000 cases with 25% MAR missingness (seeded), to try the methods on.
cv <- gbsg_covariates()
x <- simulate_cohort(1000, generation_parameters(cv), seed = 2010L)
xm <- impose_missing(x, "MAR", 0.25, seed = 7L)
xm$lp <- NULL
num <- vapply(xm, is.numeric, TRUE)
xm[num] <- lapply(xm[num], function(v) signif(v, 7))
write.csv(xm, file.path(ext, "example_cohort_mar25.csv"), row.names = FALSE)

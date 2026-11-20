# The data-description results of the paper, recomputed from GBSG2 with the package:
# Table 1, the skewness and correlations in the text, the linear predictor (full Cox model),
# the Figure 1 histograms (R's default breaks) and Table 3.
#   Rscript gbsg_targets.R targets.json
suppressMessages(library(misscox))
out_file <- commandArgs(TRUE)[1]
cv <- gbsg_covariates()
tr <- transform_covariates(cv)
env <- new.env(); utils::data("GBSG2", package = "TH.data", envir = env); g <- env$GBSG2

table1 <- lapply(names(tr), function(v) list(variable = v, mean = mean(tr[[v]]), sd = sd(tr[[v]])))
raw <- list(X2 = cv$X2, X3 = cv$X3, X4 = cv$X4, X8 = cv$X8)
skew <- lapply(raw, function(x) list(b1 = skewness(x, 3), g1 = skewness(x, 1), G1 = skewness(x, 2)))
skew_tr <- lapply(tr[c("X2", "X3", "X4", "X8")], function(x) skewness(x, 3))
pairs <- list(c("X1", "X6"), c("X3", "X4"), c("X2", "X8"), c("X5", "X6"))
cors <- lapply(pairs, function(p) list(pair = paste(p, collapse = "-"),
  raw = cor(cv[[p[1]]], cv[[p[2]]]), transformed = cor(tr[[p[1]]], tr[[p[2]]])))
fits <- lapply(c("efron", "breslow"), function(t) {
  f <- fit_full_cox(cv, ties = t); as.list(coef(f)) })
names(fits) <- c("efron", "breslow")
h <- function(x) { hh <- graphics::hist(x, plot = FALSE); list(breaks = hh$breaks, counts = hh$counts) }
hist1 <- list(age = h(g$age), pnodes = h(g$pnodes), progrec = h(g$progrec), estrec = h(g$estrec),
  horTh = h(as.integer(g$horTh) - 1), menostat = h(as.integer(g$menostat)),
  tgrade = h(as.integer(g$tgrade)), tsize = h(g$tsize),
  log_pnodes = h(log(g$pnodes)), log_progrec = h(log(g$progrec + 1)),
  log_estrec = h(log(g$estrec + 1)), log_tsize = h(log(g$tsize)))
t3 <- table3_odds_ratios()
d <- lapply(c(0.05, 0.10, 0.25, 0.50, 0.75), function(l) {
  m <- missing_design(l); list(level = l, counts = as.list(m$counts), overlaps = as.list(m$overlaps)) })
res <- list(n = nrow(cv), events = sum(cv$status), table1 = table1, skewness = skew,
  skewness_transformed = skew_tr, correlations = cors, cox = fits,
  histograms = hist1, table3 = lapply(seq_len(nrow(t3)), function(i) as.list(t3[i, ])),
  design = d, r = R.version.string,
  packages = list(survival = as.character(packageVersion("survival")),
                  TH.data = as.character(packageVersion("TH.data")),
                  misscox = as.character(packageVersion("misscox"))))
writeLines(jsonlite::toJSON(res, auto_unbox = TRUE, digits = NA, pretty = TRUE), out_file)

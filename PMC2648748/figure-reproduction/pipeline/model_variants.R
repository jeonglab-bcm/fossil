# Which reading of the paper's disease models gives its chi-squared powers? (hypothesis tests)
#
# usage: Rscript model_variants.R PUBLISHED_VALUES OUT_JSON
#
# The single-locus chi-squared test needs no random forest, so its power can be computed exactly
# from the genotype distributions of cases and controls (non-central chi-squared with 2 degrees
# of freedom, 1000 cases and 1000 controls, threshold 0.05 / 1000; the two loci are independent,
# so both are found with the product of the two powers). This compares, for every one of the 24
# settings, the published chi-squared bar with each reading of the models:
#   marchini_odds   Marchini's tables as odds, prevalence 0.1 (the paper's citation)
#   epimode_odds    model 2 with the table of epiMODE (Tang et al. 2009, the same group), odds
#   epimode_risk    the same table as relative risks (epiMODE's Text S1)
#   epimode_risk_K01  ... with prevalence 0.01 for model 2 (epiMODE's setting)
#   marchini_odds_K01 Marchini's model 2 with prevalence 0.01
# and, for the LD between each disease locus and its marker:
#   r2_as_r         the r^2 value used as r (so r^2 = 0.49 at "0.7")
suppressPackageStartupMessages({ library(epiforest); library(jsonlite) })
args <- commandArgs(trailingOnly = TRUE)
pub <- fromJSON(args[1], simplifyVector = FALSE)
MAFS <- c(0.05, 0.1, 0.2, 0.5)
LAMBDA <- c(0.3, 0.5, 1.0)
crit <- qchisq(1 - 0.05 / 1000, 2)

trans <- function(maf, r2) {
  q <- ld_transition(maf, r2)
  t(sapply(0:2, function(g) {
    out <- rep(0, 3)
    a <- dbinom(0:g, g, q[1]); b <- dbinom(0:(2 - g), 2 - g, q[2])
    for (i in 0:g) for (j in 0:(2 - g)) out[i + j + 1] <- out[i + j + 1] + a[i + 1] * b[j + 1]
    out
  }))
}

chisq_power <- function(model, maf, r2, prev = 0.1, scale = "odds", table = "epimode") {
  dm <- tryCatch(disease_model(model, LAMBDA[model], maf, prev, scale = scale, table = table),
                 error = function(e) NULL)
  if (is.null(dm)) return(NA_real_)
  hw <- c((1 - maf)^2, 2 * maf * (1 - maf), maf^2)
  w <- outer(hw, hw)
  P <- dm$penetrance
  pc <- w * P / sum(w * P)
  pu <- w * (1 - P) / sum(w * (1 - P))
  T <- trans(maf, r2)
  pw <- 1
  for (loc in 1:2) {
    mc <- as.vector((if (loc == 1) rowSums(pc) else colSums(pc)) %*% T)
    mu <- as.vector((if (loc == 1) rowSums(pu) else colSums(pu)) %*% T)
    D <- 1000 * mc; U <- 1000 * mu; E <- (D + U) / 2
    ncp <- sum(((D - E)^2 + (U - E)^2) / E)
    pw <- pw * pchisq(crit, 2, ncp = ncp, lower.tail = FALSE)
  }
  100 * pw
}

variants <- list(
  marchini_odds = list(table = "marchini"),
  epimode_odds = list(table = "epimode"),
  epimode_risk = list(table = "epimode", scale = "risk"),
  epimode_risk_K01 = list(table = "epimode", scale = "risk", prev2 = 0.01),
  marchini_odds_K01 = list(table = "marchini", prev2 = 0.01),
  epimode_odds_r2_as_r = list(table = "epimode", r2fun = function(r2) r2^2)
)
panels <- list(c(1, 0.7), c(2, 0.7), c(3, 0.7), c(1, 1.0), c(2, 1.0), c(3, 1.0))
res <- list()
for (vn in names(variants)) {
  v <- variants[[vn]]
  rows <- list()
  for (p in seq_along(panels)) {
    model <- panels[[p]][1]; r2 <- panels[[p]][2]
    for (g in 1:4) {
      published <- NA
      for (b in pub$fig2[[p]]$bars) if (b$maf_index == g - 1 && b$method_index == 3) published <- b$count
      prev <- if (!is.null(v$prev2) && model == 2) v$prev2 else 0.1
      rr <- if (!is.null(v$r2fun)) v$r2fun(r2) else r2
      pw <- chisq_power(model, MAFS[g], rr, prev = prev,
                        scale = if (is.null(v$scale)) "odds" else v$scale, table = v$table)
      tol <- if (is.na(pw)) NA else { q <- (published + pw + 1) / 202; 100 * 1.96 * sqrt(2 * q * (1 - q) / 100) }
      rows[[length(rows) + 1]] <- list(model = model, r2 = r2, maf = MAFS[g], published = published,
                                       expected_power = if (is.na(pw)) NULL else round(pw, 2),
                                       within_mc = if (is.na(pw)) FALSE else abs(pw - published) <= tol)
    }
  }
  within <- vapply(rows, function(r) isTRUE(r$within_mc), TRUE)
  m2 <- vapply(rows, function(r) r$model == 2, TRUE)
  res[[vn]] <- list(settings_within_mc = sum(within), model2_within_mc = sum(within & m2),
                    feasible = sum(vapply(rows, function(r) !is.null(r$expected_power), TRUE)),
                    rows = rows)
}
writeLines(toJSON(res, auto_unbox = TRUE, pretty = TRUE, digits = NA, null = "null"), args[2])
for (vn in names(res)) cat(sprintf("%-22s %2d of 24 settings within MC error (model 2: %d of 8; feasible %d)\n",
                                   vn, res[[vn]]$settings_within_mc, res[[vn]]$model2_within_mc, res[[vn]]$feasible))

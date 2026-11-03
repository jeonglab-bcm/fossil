# S1 high-variance model (highvar.fitness, highvar.selection; S1 lines 71-87) vs Eqs 24-29.
source(file.path(dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])), "common.R"))
source(file.path(ANALYSIS_DIR, "reference", "paper_models.R"))
s1 <- load_s1()
vec <- function(J, m) { v <- numeric(m); v[J] <- 1; v }
fa <- list(alpha = 0.05)

# (a) S1 uses 1 - pchisq(ratio, |J| - 1), the upper tail; Eq 25 prints the CDF F_chi2.
set.seed(1)
d <- alg2("highvar", p = 30, q = 6, zeta = 0.2)
chr <- vec(d$J, 20)
v <- instrument(s1$highvar.fitness)
loc <- bind(v, d$x, fa)(chr)
up <- paper_highvar(chr, d$x, 0.05, "upper", floor = 2e-16)
pr <- paper_highvar(chr, d$x, 0.05, "printed")
check("10.1", max(abs(loc$var.pvals - up$p)) < 1e-12 && abs(loc$score - up$score) < 1e-9 * up$score,
      "S1 p-values and score equal Eqs 24-29 with the upper tail 1 - F (and a 2e-16 floor)",
      sprintf("score %.2f vs %.2f", loc$score, up$score))
check("10.2", length(intersect(pr$features, d$I)) < length(intersect(up$features, d$I)),
      "Eq 25 as printed (CDF) selects low-variance rows instead",
      sprintf("implanted rows selected: printed %d, upper tail %d, of %d",
              length(intersect(pr$features, d$I)), length(intersect(up$features, d$I)), length(d$I)))

# (b) The statistic. Under H0, var_J / var_J' ~ F(|J|-1, |J'|-1), and (|J|-1) var_J / sigma^2 ~ chi2(|J|-1).
#     Comparing the bare ratio (mean ~1) with chi2(|J|-1) (mean |J|-1) makes the test conservative for
#     every |J| > 2. Both the paper and S1 do this.
set.seed(2)
null <- matrix(rnorm(4000 * 20), 4000, 20)
sizes <- c(2, 3, 5, 10, 18)
rate <- t(vapply(sizes, function(k) {
  chr <- vec(1:k, 20)
  p <- bind(instrument(s1$highvar.fitness), null, fa)(chr)$var.pvals
  c(s1 = mean(p < 0.05), ftest = mean(ftest_highvar(chr, null, 0.05)$p < 0.05))
}, numeric(2)))
check("10.3", all(rate[sizes %in% c(5, 10), "s1"] < 0.002) && rate[sizes == 18, "s1"] > 0.1 &&
        all(abs(rate[, "ftest"] - 0.05) < 0.015),
      "type I error at alpha 0.05 on N(0,1) noise (m = 20): S1 ~0 for mid |J|, 0.14 at |J| = 18 (|J'| = 2); F test 0.05",
      paste(sprintf("|J|=%d: %.3f vs %.3f", sizes, rate[, "s1"], rate[, "ftest"]), collapse = "; "))
need <- rbind(s1 = qchisq(0.95, sizes - 1), ftest = qf(0.95, sizes - 1, 20 - sizes - 1))
note("variance ratio needed for p < 0.05 (m = 20): %s",
     paste(sprintf("|J|=%d: %.1f vs %.1f", sizes, need["s1", ], need["ftest", ]), collapse = "; "))

# (c) Consequence on Algorithm 2 'highvar' data: along nested subsets of the true J, S1's fitness peaks
#     at a subset; the F-test version peaks at (or near) the full J. Sample recall bounds the F-measure.
set.seed(3)
peak <- t(replicate(60, {
  repeat { dd <- alg2("highvar"); if (dd$q >= 6 && dd$p >= 5) break }
  ord <- sample(dd$J)
  ks <- 2:dd$q
  s_s1 <- vapply(ks, function(k) bind(s1$highvar.fitness, dd$x, fa)(vec(ord[1:k], 20)), 1)
  s_f <- vapply(ks, function(k) ftest_highvar(vec(ord[1:k], 20), dd$x, 0.05)$score, 1)
  c(s1 = ks[which.max(s_s1)] / dd$q, ftest = ks[which.max(s_f)] / dd$q)
}))
check("10.4", mean(peak[, "s1"] < 0.75) > mean(peak[, "ftest"] < 0.75),
      "on nested subsets of the implanted columns, S1 fitness peaks short of the full J more often than the F test",
      sprintf("peak |J_k|/q < 0.75 in %.0f%% (S1) vs %.0f%% (F test) of 60 datasets; medians %.2f vs %.2f",
              100 * mean(peak[, "s1"] < 0.75), 100 * mean(peak[, "ftest"] < 0.75),
              median(peak[, "s1"]), median(peak[, "ftest"])))
done()

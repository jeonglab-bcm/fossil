# S1 dysregulation-vs-outcome model (getFitnesses, featureSelection.dysregSurv; S1 lines 91-186)
# vs Eqs 30-44.
source(file.path(dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])), "common.R"))
source(file.path(ANALYSIS_DIR, "reference", "paper_models.R"))
s1 <- load_s1()
vec <- function(J, m) { v <- numeric(m); v[J] <- 1; v }
gi <- instrument(s1$getFitnesses)
si <- instrument(s1$featureSelection.dysregSurv)
q <- function(expr) suppressWarnings(expr) # prcomp warns that na.action is ignored (S1:106)

# Test data: 80 samples. Rows 1-6 high on J, rows 7-12 low on J, rows 13-40 share a column profile
# on J (correlated), rows 41-60 noise. Survival is random.
make <- function(J, seed, m = 80) {
  set.seed(seed)
  x <- matrix(runif(60 * m), 60, m)
  x[1:6, J] <- runif(6 * length(J), 0.9, 1)
  x[7:12, J] <- runif(6 * length(J), 0, 0.1)
  prof <- rnorm(length(J))
  x[13:40, J] <- 0.5 + 0.15 * matrix(prof, 28, length(J), byrow = TRUE) + matrix(rnorm(28 * length(J), 0, 0.1), 28)
  x
}
surv <- function(m = 80, seed = 9) { set.seed(seed); Surv(rexp(m, 0.01), rbinom(m, 1, 0.7)) }
fa <- list(consistency = 0.8, rho = 0.5, alpha = 0.05, surv = surv())

# (a) alllow.rows <- which(1-pmatMeans < (1-consistency)) is pmatMeans > consistency again (S1:98, 146).
J <- 1:20
x <- make(J, 1)
L <- q(bind(gi, x, fa)(vec(J, 80)))
sel <- q(bind(s1$featureSelection.dysregSurv, x, fa)(J))
check("11.1", identical(L$alllow.rows, L$allhigh.rows) && setequal(L$allhigh.rows, 1:6),
      "'all-low' rows are the 'all-high' rows again; the low rows 7-12 are in neither list")
check("11.2", L$allhigh.score == length(J) * 6,
      "block score is |J| * n_high: each row adds m + (1 - m) = 1, the same as Eq 16", sprintf("%.0f", L$allhigh.score))
check("11.3", !any(7:12 %in% L$rowsForCor),
      "rows low on J (scaled mean < 1 - consistency) are not correlation candidates either")
L2 <- q(bind(si, x, modifyList(fa, list(rho = 1.01)))(J)) # no row passes |rho| > 1.01: block branch wins
check("11.4", !L2$useCor && identical(sort(L2$features), sort(c(1:6, 1:6))),
      "when the block branch wins, featureSelection.dysregSurv returns each high row twice",
      paste("features:", paste(sort(L2$features), collapse = ",")))

# (b) Coordinator finding: rowsForCor still contains seedRow, so cor.test(seed, seed) is in the sum.
#     getFitnesses does not floor p (S1:116; the selection function does, S1:163). R's Spearman test
#     returns p = 0 for rho = 1 at n = 10-15 and n >= 27 without ties, and at every n with ties.
p_self <- vapply(3:40, function(n) cor.test(1:n, 1:n, method = "spearman")$p.value, 1)
zero_n <- (3:40)[p_self == 0]
check("11.5", identical(zero_n, c(10:15, 27:40)), "cor.test(1:n, 1:n, 'spearman') gives p = 0 for n in 10-15 and 27-40",
      paste("p > 0 at n =", paste((3:40)[p_self > 0], collapse = ",")))
check("11.6", L$seedRow %in% L$rowsForCor && L$seedRow %in% L$rowsForCor[L$cor.features],
      "the seed row is among its own correlation features (S1:112-115)")
sizes <- 4:40
fin <- vapply(sizes, function(k) {
  JJ <- seq(1, by = 2, length.out = k)
  xx <- make(JJ, 2)
  is.finite(q(bind(s1$getFitnesses, xx, fa)(vec(JJ, 80))))
}, logical(1))
check("11.7", all(!fin[sizes %in% c(10:15, 27:40)]) && all(fin[sizes %in% c(4:9, 22:26)]),
      "getFitnesses is Inf (GABi scores 0) for every |J| in 10-15 and 27-40; finite for 4-9 and 22-26",
      paste("finite for |J| =", paste(sizes[fin], collapse = ",")))
# For n = 16-21 the self-test is finite, but R also returns p = 0 for a band of |rho| below 1
# (AS 89 Edgeworth series clamped at 0). Any candidate row in the band makes the fitness Inf.
two_sided <- function(n) {
  N <- n^3 - n
  S <- seq(0, N / 3, by = 2)
  p <- vapply(S, function(q) min(1, 2 * .Call(stats:::C_pRho, round(q) + 2, n, TRUE)), 1)
  data.frame(rho = 1 - 6 * S / N, p = p)
}
band <- t(vapply(16:21, function(n) { d <- two_sided(n); range(d$rho[d$p == 0]) }, numeric(2)))
set.seed(5)
repeat { # a random y whose rank correlation with 1:21 falls in the band
  y <- 1:21 + rnorm(21, 0, 3)
  ct <- cor.test(1:21, y, method = "spearman")
  if (ct$p.value == 0) break
}
check("11.8", all(band[, 2] < 1) && ct$p.value == 0,
      "n = 16-21: p = 0 for rho in a band below 1 (n = 21, the paper's |J|: 0.836-0.865)",
      sprintf("example n = 21: rho = %.3f, p = %g; bands: %s", ct$estimate, ct$p.value,
              paste(sprintf("n=%d %.3f-%.3f", 16:21, band[, 1], band[, 2]), collapse = ", ")))
JJ <- seq(1, by = 2, length.out = 24)
xt <- round(make(JJ, 2), 1) # 1-decimal values, so the seed row has ties
check("11.9", is.infinite(q(bind(s1$getFitnesses, xt, fa)(vec(JJ, 80)))) &&
        is.finite(q(bind(s1$getFitnesses, make(JJ, 2), fa)(vec(JJ, 80)))),
      "with ties (values rounded to 1 decimal), |J| = 24 is Inf too; finite without rounding")
fsel <- q(bind(si, make(seq(1, by = 2, length.out = 12), 2), fa)(seq(1, by = 2, length.out = 12)))
check("11.10", is.finite(fsel$cor.score), "featureSelection.dysregSurv floors p at 2e-16, so |J| = 12 is finite there",
      sprintf("cor.score %.1f", fsel$cor.score))

# (c) S1:115 cor.features indexes rowsForCor, but S1:123/126 use it as a position in diffRows
#     (the selection function maps it, S1:166). The outcome step then uses the wrong rows to pick J'.
J8 <- seq(1, by = 2, length.out = 8)
x8 <- make(J8, 3)
chr8 <- vec(J8, 80)
G <- q(bind(gi, x8, fa)(chr8))
right <- G$rowsForCor[G$cor.features]
gfix <- patch(s1$getFitnesses, "survFeatures <- cor.features", "survFeatures <- rowsForCor[cor.features]")
a <- q(bind(s1$getFitnesses, x8, fa)(chr8))
b <- q(bind(gfix, x8, fa)(chr8))
check("11.11", G$useCor && !setequal(G$survFeatures, right) && any(G$survFeatures %in% 1:12) && a != b,
      "correlation branch: J' is chosen from the wrong rows (includes the high/low rows 1-12)",
      sprintf("|J| = 8: %d of %d rows used are correlation features; fitness %.1f as published vs %.1f with rowsForCor[...]",
              sum(G$survFeatures %in% right), length(G$survFeatures), a, b))

# (d) BH adjustment only in the selection function (S1:163); the fitness uses raw p (S1:115).
S8 <- q(bind(si, x8, fa)(J8))
check("11.12", length(G$cor.features) > length(S8$cor.features),
      "the fitness counts more correlation features (raw p < alpha) than the selection returns (BH p < alpha)",
      sprintf("|J| = 8: %d vs %d", length(G$cor.features), length(S8$cor.features)))

# (e) J' and l match Eqs 36-40 and the p9 text: the l = min(|J|, |Y| - |J|) columns outside J with the
#     lowest |Pearson r| with the first column of J, j1, across the selected rows. Block branch, so (c)
#     does not interfere.
fb <- modifyList(fa, list(rho = 1.01))
B <- q(bind(gi, x, fb)(vec(J, 80)))
out <- setdiff(1:80, J)
rows <- B$survFeatures
r <- vapply(out, function(y) cor(x[rows, y], x[rows, J[1]]), 1)
l <- min(length(J), 80 - length(J))
check("11.13", !B$useCor && identical(B$colsForSurv, order(abs(r))[1:l]),
      "J' = the l least |r|-correlated columns of Y \\ J against j1 = first column of J (as in Eq 40)",
      sprintf("l = %d", l))

# (f) h: S1 uses -log(1 - pchisq(survdiff chisq, 1)). That is -log(2 Phi(-|z|)) with z from Eqs 31-35.
#     Eq 31 as printed, -log(2 Phi(z)), is negative or NaN when z > 0.
grp <- c(which(vec(J, 80) == 1), out[B$colsForSurv])
st <- fa$surv[grp]
lr <- paper_logrank(st[, "time"], st[, "status"], seq_along(grp) <= length(J))
lr2 <- paper_logrank(st[, "time"], st[, "status"], seq_along(grp) > length(J)) # groups swapped: z -> -z
check("11.14", abs(B$surv.score - lr[["h_two_sided"]]) < 1e-8 && abs(lr2[["h_two_sided"]] - lr[["h_two_sided"]]) < 1e-12,
      "S1's h equals the two-sided logrank -log p built from Eqs 32-35",
      sprintf("z = %.3f: h = %.4f; Eq 31 as printed gives %.4f, and %.4f for z = %.3f",
              lr[["z"]], B$surv.score, lr[["h_printed"]], lr2[["h_printed"]], lr2[["z"]]))
done()

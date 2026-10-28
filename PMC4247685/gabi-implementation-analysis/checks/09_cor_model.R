# S1 correlation model (cor.fitness, cor.selection; S1 lines 22-65) vs Eqs 17-23.
source(file.path(dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])), "common.R"))
source(file.path(ANALYSIS_DIR, "reference", "paper_models.R"))
s1 <- load_s1()
cf <- instrument(s1$cor.fitness)
vec <- function(J, m) { v <- numeric(m); v[J] <- 1; v }

# (a) Seed row: S1 takes argmax of the mean Pearson correlation with all candidate rows (S1:33);
#     Eq 20 takes argmax |cor(row, PC1 rotation)|.
set.seed(1)
d <- alg2("cor", p = 40, q = 10, zeta = 0.3)
fa <- list(consistency = 1, rho = 0.5, alpha = 0.05) # consistency 1: no all-high rows
seeds <- t(replicate(200, {
  chr <- vec(sample(20, sample(4:18, 1)), 20)
  v <- suppressWarnings(bind(cf, d$x, fa)(chr))
  c(s1 = v$cor.features[v$cor.seed], paper = paper_cor_seed(chr, d$x))
}))
dis <- mean(seeds[, "s1"] != seeds[, "paper"])
check("09.1", dis > 0, "S1 seed row differs from Eq 20's PC1 seed", sprintf("%.0f%% of 200 random J", 100 * dis))

# (b) S1:36 tests every selected row against x[cor.seed, ], but cor.seed is a position in cor.features,
#     not a row of x. They differ whenever cor.features != 1:nrow(x), i.e. when >1 rows are 'all high'
#     on J (S1:28-31) or GABi's row filter dropped rows.
fa8 <- list(consistency = 0.8, rho = 0.5, alpha = 0.05)
chrJ <- vec(d$J, 20)
fixed <- patch(s1$cor.fitness, "y = x[cor.seed, chr == 1]", "y = x[cor.features[cor.seed], chr == 1]")
set.seed(5)
repeat { # first random J on this dataset where the two rows differ
  chr <- vec(sample(20, sample(3:10, 1)), 20)
  v <- bind(cf, d$x, fa8)(chr)
  if (!is.null(v$cor.seed) && v$cor.features[v$cor.seed] != v$cor.seed) break
}
a <- bind(s1$cor.fitness, d$x, fa8)(chr)
b <- bind(fixed, d$x, fa8)(chr)
check("09.2", a != b, "with 'all-high' rows present, p-values are computed against the wrong row",
      sprintf("|J| = %d, %d all-high rows: seed row %d, tested against row %d; score %.1f (as published) vs %.1f (fixed)",
              sum(chr), length(v$features), v$cor.features[v$cor.seed], v$cor.seed, a, b))
set.seed(2)
active <- replicate(300, {
  dd <- alg2("cor")
  chr <- vec(sample(20, sample(2:18, 1)), 20)
  w <- suppressWarnings(bind(cf, dd$x, fa8)(chr))
  if (is.null(w$cor.seed)) NA else w$cor.features[w$cor.seed] != w$cor.seed
})
note("Algorithm 2 'cor' data, random J, consistency 0.8: wrong seed row in %.0f%% of evaluations",
     100 * mean(active, na.rm = TRUE))

# (c) |rho| > fitnessArgs$rho gates the rows (S1:34); the paper has no rho.
s_rho <- vapply(c(0, 0.5, 0.9), function(r) bind(s1$cor.fitness, d$x, modifyList(fa, list(rho = r)))(chrJ), 1)
check("09.3", length(unique(s_rho)) == 3, "fitness depends on rho, a parameter not in Eqs 19-23",
      paste(sprintf("rho=%s: %.1f", c(0, 0.5, 0.9), s_rho), collapse = "; "))

# (d) alpha is not used by cor.fitness (Eq 22-23 sum only rows with p < alpha); only cor.selection uses it.
s_a <- vapply(c(1e-12, 0.05, 1), function(al) bind(s1$cor.fitness, d$x, modifyList(fa, list(alpha = al)))(chrJ), 1)
n_a <- vapply(c(1e-12, 0.05, 1), function(al) length(bind(s1$cor.selection, d$x, modifyList(fa, list(alpha = al)))(d$J)), 1)
check("09.4", length(unique(s_a)) == 1 && length(unique(n_a)) > 1,
      "cor.fitness ignores alpha; cor.selection applies it",
      sprintf("fitness %.1f at alpha 1e-12, 0.05, 1; selected rows %s", s_a[1], paste(n_a, collapse = ", ")))

# (e) 'All-high' fallback (S1:28-31, 39): rows with mean > consistency on J are removed from the
#     correlation candidates and the score is max(cor score, |J| * n_high). Not in Eqs 19-23.
set.seed(3)
x <- matrix(runif(30 * 12), 30, 12)
x[23:30, 1:6] <- 0.95 # 8 rows all-high on columns 1-6, placed last so positions equal rows
chr <- vec(1:6, 12)
fa9 <- list(consistency = 0.8, rho = 0.9, alpha = 0.05)
w <- bind(cf, x, fa9)(chr)
corpart <- if (is.null(w$cor.pvals)) 0 else 6 * sum(-log(w$cor.pvals))
check("09.5", w$allhigh.score == 48 && !any(23:30 %in% w$cor.features) && w$score == max(corpart, 48),
      "8 rows all-high on 6 columns: they leave the correlation candidates and score = max(cor score, 6 * 8)",
      sprintf("cor part %.1f, block part 48, score %.1f", corpart, w$score))
# If the all-high rows come first, the misindexed seed of (b) is one of those rows, which are constant on
# J: cor.test gives NA, the fitness is NA (GABi scores it 0) and cor.selection stops with an error.
x3 <- matrix(runif(30 * 12), 30, 12)
x3[1:20, 1:6] <- 0.95 # cor.features = rows 21-30, so cor.seed (a position 1-10) points at rows 1-10
fa0 <- list(consistency = 0.8, rho = 0, alpha = 0.05)
s_na <- suppressWarnings(bind(s1$cor.fitness, x3, fa0)(chr))
err <- tryCatch({ suppressWarnings(bind(s1$cor.selection, x3, fa0)(1:6)); "no error" }, error = conditionMessage)
s_fix <- suppressWarnings(bind(fixed, x3, fa0)(chr))
check("09.6", is.na(s_na) && grepl("missing value", err) && is.finite(s_fix),
      "20 all-high rows first: fitness NA (GABi scores 0) and cor.selection errors, which would stop GABi's last step",
      sprintf("%s; with the seed index fixed: %.1f", err, s_fix))

# (f) When the fallback wins, cor.selection returns positions within diffRows (S1:50, 62), not rows of x.
x2 <- rbind(rep(0.5, 12), x) # row 1 invariant, so diffRows = 2..31; planted rows are now 24..31
sel <- suppressWarnings(bind(s1$cor.selection, x2, fa9)(1:6))
check("09.7", identical(as.integer(sel), 23:30), "with row 1 filtered out, cor.selection returns 23..30 for planted rows 24..31",
      paste("returned:", paste(range(sel), collapse = "..")))

# (g) Eq 19 as printed: 2*Phi(z) > 1 for every positive correlation, so no positively correlated row
#     passes delta (Eq 22). The two-sided form is what the text describes.
pr <- paper_cor(chrJ, d$x, 0.05, "printed")
ts <- paper_cor(chrJ, d$x, 0.05, "two-sided", floor = 2e-16)
cc <- apply(d$x[, d$J], 1, cor, y = d$x[pr$seed, d$J])
check("09.8", all(cc[pr$features] < 0) && any(cc[ts$features] > 0),
      "as printed, Eqs 19-23 select only rows negatively correlated with the seed",
      sprintf("printed: %d rows, all r < 0; two-sided: %d rows", length(pr$features), length(ts$features)))

# (h) S1 takes p from cor.test(method = "spearman"). For 10 <= n < 1290 R uses the AS 89 Edgeworth series,
#     clamped at 0, so p is 0 (then floored to 2e-16) for a band of rho and not monotone in rho. With the
#     seed in its own feature set (|r| = 1 > rho), every J gets a self-term |J| * -log(max(2e-16, p_self)).
self_term <- vapply(4:18, function(n) n * -log(max(2e-16, cor.test(1:n, 1:n, method = "spearman")$p.value)), 1)
set.seed(8)
repeat { y <- 1:16 + rnorm(16, 0, 1.5); ct <- cor.test(1:16, y, method = "spearman"); if (ct$p.value == 0) break }
row_band <- -log(max(2e-16, ct$p.value))
row_one <- -log(max(2e-16, cor.test(1:16, 1:16, method = "spearman")$p.value))
check("09.9", row_band > 3 * row_one,
      "n = 16: a row with rho < 1 can contribute 3x more than a perfectly correlated row",
      sprintf("rho = %.3f: %.1f; rho = 1: %.1f; Fisher z (Eq 19) is monotone in rho", ct$estimate, row_band, row_one))
note("seed self-term |J| * -log(max(2e-16, p_self)) for |J| = 4..18: %s", paste(round(self_term), collapse = ", "))
done()

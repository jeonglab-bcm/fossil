# Differential test: S1 fitness functions vs the reference implementation of the paper's equations
# (reference/paper_models.R) on random Algorithm 2 inputs.
source(file.path(dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])), "common.R"))
source(file.path(ANALYSIS_DIR, "reference", "paper_models.R"))
s1 <- load_s1()
vec <- function(J, m) { v <- numeric(m); v[J] <- 1; v }
q <- function(expr) suppressWarnings(expr)

# Block, Eqs 14-16: identical apart from >= vs > (no ties on continuous data).
set.seed(1)
blk <- replicate(200, {
  d <- alg2("block")
  chr <- vec(sample(20, sample(2:18, 1)), 20)
  bind(s1$block.fitness, d$x, list(consistency = 0.7))(chr) == paper_block(chr, d$x, 0.7)$score
})
check("12.1", all(blk), "block: S1 == Eqs 14-16 on 200 random inputs")

# High variance, Eqs 24-29 with the upper tail: identical up to the 2e-16 floor.
set.seed(2)
hv <- t(replicate(200, {
  d <- alg2("highvar")
  chr <- vec(sample(20, sample(2:18, 1)), 20)
  a <- bind(s1$highvar.fitness, d$x, list(alpha = 0.05))(chr)
  b <- paper_highvar(chr, d$x, 0.05, "upper", floor = 2e-16)$score
  pr <- paper_highvar(chr, d$x, 0.05, "printed")$score
  # the same, but with S1's 1 - pchisq() instead of pchisq(lower.tail = FALSE)
  J <- which(chr == 1)
  p1 <- pmax(2e-16, 1 - pchisq(apply(d$x, 1, function(y) var(y[J]) / var(y[-J])), length(J) - 1))
  b1 <- -length(J) * sum(log(p1[p1 < 0.05]))
  c(rel = if (b == 0) abs(a) else abs(a - b) / b, rel1 = if (b1 == 0) abs(a) else abs(a - b1) / b1,
    printed_differs = a != pr)
}))
check("12.2", max(hv[, "rel1"]) < 1e-12 && max(hv[, "rel"]) < 1e-3,
      "highvar: S1 == Eqs 24-29 with the upper tail 1 - F_chi2 (200 inputs)",
      sprintf("max rel. diff %.0e computed as 1 - pchisq, %.0e with pchisq(lower.tail = FALSE); printed CDF form differs in %.0f%%",
              max(hv[, "rel1"]), max(hv[, "rel"]), 100 * mean(hv[, "printed_differs"])))

# Correlation, Eqs 17-23 (two-sided form, p floored at 2e-16 like S1) vs S1 cor.fitness / cor.selection.
cor_compare <- function(consistency, ndata = 25, nrand = 20, seed = 3) {
  set.seed(seed)
  fa <- list(consistency = consistency, rho = 0.5, alpha = 0.05)
  res <- lapply(seq_len(ndata), function(i) {
    d <- alg2("cor")
    sets <- c(list(d$J), replicate(nrand, sort(sample(20, length(d$J))), simplify = FALSE))
    one <- t(vapply(sets, function(J) {
      chr <- vec(J, 20)
      v <- q(bind(instrument(s1$cor.fitness), d$x, fa)(chr))
      p <- paper_cor(chr, d$x, 0.05, "two-sided", floor = 2e-16)
      fs <- q(bind(s1$cor.selection, d$x, fa)(J))
      s1seed <- if (is.null(v$cor.seed)) NA else v$cor.features[v$cor.seed]
      c(s1 = ifelse(is.na(v$score), 0, v$score), paper = p$score,
        seed_same = identical(unname(s1seed), unname(p$seed)),
        fallback = v$allhigh.score > 0 && v$score == v$allhigh.score,
        jac = length(intersect(fs, p$features)) / max(1, length(union(fs, p$features))),
        s1_recall_I = mean(d$I %in% fs), paper_recall_I = mean(d$I %in% p$features))
    }, numeric(7)))
    c(rank_cor = suppressWarnings(cor(one[, "s1"], one[, "paper"], method = "spearman")),
      s1_true_top = unname(one[1, "s1"] >= max(one[-1, "s1"])),
      paper_true_top = unname(one[1, "paper"] >= max(one[-1, "paper"])),
      colMeans(one[, c("seed_same", "fallback", "jac")]),
      one[1, c("s1_recall_I", "paper_recall_I")], ratio = unname(one[1, "s1"] / one[1, "paper"]))
  })
  do.call(rbind, res)
}
for (cons in c(1, 0.8)) {
  r <- cor_compare(cons)
  note("cor, consistency %s (25 datasets x 21 J): seed same %.0f%%; S1 score from block fallback %.0f%%; feature Jaccard %.2f; Spearman(S1, paper) over J median %.2f; true J ranks first: S1 %.0f%%, paper %.0f%%; recall of I at true J: S1 %.2f, paper %.2f; S1/paper score at true J median %.2f",
       cons, 100 * mean(r[, "seed_same"]), 100 * mean(r[, "fallback"]), mean(r[, "jac"]),
       median(r[, "rank_cor"], na.rm = TRUE), 100 * mean(r[, "s1_true_top"]), 100 * mean(r[, "paper_true_top"]),
       mean(r[, "s1_recall_I"]), mean(r[, "paper_recall_I"]), median(r[, "ratio"], na.rm = TRUE))
  check(sprintf("12.%d", if (cons == 1) 3 else 4), mean(r[, "seed_same"]) < 0.5 && mean(r[, "jac"]) < 0.9,
        sprintf("cor (consistency %s): S1 and Eqs 17-23 disagree on seed and selected rows", cons),
        sprintf("seed same %.0f%%, Jaccard %.2f", 100 * mean(r[, "seed_same"]), mean(r[, "jac"])))
}
done()

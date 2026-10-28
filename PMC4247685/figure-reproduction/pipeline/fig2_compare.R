# Fig. 2 comparison: our box statistics (as ggplot2 draws them) next to the ones read from the
# published figure, and the paper's paired Wilcoxon tests of the matched GABi model against every
# other method (p. 11: all p < 0.01 except Bimax on block structure, p = 0.1).
# Usage: Rscript fig2_compare.R <fig2_scores.csv> <fig2_published_boxes.json> <out .csv> <out .json>
suppressMessages(library(jsonlite))
a <- commandArgs(trailingOnly = TRUE)
d <- read.csv(a[1]); pub <- fromJSON(a[2])$boxes
methods <- c("GABi.block", "GABi.cor", "GABi.highvar", "ISA", "CC", "Plaid", "Bimax")
structures <- c("block", "cor", "highvar")

boxstats <- function(v) {
  q <- quantile(v, c(0.25, 0.5, 0.75), names = FALSE)
  iqr <- q[3] - q[1]
  inr <- v[v >= q[1] - 1.5 * iqr & v <= q[3] + 1.5 * iqr]
  c(lower = min(inr), q1 = q[1], median = q[2], q3 = q[3], upper = max(inr))
}

rows <- list()
for (s in structures) for (m in methods) {
  b <- boxstats(d$F.score[d$structure == s & d$method == m])
  p <- pub[[s]][[m]]
  rows[[length(rows) + 1]] <- data.frame(
    structure = s, method = m,
    published_q1 = p$q1, published_median = p$median, published_q3 = p$q3,
    ours_q1 = b[["q1"]], ours_median = b[["median"]], ours_q3 = b[["q3"]],
    ours_mean = mean(d$F.score[d$structure == s & d$method == m]))
}
tab <- do.call(rbind, rows)
write.csv(tab, a[3], row.names = FALSE)

matched <- c(block = "GABi.block", cor = "GABi.cor", highvar = "GABi.highvar")
tests <- list()
for (s in structures) {
  x <- d[d$structure == s, ]
  mine <- x$F.score[x$method == matched[[s]]][order(x$dataset[x$method == matched[[s]]])]
  for (m in setdiff(methods, matched[[s]])) {
    other <- x$F.score[x$method == m][order(x$dataset[x$method == m])]
    w <- suppressWarnings(wilcox.test(mine, other, paired = TRUE, alternative = "greater"))
    tests[[length(tests) + 1]] <- list(structure = s, matched = matched[[s]], versus = m,
                                       p_greater = w$p.value)
  }
}
best <- lapply(setNames(structures, structures), function(s) {
  t <- tab[tab$structure == s, ]
  list(published = t$method[which.max(t$published_median)], ours = t$method[which.max(t$ours_median)])
})
write_json(list(highest_median = best, wilcoxon = tests,
                runtime_hours = sum(d$seconds) / 3600),
           a[4], auto_unbox = TRUE, digits = NA, pretty = TRUE)

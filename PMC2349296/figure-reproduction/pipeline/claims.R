#!/usr/bin/env Rscript
# The paper's summary statistics and correlation tests, computed from the published tables and
# from our run with the same code.
#
#   * average absolute F difference between co-occurrence and RelEx ("just 13%")
#   * average pairwise between-corpus RelEx F difference ("19%", "down ... to 11%" filtered)
#   * relative reduction in F error from co-occurrence to RelEx ("21-32%")
#   * co-occurrence beats RelEx on every filtered corpus except LLL
#   * Kendall's tau (R cor.test, exact Best-Gipps p for n = 5) of I/EP vs RelEx F ("p ~ 0.08")
#     and of the fraction of sentences without interactions vs RelEx F ("not significant")
#
# Three columns, one code path:
#   published_tables              the paper's own Tables 2 to 4. Checks that this code computes each
#                                 number the way the paper did; it says nothing about our run.
#   ours                          our run: the reproduction. Verdicts are computed from it alone.
#   ours_with_published_BioInfer  our run with BioInfer's row replaced by the paper's. A sensitivity
#                                 check: it moves toward the paper by construction, so it shows how
#                                 much BioInfer matters, not that we agree.
#
# Usage: claims.R PUBLISHED_VALUES.csv COOCCURRENCE.csv RELEX.csv TABLE3.csv OUT.csv VALUES_OUT.csv \
#          VERDICTS_OUT.csv BY_CORPUS_OUT.csv
# VALUES_OUT.csv: our F-scores and statistics in the layout of published_values.csv (for figures.R).
# VERDICTS_OUT.csv: each claim in the paper's text, its value in the three columns, and its verdict.
# BY_CORPUS_OUT.csv: per corpus, co-occurrence and RelEx F and the relative cut in F error, from the
#   paper's tables, from our run and with the paper's BioInfer row.

args <- commandArgs(trailingOnly = TRUE)
pub <- read.csv(args[1])
co <- read.csv(args[2])
rx <- read.csv(args[3])
t3 <- read.csv(args[4])
corpora <- c("AIMed", "BioInfer", "HPRD50", "IEPA", "LLL")

pick <- function(d, variant, col) d[d$variant == variant, ][match(corpora, d[d$variant == variant, ]$corpus), col]

ours <- data.frame(
  corpus = corpora,
  cooc_F = pick(co, "unfiltered", "F"), relex_F = pick(rx, "unfiltered", "F"),
  cooc_F_filt = pick(co, "filtered", "F"), relex_F_filt = pick(rx, "filtered", "F"),
  I_over_EP = pick(co, "unfiltered", "I_over_EP"),
  no_interactions = t3$no_interactions[match(corpora, t3$corpus)]
)
pub <- pub[match(corpora, pub$corpus), ]

pairwise <- function(f) mean(abs(outer(f, f, "-"))[upper.tri(diag(5))])
claims <- function(d) {
  red <- ((1 - d$cooc_F) - (1 - d$relex_F)) / (1 - d$cooc_F)
  k1 <- suppressWarnings(cor.test(d$I_over_EP, d$relex_F, method = "kendall"))
  k2 <- suppressWarnings(cor.test(d$no_interactions, d$relex_F, method = "kendall"))
  beats <- d$cooc_F_filt > d$relex_F_filt
  c(
    method_gap_pts = 100 * mean(abs(d$relex_F - d$cooc_F)),
    relex_pairwise_pts = 100 * pairwise(d$relex_F),
    relex_pairwise_filtered_pts = 100 * pairwise(d$relex_F_filt),
    cooc_pairwise_pts = 100 * pairwise(d$cooc_F),
    error_reduction_min_pct = 100 * min(red),
    error_reduction_max_pct = 100 * max(red),
    cooc_beats_relex_filtered_n = sum(beats),
    cooc_beats_relex_filtered_all_but_LLL = as.numeric(all(beats[1:4]) && !beats[5]),
    kendall_IEP_tau = unname(k1$estimate), kendall_IEP_p = k1$p.value,
    kendall_noint_tau = unname(k2$estimate), kendall_noint_p = k2$p.value
  )
}

# Sensitivity: our four corpora whose unified versions match the paper, with the paper's
# BioInfer row (the mirror's BioInfer is a later conversion; see README).
hybrid <- ours
cols <- c("cooc_F", "relex_F", "cooc_F_filt", "relex_F_filt", "I_over_EP", "no_interactions")
hybrid[2, cols] <- pub[2, cols]
res <- data.frame(statistic = names(claims(pub)), published_tables = claims(pub), ours = claims(ours),
                  ours_with_published_BioInfer = claims(hybrid))
paper <- c(method_gap_pts = 13, relex_pairwise_pts = 19, relex_pairwise_filtered_pts = 11,
           error_reduction_min_pct = 21, error_reduction_max_pct = 32,
           cooc_beats_relex_filtered_all_but_LLL = 1, kendall_IEP_p = 0.08)
res$paper_text <- paper[res$statistic]
write.csv(res, args[5], row.names = FALSE)
write.csv(ours, args[6], row.names = FALSE)
print(res[, -1], digits = 3)

# Verdicts. A yes/no claim holds when it holds. A "not significant" claim holds when p >= 0.05.
# A number holds when it rounds to the paper's printed value, is close when within 10% of it, and
# differs otherwise.
RULES <- c(yes = "holds if true",
           nonsig = "holds if p >= 0.05",
           num = "holds if it rounds to the paper's value; close if within 10% of it; else differs")
spec <- data.frame(
  claim_id = c("relex_spread_exceeds_method_gap", "cooc_beats_relex_filtered_all_but_LLL",
               "kendall_noint_p", "method_gap_pts", "relex_pairwise_filtered_pts",
               "error_reduction_min_pct", "error_reduction_max_pct", "kendall_IEP_p"),
  claim = c("RelEx varies more between corpora than between the methods",
            "Co-occurrence beats RelEx on every filtered corpus except LLL",
            "Kendall p, sentences without interactions against RelEx F",
            "Gap between the methods",
            "Between-corpus RelEx difference after filtering",
            "Smallest relative cut in F error, co-occurrence to RelEx",
            "Largest relative cut in F error",
            "Kendall p, interactions per entity pair against RelEx F"),
  paper = c("19 vs 13 points", "yes", "not significant", "13 points", "11 points", "21%", "32%", "about 0.08"),
  kind = c("yes", "yes", "nonsig", "num", "num", "num", "num", "num"),
  target = c(NA, NA, NA, 13, 11, 21, 32, 0.08),
  digits = c(NA, NA, NA, 0, 0, 0, 0, 2),
  stringsAsFactors = FALSE)

shown <- function(id, v) {
  switch(id,
    relex_spread_exceeds_method_gap = sprintf("%.1f vs %.1f points", v[["relex_pairwise_pts"]], v[["method_gap_pts"]]),
    cooc_beats_relex_filtered_all_but_LLL = if (v[[id]] == 1) "yes" else "no",
    kendall_noint_p = , kendall_IEP_p = sprintf("%.3f", v[[id]]),
    method_gap_pts = , relex_pairwise_filtered_pts = sprintf("%.1f points", v[[id]]),
    sprintf("%.1f%%", v[[id]]))
}
verdict <- function(i, v) {
  id <- spec$claim_id[i]
  x <- if (id == "relex_spread_exceeds_method_gap") as.numeric(v[["relex_pairwise_pts"]] > v[["method_gap_pts"]]) else v[[id]]
  switch(spec$kind[i],
    yes = if (x == 1) "holds" else "differs",
    nonsig = if (x >= 0.05) "holds" else "differs",
    num = {
      t <- spec$target[i]; d <- spec$digits[i]
      if (sprintf("%.*f", d, x) == sprintf("%.*f", d, t)) "holds"
      else if (abs(x - t) <= 0.1 * abs(t)) "close" else "differs"
    })
}
cols3 <- list(published_tables = claims(pub), ours = claims(ours), ours_with_published_BioInfer = claims(hybrid))
ver <- spec[, c("claim_id", "claim", "paper")]
for (nm in names(cols3)) ver[[nm]] <- vapply(ver$claim_id, shown, "", v = cols3[[nm]], USE.NAMES = FALSE)
ver$rule <- unname(RULES[spec$kind])
ver$verdict_published_tables <- vapply(seq_len(nrow(spec)), verdict, "", v = cols3$published_tables)
ver$verdict <- vapply(seq_len(nrow(spec)), verdict, "", v = cols3$ours)
write.csv(ver, args[7], row.names = FALSE)
print(ver[, c("claim_id", "ours", "verdict")])

# Per corpus: what sets the smallest and largest error cut.
reduction <- function(d) 100 * (d$relex_F - d$cooc_F) / (1 - d$cooc_F)
byc <- data.frame(
  corpus = corpora,
  corpus_version = c("12 sentences and self-interactions missing", "later conversion",
                     "the paper's", "the paper's", "the paper's"),
  cooc_F_published = pub$cooc_F, cooc_F_ours = ours$cooc_F,
  relex_F_published = pub$relex_F, relex_F_ours = ours$relex_F,
  error_reduction_pct_published = reduction(pub), error_reduction_pct_ours = reduction(ours),
  error_reduction_pct_with_published_BioInfer = reduction(hybrid))
write.csv(byc, args[8], row.names = FALSE)

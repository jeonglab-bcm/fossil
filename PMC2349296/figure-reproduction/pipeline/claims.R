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
# Usage: claims.R PUBLISHED_VALUES.csv COOCCURRENCE.csv RELEX.csv TABLE3.csv OUT.csv VALUES_OUT.csv
# VALUES_OUT.csv: our F-scores and statistics in the layout of published_values.csv (for figures.R).

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

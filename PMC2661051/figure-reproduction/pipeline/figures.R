# Figures 2, 3 and 4 of Ackermann and Strimmer (2009) from our p53 and Hedenfalk runs, drawn with
# base R graphics as the paper's were, at the published pixel sizes (Springer originals: 1200 x 571
# for Figs 2 and 4, 1200 x 960 for Fig. 3). Also writes the plotted numbers.
#
# Usage: Rscript figures.R P53.rds P53_PVALUES.csv HEDENFALK_PVALUES.csv OUTDIR
library(jsonlite)
args <- commandArgs(TRUE)
p53 <- readRDS(args[1])
pp <- read.csv(args[2], check.names = FALSE)
ph <- read.csv(args[3], check.names = FALSE)
out <- args[4]
dir.create(out, showWarnings = FALSE, recursive = TRUE)

stats <- c("mean", "median", "maxmean", "es", "wilcoxon", "condfdr", "globaltest", "hotelling")
labels <- c("mean", "median", "maxmean", "ES", "Wilcoxon", "cond. fdr", "global", "Hotelling")
letters_ <- c("m", "d", "x", "E", "w", "c", "g", "h")
cutoffs <- c(0.001, 0.005, 0.01, 0.02, 0.05, 0.1)

counts <- function(P) {
  sapply(c("resampling", "permutation"), function(me) {
    sapply(stats, function(st) sapply(cutoffs, function(cu) sum(P[[paste(st, me, sep = ".")]] <= cu)))
  }, simplify = "array")   # cutoff x stat x method
}

# Each plot region is placed on the published pixel grid: the pixel rows and columns of the
# published tick marks (found in published/Fig*.png, as read_published.py does) give the map from
# data to pixels, and par(plt) puts our user coordinates on the same map.
W2 <- 1200; H2 <- 571; W3 <- 1200; H3 <- 960
lin <- function(v, pa, va, pb, vb) pa + (v - va) * (pb - pa) / (vb - va)
region <- function(W, H, usr, xcal, ycal) {
  # usr: c(x0, x1, y0, y1); xcal/ycal: c(pixel a, value a, pixel b, value b); pixel centres
  x <- lin(usr[1:2], xcal[1], xcal[2], xcal[3], xcal[4]) + 0.5
  y <- lin(usr[3:4], ycal[1], ycal[2], ycal[3], ycal[4]) + 0.5
  par(plt = c(x[1] / W, x[2] / W, 1 - y[1] / H, 1 - y[2] / H), new = TRUE)
  plot.new()
  plot.window(usr[1:2], usr[3:4], xaxs = "i", yaxs = "i")
}
ext <- function(r) r + c(-1, 1) * 0.04 * diff(r)   # R's default 4% axis extension

draw_counts <- function(C, title, ymax_left, ycal_left, ymax_right, ycal_right) {
  par(mar = c(0, 0, 0, 0))
  plot.new()
  # left panel: x ticks 0 and 0.1 at columns 66 and 556
  region(W2, H2, c(ext(c(0, 0.1)), ext(c(0, ymax_left))), c(66, 0, 556, 0.1), ycal_left)
  for (k in seq_along(stats)) {
    lines(cutoffs, C[, k, "resampling"], col = "black")
    text(cutoffs, C[, k, "resampling"], letters_[k], col = "black", cex = 0.7)
    lines(cutoffs, C[, k, "permutation"], col = "blue")
    text(cutoffs, C[, k, "permutation"], letters_[k], col = "blue", cex = 0.7)
  }
  box()
  axis(1, cex.axis = 0.7)
  axis(2, cex.axis = 0.7)
  title(xlab = "p-value cutoff", ylab = "number of sets with p <= cutoff", cex.lab = 0.7)
  legend("topleft", legend = labels, pch = letters_, cex = 0.9)
  legend("topright", legend = c("resampling", "permutation"), lty = 1, col = c("black", "blue"), cex = 0.6)
  # right panel: barplot units (bars 1 unit wide, groups 3 units apart); the left edge of the first
  # bar (unit 1) at column 666 and groups 64 px apart
  region(W2, H2, c(ext(c(1, 24)), ext(c(0, ymax_right))), c(666 - 0.5, 1, 666 - 0.5 + 64, 4), ycal_right)
  i <- which(cutoffs == 0.01)
  mids <- barplot(t(C[i, , ]), beside = TRUE, col = c("black", "blue"), names.arg = rep("", length(labels)),
                  add = TRUE, axes = FALSE)
  axis(2, cex.axis = 0.85)
  mtext(labels, side = 1, at = colMeans(mids), line = 1, cex = 0.75)
  title(main = title)
  legend("topright", legend = c("resampling", "permutation"), fill = c("black", "blue"), cex = 0.85)
  legend("topleft", legend = "pvalue cutoff 0.01", cex = 0.6)
}

Cp <- counts(pp)
Ch <- counts(ph)
png(file.path(out, "fig2_ours.png"), width = W2, height = H2, pointsize = 16)
draw_counts(Cp, "p53 Data", 300, c(495, 0, 49, 300), 250, c(512, 0, 111, 250))
invisible(dev.off())
png(file.path(out, "fig4_ours.png"), width = W2, height = H2, pointsize = 16)
draw_counts(Ch, "Hedenfalk Data", 80, c(495, 0, 111, 80), 80, c(512, 0, 98, 80))
invisible(dev.off())

# Fig. 3: mean pairwise (absolute) correlation within each p53 gene set, over all 50 cell lines
X <- p53$X
mc <- t(sapply(p53$sets, function(g) {
  C <- cor(t(X[g, ]))
  u <- C[upper.tri(C)]
  c(mean = mean(u), mean_abs = mean(abs(u)))
}))
br_top <- seq(-0.01, 0.30, 0.01)
br_bot <- seq(0.125, 0.325, 0.005)
h_top <- table(cut(mc[, "mean"], br_top, right = FALSE))
h_bot <- table(cut(mc[, "mean_abs"], br_bot, right = FALSE))
# Plot breaks: the published bin widths, extended where our values fall outside the published range.
span <- function(x, br, w) seq(min(br[1], floor(min(x) / w) * w), max(br[length(br)], ceiling(max(x) / w) * w), w)
png(file.path(out, "fig3_ours.png"), width = W3, height = H3, pointsize = 16)
par(mar = c(0, 0, 0, 0))
plot.new()
xcal <- c(165.5, 0, 1041.5, 0.30)
region(W3, H3, c(-0.04, 0.34, -3, 63), xcal, c(347.5, 0, 99, 60))
hist(mc[, "mean"], breaks = span(mc[, "mean"], br_top, 0.01), right = FALSE, add = TRUE)
axis(1, at = seq(0, 0.3, 0.05)); axis(2)
title(xlab = "mean pairwise correlation in set", ylab = "Frequency")
region(W3, H3, c(-0.04, 0.34, -2, 42), xcal, c(827.5, 0, 599, 40))
hist(mc[, "mean_abs"], breaks = span(mc[, "mean_abs"], br_bot, 0.005), right = FALSE, add = TRUE)
axis(1, at = seq(0, 0.3, 0.05)); axis(2)
title(xlab = "mean pairwise absolute correlation in set", ylab = "Frequency")
invisible(dev.off())

as_list <- function(C) {
  lapply(setNames(c("resampling", "permutation"), c("resampling", "permutation")), function(me)
    setNames(lapply(seq_along(stats), function(k) setNames(as.list(C[, k, me]), as.character(cutoffs))), stats))
}
write_json(list(cutoffs = cutoffs,
                fig2 = as_list(Cp), fig4 = as_list(Ch),
                fig3 = list(mean_correlation = list(breaks = br_top, counts = as.integer(h_top),
                                                    outside = sum(is.na(cut(mc[, "mean"], br_top, right = FALSE)))),
                            mean_abs_correlation = list(breaks = br_bot, counts = as.integer(h_bot),
                                                        outside = sum(is.na(cut(mc[, "mean_abs"], br_bot, right = FALSE)))),
                            median_mean = median(mc[, "mean"]), median_mean_abs = median(mc[, "mean_abs"]),
                            max_mean = max(mc[, "mean"]), sets = nrow(mc))),
           file.path(out, "figures.json"), auto_unbox = TRUE, pretty = TRUE, digits = NA)

# Variants of Fig. 3 that test why our histograms differ from the published ones: other scales,
# Spearman correlation, and correlation within the two classes.
cent <- function(Z, y) {
  Z[, y == 1] <- Z[, y == 1] - rowMeans(Z[, y == 1])
  Z[, y == 0] <- Z[, y == 0] - rowMeans(Z[, y == 0])
  Z
}
variants <- list(
  raw_scale = function(g) cor(t(2^X[g, ])),
  spearman = function(g) cor(t(X[g, ]), method = "spearman"),
  within_class = function(g) cor(t(cent(X[g, ], p53$y)))
)
vres <- lapply(variants, function(f) {
  m <- t(sapply(p53$sets, function(g) { C <- f(g); u <- C[upper.tri(C)]; c(mean(u), mean(abs(u))) }))
  list(mean_correlation = as.integer(table(cut(m[, 1], br_top, right = FALSE))),
       mean_abs_correlation = as.integer(table(cut(m[, 2], br_bot, right = FALSE))),
       median_mean = median(m[, 1]), median_mean_abs = median(m[, 2]))
})
write_json(vres, file.path(out, "fig3_variants.json"), auto_unbox = TRUE, pretty = TRUE, digits = NA)

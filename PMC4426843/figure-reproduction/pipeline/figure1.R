#!/usr/bin/env Rscript
# Figure 1 of Bleazard et al. 2015 with base R graphics, as published: two histograms
# (plot.histogram) of the probability per 5-gene bin, right-closed bins seq(165, 295, 5),
# x limits 150-300, legend at the top right.
#
# Usage: figure1.R HIST.tsv PARAMS.R OUT_PREFIX
#   HIST.tsv: k, draws (null distribution of target genes in GO:0006811 for 39 random miRNAs)
#   PARAMS.R: presentation parameters fitted to the published image (params/figure1_params.R)
# The hypergeometric distribution is exact: N = 15733 genes, K = 327 in the term, n = 10057
# targets (Section 3.1). Writes OUT_PREFIX.png and OUT_PREFIX.pdf on a canvas that contains the
# published frame at (0, fp$pad_top), size fp$crop; compare_figure1.py crops it.

args <- commandArgs(trailingOnly = TRUE)
emp <- read.delim(args[1])
source(args[2])  # defines `fp`
out <- args[3]

N <- 15733; K <- 327; n <- 10057
breaks <- seq(165, 295, 5)

as_hist <- function(k, w) {
  # plot.histogram with probabilities per bin in `counts`; right-closed bins as hist() makes.
  bin <- findInterval(k, breaks, left.open = TRUE, rightmost.closed = FALSE)
  keep <- bin >= 1 & bin < length(breaks)
  p <- tapply(w[keep], factor(bin[keep], levels = seq_len(length(breaks) - 1)), sum)
  p[is.na(p)] <- 0
  structure(list(breaks = breaks, counts = as.numeric(p) / sum(w),
                 density = as.numeric(p) / sum(w) / 5, mids = breaks[-1] - 2.5,
                 xname = "x", equidist = TRUE), class = "histogram")
}
k <- 0:K
h_hyp <- as_hist(k, dhyper(k, K, N - K, n))
h_emp <- as_hist(emp$k, emp$draws)
ymax <- max(h_hyp$counts)

draw <- function() {
  # Plot region on the published pixel grid: x = 150..300 at fp$x150..fp$x300 px and
  # y = 0..0.20 at fp$y0..fp$y020 px. R extends the axes by 4%.
  ux <- (fp$x300 - fp$x150) / 150
  uy <- (fp$y0 - fp$y020) / 0.20
  # The published image is cropped on the top and right; the device adds fp$pad_top px above it.
  left <- fp$x150 - 6 * ux; right <- fp$x300 + 6 * ux
  bottom <- fp$pad_top + fp$y0 + 0.04 * ymax * uy; top <- fp$pad_top + fp$y0 - 1.04 * ymax * uy
  par(plt = c(left / fp$width, right / fp$width, 1 - bottom / fp$height, 1 - top / fp$height),
      mgp = fp$mgp, xpd = NA)
  plot(h_hyp, freq = TRUE, col = fp$col_hyp, border = "black", xlim = c(150, 300),
       ylim = c(0, ymax), main = "", xlab = "", ylab = "", axes = FALSE)
  plot(h_emp, freq = TRUE, col = fp$col_emp, border = "black", add = TRUE)
  axis(1, at = seq(150, 300, 50))
  axis(2, at = seq(0, 0.20, 0.05), labels = sprintf("%.2f", seq(0, 0.20, 0.05)))
  title(xlab = "Number of predicted targets in GO term", line = fp$xlab_line)
  mtext("Probability", side = 2, line = fp$ylab_line, padj = 0,
        at = grconvertY(fp$pad_top + fp$ylab_px, "device", "user"))
  lx <- grconvertX(fp$legend_px[1], "device", "user")
  ly <- grconvertY(fp$pad_top + fp$legend_px[2], "device", "user")
  legend(lx, ly, legend = c("Hypergeometric", "Empirical"), fill = c(fp$col_hyp, fp$col_emp),
         bty = "n", x.intersp = fp$legend_xi, y.intersp = fp$legend_yi, cex = fp$legend_cex)
}

png(paste0(out, ".png"), width = fp$width, height = fp$height, pointsize = 12,
    res = fp$res, type = "cairo", antialias = "gray", family = fp$family)
draw()
invisible(dev.off())
cairo_pdf(paste0(out, ".pdf"), width = fp$width / fp$res, height = fp$height / fp$res,
          family = fp$family, pointsize = 12)
draw()
invisible(dev.off())
write.csv(data.frame(bin_lo = head(breaks, -1), bin_hi = breaks[-1],
                     hypergeometric = h_hyp$counts, empirical = h_emp$counts),
          paste0(out, "_bins.csv"), row.names = FALSE)

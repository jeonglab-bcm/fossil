#!/usr/bin/env Rscript
# Draw Figures 1 and 2 of Pyysalo et al. 2008 with base R graphics, as the paper did
# (Helvetica-like sans text, pch 16/17 points, type "b" lines, separate axes, boxed legend).
#
# Usage: figures.R VALUES.csv PARAMS.R OUT_PREFIX
#   VALUES.csv: corpus, cooc_F, relex_F, cooc_F_filt, relex_F_filt (fractions)
#   PARAMS.R:   presentation parameters fitted to the published images (params/figure_params.R)
# Writes OUT_PREFIX-figure-1.png/.pdf and OUT_PREFIX-figure-2.png/.pdf.

args <- commandArgs(trailingOnly = TRUE)
vals <- read.csv(args[1], stringsAsFactors = FALSE)
source(args[2])  # defines `fp`, a list with one entry per figure
out <- args[3]

corpora <- c("AIMed", "BioInfer", "HPRD50", "IEPA", "LLL")
vals <- vals[match(corpora, vals$corpus), ]

# Plot region in device pixels from the axis calibration (see params): x = 1..5 at x1..x5 px,
# y = 0..100 at y0..y100 px; R extends both axes by 4%.
plt_from_calibration <- function(p) {
  ux <- (p$x5 - p$x1) / 4            # px per x unit
  uy <- (p$y0 - p$y100) / 100        # px per y unit
  left <- p$x1 - 0.16 * ux
  right <- p$x5 + 0.16 * ux
  top <- p$y100 - 4 * uy
  bottom <- p$y0 + 4 * uy
  c(left / p$width, right / p$width, 1 - bottom / p$height, 1 - top / p$height)
}

draw <- function(fig, p, series, legend_rows) {
  par(plt = plt_from_calibration(p), mgp = p$mgp, las = 0, xpd = NA)
  plot(1:5, series[[1]]$y, type = "n", axes = FALSE, xlab = "", ylab = "%",
       ylim = c(0, 100), xlim = c(1, 5))
  for (s in series) {
    lines(1:5, s$y, type = "b", pch = s$pch, col = s$col, lwd = 1, cex = p$cex_pt)
  }
  axis(1, at = 1:5, labels = corpora, cex.axis = 1)
  axis(2, at = seq(0, 100, 20))
  lx <- grconvertX(p$legend_px[1], "device", "user")
  ly <- grconvertY(p$legend_px[2], "device", "user")
  legend(lx, ly, legend = legend_rows$label, pch = legend_rows$pch, col = legend_rows$col,
         bty = "o", inset = 0, x.intersp = p$legend_xi, y.intersp = p$legend_yi, pt.cex = p$cex_pt)
}

render <- function(fig, series, legend_rows) {
  p <- fp$fig[[fig]]
  png(sprintf("%s-figure-%d.png", out, fig), width = p$width, height = p$height,
      pointsize = p$pointsize, res = 72, type = "cairo", antialias = "gray", family = "sans")
  draw(fig, p, series, legend_rows)
  invisible(dev.off())
  cairo_pdf(sprintf("%s-figure-%d.pdf", out, fig), width = p$width / 72, height = p$height / 72,
      pointsize = p$pointsize)
  draw(fig, p, series, legend_rows)
  invisible(dev.off())
}

blk <- "black"
grey <- fp$grey
render(1,
       list(list(y = 100 * vals$relex_F, pch = 16, col = blk),
            list(y = 100 * vals$cooc_F, pch = 17, col = blk)),
       data.frame(label = c("RelEx", "Co−occurrence"), pch = c(16, 17), col = blk))
render(2,
       list(list(y = 100 * vals$relex_F, pch = 1, col = grey),
            list(y = 100 * vals$cooc_F, pch = 2, col = grey),
            list(y = 100 * vals$relex_F_filt, pch = 16, col = blk),
            list(y = 100 * vals$cooc_F_filt, pch = 17, col = blk)),
       data.frame(label = c("RelEx (filt.)", "Co−occurrence (filt.)", "RelEx", "Co−occurrence"),
                  pch = c(16, 17, 1, 2), col = c(blk, blk, grey, grey)))

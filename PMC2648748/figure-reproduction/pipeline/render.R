# Draw our Figs 2 and 3 the way the paper drew them (base R barplot and notched boxplot), on the
# published 2400 x 1200 pixel grid, and the negative-control variants used to test the pixel score.
#
# usage: Rscript render.R SUMMARY_JSON OUTDIR
#
# The published figures are 2400 x 1200 images of a 2 x 3 layout of base-R panels. We draw at
# 12 x 6 in and 200 px per inch, and take the margins (in inches) from the published frames
# (read_published.py): frame left/right/top/bottom at 179.5/739.5/89.5/509.5 px within each
# 800 x 600 px panel region. Text sizes and offsets were matched to the published glyphs.
suppressPackageStartupMessages(library(jsonlite))
args <- commandArgs(trailingOnly = TRUE)
summ <- fromJSON(args[1], simplifyVector = FALSE)
outdir <- args[2]
dir.create(outdir, showWarnings = FALSE, recursive = TRUE)

FAMILY <- "Liberation Sans"   # metric-compatible with Helvetica, the published font
RES <- 200
MAI <- c(600 - 509.5, 179.5, 89.5, 800 - 739.5) / RES   # bottom, left, top, right (in)
FILLS <- grey(c(0.4, 0.6, 0.8, 0.98))                  # epiForest, BEAM, LR, chi-squared
METHODS <- c("epiForest", "BEAM", "Logistic regression", "Chi-squared test")
MAF_LABELS <- c("0.05", "0.10", "0.20", "0.50")
P <- list(cex_axis = 1.45, cex_names = 1.9, cex_main = 1.95, cex_lab = 1.87, cex_leg = 2.15,
          mgp_y = c(4.6, 1.6, 0), ylab_line = 4.3, tcl = -0.75, line_names = 1.88, maf_at = -0.38,
          maf_at3 = 0.69, leg_extra = 0.6,
          leg_inset = c(0.05, 0.07))

open_png <- function(path) {
  png(path, width = 2400, height = 1200, res = RES, type = "cairo", family = FAMILY, bg = "white")
  par(mfrow = c(2, 3), mai = MAI, family = FAMILY, lwd = 1.08)
}

ylab_r2 <- function(r2) bquote("Power ( " * r^2 * "= " * .(sprintf("%.1f", r2)) * " )")

# power: list over panels (row-major: r2 = 0.7 models 1-3, then r2 = 1.0), each a 4 x 4 matrix
# [method, MAF] in percent; NA bars (methods we did not run) are left out.
draw_fig2 <- function(path, power) {
  open_png(path)
  for (p in 1:6) {
    r2 <- if (p <= 3) 0.7 else 1.0
    m <- power[[p]]
    h <- m
    h[is.na(h)] <- 0
    bp <- barplot(h, beside = TRUE, space = c(0, 1), col = FILLS, ylim = c(0, 110),
                  yaxs = "i", axes = FALSE, names.arg = rep("", 4), border = NA, plot = TRUE)
    # draw the bars we have (outlines too); missing methods leave a gap
    for (j in 1:4) for (i in 1:4) if (!is.na(m[i, j]))
      rect(bp[i, j] - 0.5, 0, bp[i, j] + 0.5, m[i, j], col = FILLS[i], border = "black")
    axis(2, at = seq(0, 100, 20), cex.axis = P$cex_axis, mgp = P$mgp_y, tcl = P$tcl)
    mtext(MAF_LABELS, side = 1, at = colMeans(bp), line = P$line_names, cex = P$cex_names * 0.66)
    if ((p - 1) %% 3 == 0) {
      mtext("MAF", side = 1, at = P$maf_at, line = P$line_names, cex = P$cex_names * 0.66)
      mtext(ylab_r2(r2), side = 2, line = P$ylab_line, cex = P$cex_lab * 0.66)
    }
    if (p <= 3) title(main = paste("Model", p), cex.main = P$cex_main)
    box()
    if (p == 1) legend("topright", METHODS, fill = FILLS, cex = P$cex_leg * 0.66,
                       inset = P$leg_inset, bg = "white", y.intersp = 1.0, x.intersp = 1.25,
                       text.width = max(strwidth(METHODS, cex = P$cex_leg * 0.66)) + P$leg_extra)
  }
  invisible(dev.off())
}

# counts: list over panels, each a list of 4 integer vectors (number of SNPs selected per data set)
draw_fig3 <- function(path, counts) {
  open_png(path)
  for (p in 1:6) {
    r2 <- if (p <= 3) 0.7 else 1.0
    cp <- counts[[p]]
    if (all(lengths(cp) == 0)) {
      plot(NA, xlim = c(0.5, 4.5), ylim = c(0, 80), axes = FALSE, xlab = "", ylab = "")
    } else {
      cp <- lapply(cp, function(v) if (length(v)) v else NA_real_)
      boxplot(cp, notch = TRUE, ylim = c(0, 80), axes = FALSE, outcex = 1.1, outlwd = 1.5)
    }
    axis(2, at = seq(0, 80, 20), cex.axis = P$cex_axis, mgp = P$mgp_y, tcl = P$tcl)
    mtext(MAF_LABELS, side = 1, at = 1:4, line = P$line_names, cex = P$cex_names * 0.66)
    if ((p - 1) %% 3 == 0) {
      mtext("MAF", side = 1, at = P$maf_at3, line = P$line_names, cex = P$cex_names * 0.66, adj = 1)
      mtext(bquote("#{Selected SNPs} ( " * r^2 * "= " * .(sprintf("%.1f", r2)) * " )"), side = 2,
            line = P$ylab_line, cex = P$cex_lab * 0.66)
    }
    if (p <= 3) title(main = paste("Model", p), cex.main = P$cex_main)
    box()
  }
  invisible(dev.off())
}

panels <- function(key) lapply(summ$panels, function(pn) pn[[key]])
as_power <- function(lst) lapply(lst, function(x) {
  if (is.null(x)) return(matrix(NA_real_, 4, 4))
  matrix(unlist(lapply(x, function(row) lapply(row, function(v) if (is.null(v)) NA_real_ else v))), 4, 4, byrow = TRUE)
})
as_counts <- function(lst) lapply(lst, function(x) lapply(x, function(v) unlist(v)))

power <- as_power(panels("power"))
counts <- as_counts(panels("selected"))
draw_fig2(file.path(outdir, "fig2_ours.png"), power)
draw_fig3(file.path(outdir, "fig3_ours.png"), counts)

# negative controls: the same drawing with known-wrong inputs
shift_power <- function(pw, d) lapply(pw, function(m) pmin(pmax(m + d, 0), 100))
rot <- c(2, 3, 1, 5, 6, 4)   # each panel gets the next model's values (same r2)
ctrl <- file.path(outdir, "controls")
dir.create(ctrl, showWarnings = FALSE)
draw_fig2(file.path(ctrl, "fig2_wrong_model.png"), power[rot])
draw_fig2(file.path(ctrl, "fig2_wrong_r2.png"), power[c(4, 5, 6, 1, 2, 3)])
draw_fig2(file.path(ctrl, "fig2_plus5.png"), shift_power(power, 5))
draw_fig2(file.path(ctrl, "fig2_minus5.png"), shift_power(power, -5))
draw_fig3(file.path(ctrl, "fig3_wrong_model.png"), counts[rot])
draw_fig3(file.path(ctrl, "fig3_plus2.png"), lapply(counts, function(pn) lapply(pn, function(v) v + 2)))
draw_fig3(file.path(ctrl, "fig3_minus2.png"), lapply(counts, function(pn) lapply(pn, function(v) v - 2)))

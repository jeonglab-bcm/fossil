# Redraw Figs 1-3 of Nemes et al. (2009) on the published pixel grid, and the negative controls.
#   Rscript figures.R CALIB_CSV PER_N_CSV SAMPLES_CSV OUTDIR [HYP_PER_N_CSV HYP_SAMPLES_CSV]
# Each panel's plot region is put on the published panel box, with the axis limits fitted to the
# published tick marks (calibrate.py), so a value lands on the pixel where the paper drew it.
# Writes OUTDIR/fig1_ours.png, fig2_ours.png, fig3_ours.png, and OUTDIR/controls/<fig>_<name>.png.
# Hypothesis renders (scored by compare.py, never as agreement) go to OUTDIR/hypotheses/:
# fig1_population.png, our series moved by the difference between Table 1's intercepts and ours
# (the population draw); and, given a second run, fig*_xsd1.png from it (x with SD 1).
# Text (titles, labels) is drawn for the reader only; compare.py scores the ink inside the boxes.
suppressPackageStartupMessages(library(logitbias))
a <- commandArgs(TRUE)
cal <- read.csv(a[1])
s <- read.csv(a[2])
smp <- read.csv(a[3])
out <- a[4]
dir.create(file.path(out, "controls"), showWarnings = FALSE, recursive = TRUE)
dir.create(file.path(out, "hypotheses"), showWarnings = FALSE, recursive = TRUE)
font <- "Liberation Sans"

dev_open <- function(file, id) {
  r <- cal[cal$id == id, ]
  png(file, width = r$W, height = r$H, type = "cairo", family = font, res = 72, pointsize = 12,
      bg = "white")
  plot.new()
}
panel <- function(id) {
  r <- cal[cal$id == id, ]
  par(fig = c(0, 1, 0, 1), new = TRUE, xaxs = "i", yaxs = "i",
      plt = c((r$x0 + 0.5) / r$W, (r$x1 + 0.5) / r$W, 1 - (r$y1 + 0.5) / r$H, 1 - (r$y0 + 0.5) / r$H))
  list(xlim = c(r$xusr0, r$xusr1), ylim = c(r$yusr0, r$yusr1))
}

# ---- Fig. 1: mean coefficient per sample size and the fitted curve beta + b1/n --------------
curve_fit <- fit_bias_curve(s, "means")
coef_of <- function(tm, prm) curve_fit$estimate[curve_fit$term == tm & curve_fit$param == prm]
paper_b0 <- c(x = 2.011, z = -0.898)  # Table 1 intercepts, for the population-draw hypothesis
fig1_series <- function(variant = "ours") {
  lapply(c(x = "x", z = "z"), function(tm) {
    d <- s[s$term == tm, ]
    b0 <- coef_of(tm, "intercept"); b1 <- coef_of(tm, "inv_n")
    m <- d$mean
    lim <- cal[cal$id == if (tm == "x") "fig1.continuous" else "fig1.discrete", ]
    span <- lim$yusr1 - lim$yusr0
    m <- switch(variant,
      ours = m,
      no_bias = m - b1 / d$n,
      every_fit_kept = d$mean_all,
      warning_rule = d$mean_warning,
      bias_x1.1 = m + 0.1 * b1 / d$n,
      bias_x0.9 = m - 0.1 * b1 / d$n,
      shift_up = m + 0.01 * span,
      shift_down = m - 0.01 * span,
      population = m + paper_b0[[tm]] - b0)
    k <- switch(variant, no_bias = 0, bias_x1.1 = 1.1, bias_x0.9 = 0.9, 1)
    sh <- switch(variant, shift_up = 0.01 * span, shift_down = -0.01 * span,
                 population = paper_b0[[tm]] - b0, 0)
    if (variant %in% c("every_fit_kept", "warning_rule")) {
      d2 <- d; d2$mean <- m
      f2 <- fit_bias_curve(d2, "means")
      cv <- f2$estimate[1] + f2$estimate[2] / d$n
    } else {
      cv <- b0 + k * b1 / d$n + sh
    }
    list(n = d$n, m = m, curve = cv)
  })
}
fig1 <- function(file, ser) {
  dev_open(file, "fig1.continuous")
  for (tm in c("x", "z")) {
    id <- if (tm == "x") "fig1.continuous" else "fig1.discrete"
    p <- panel(id)
    plot(ser[[tm]]$n, ser[[tm]]$m, xlim = p$xlim, ylim = p$ylim, cex = 0.8,
         main = if (tm == "x") "Continuous variable" else "Discrete variable",
         xlab = "Sample Size", ylab = if (tm == "x") "Log Odds Ratio" else "",
         cex.main = 1.6, cex.lab = 1.75, cex.axis = 1.35)
    lines(ser[[tm]]$n, ser[[tm]]$curve, lwd = 2)
  }
  invisible(dev.off())
}
fig1(file.path(out, "fig1_ours.png"), fig1_series("ours"))
for (v in c("no_bias", "every_fit_kept", "warning_rule", "bias_x1.1", "bias_x0.9", "shift_up", "shift_down")) {
  fig1(file.path(out, "controls", paste0("fig1_", v, ".png")), fig1_series(v))
}

# ---- Fig. 2: density of the continuous coefficient at six sample sizes ---------------------
sizes <- c(100, 150, 300, 500, 750, 1000)
neighbour <- c(`100` = 150, `150` = 100, `300` = 500, `500` = 300, `750` = 1000, `1000` = 750)
est_at <- function(n) { v <- smp[smp$n == n & smp$status == "ok", "x"]; v }
fig2 <- function(file, variant = "ours") {
  dev_open(file, "fig2.n100")
  for (k in seq_along(sizes)) {
    n <- sizes[k]
    id <- paste0("fig2.n", n)
    p <- panel(id)
    v <- if (variant == "neighbour_n") est_at(neighbour[[as.character(n)]]) else est_at(n)
    bwadj <- switch(variant, bw_x1.25 = 1.25, bw_x0.8 = 0.8, 1)
    d <- density(v, adjust = bwadj)
    span <- diff(p$xlim)
    if (variant == "shift_right") d$x <- d$x + 0.01 * span
    if (variant == "shift_left") d$x <- d$x - 0.01 * span
    plot(d, xlim = p$xlim, ylim = p$ylim, main = bquote(beta * "= " * .(as.character(round(mean(est_at(n)), 3)))),
         xlab = paste0("n=", n), ylab = if (k %in% c(1, 4)) "Density" else "",
         cex.main = 1.05, font.main = 1, cex.lab = 1.0, cex.axis = 1.0)
    abline(v = 2)
  }
  invisible(dev.off())
}
fig2(file.path(out, "fig2_ours.png"))
for (v in c("neighbour_n", "bw_x1.25", "bw_x0.8", "shift_right", "shift_left")) {
  fig2(file.path(out, "controls", paste0("fig2_", v, ".png")), v)
}

# ---- Fig. 3: box plots of the continuous coefficient at the six sample sizes ----------------
fig3 <- function(file, variant = "ours") {
  dev_open(file, "fig3")
  p <- panel("fig3")
  span <- diff(p$ylim)
  vals <- lapply(sizes, function(n) {
    v <- if (variant == "neighbour_n") est_at(neighbour[[as.character(n)]]) else est_at(n)
    if (variant == "shift_up") v <- v + 0.01 * span
    if (variant == "shift_down") v <- v - 0.01 * span
    if (variant == "spread_x0.9") v <- median(v) + 0.9 * (v - median(v))
    if (variant == "spread_x1.1") v <- median(v) + 1.1 * (v - median(v))
    v
  })
  names(vals) <- paste0("n=", sizes)
  boxplot(vals, xlim = p$xlim, ylim = p$ylim, main = "Study Size and Bias when Modelling Odds Ratio",
          ylab = "Log Odds Ratio", cex.main = 1.3, cex.lab = 1.35, cex.axis = 1.35, las = 1,
          col = "white", lwd = 1, medlwd = 3)
  abline(h = 2)
  invisible(dev.off())
}
fig3(file.path(out, "fig3_ours.png"))
for (v in c("neighbour_n", "shift_up", "shift_down", "spread_x0.9", "spread_x1.1")) {
  fig3(file.path(out, "controls", paste0("fig3_", v, ".png")), v)
}
fig1(file.path(out, "hypotheses", "fig1_population.png"), fig1_series("population"))
if (length(a) >= 6) {
  s <- read.csv(a[5])
  smp <- read.csv(a[6])
  curve_fit <- fit_bias_curve(s, "means")
  fig1(file.path(out, "hypotheses", "fig1_xsd1.png"), fig1_series("ours"))
  fig2(file.path(out, "hypotheses", "fig2_xsd1.png"))
  fig3(file.path(out, "hypotheses", "fig3_xsd1.png"))
}
cat("figures written\n")

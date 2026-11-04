# Presentation parameters for Figures 1 and 2 (written by fit_figures.py).
# MEASURED from the published images (pixels): size, axis ticks (x = 1..5 -> x1..x5,
# y = 0 and 100 -> y0, y100), legend box top-left corner, series grey (Fig. 2 mode 189 =
# R "gray", 190). FITTED (not data): pointsize, mgp, cex_pt, legend_xi, legend_yi.
fp <- list(
  grey = "gray",
  fig = list(
    list(width = 407, height = 231, x1 = 71.5, x5 = 389.5, y0 = 191.5, y100 = 14.5,
         legend_px = c(246.5, 120.5), pointsize = 12.0, mgp = c(3.0, 1.0, 0.0),
         legend_xi = 1.4, legend_yi = 1.0, cex_pt = 1.2),
    list(width = 402, height = 231, x1 = 71.5, x5 = 388.5, y0 = 192.5, y100 = 14.5,
         legend_px = c(246.5, 121.5), pointsize = 12.0, mgp = c(3.0, 1.0, 0.0),
         legend_xi = 1.3, legend_yi = 1.0, cex_pt = 1.2)
  )
)

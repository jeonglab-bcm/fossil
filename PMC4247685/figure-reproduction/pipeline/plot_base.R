# Base-graphics renders of Figs 3-5. The published frames are the plot region of R's default
# png() device (480 x 480 px, 72 dpi, pointsize 12, default margins) scaled by about 2, so we draw
# on that device; align.py maps the render onto the published pixel grid.
# Usage: Rscript plot_base.R <fig3|fig4|fig5> <data file> <out .png>
suppressMessages(library(survival))
a <- commandArgs(trailingOnly = TRUE)
fig <- a[1]

png(a[3], width = 480, height = 480, type = "cairo")

# survival 2.x drew curves with xaxs = "S" (axis starts at 0); survival 3 defaults to "r".
km_plot <- function(cl, time, event, xlab = "", ylab = "") {
  f <- survfit(Surv(cl[[time]], cl[[event]]) ~ cl$group)
  plot(f, lty = c(1, 2), mark.time = TRUE, xaxs = "S", xlab = xlab, ylab = ylab)
}

if (fig == "fig3") {
  d <- read.csv(a[2])
  b <- d[d$set == "bicluster", ]; k <- d[d$set == "control", ]
  # plot(density(bicluster)) then lines(density(control)): the axes follow the first density only.
  plot(b$x, b$y, type = "l", main = "", xlab = "value of pair-wise Pearson correlation coefficient",
       ylab = "Density")
  abline(h = 0, lwd = 0.1, col = "gray")
  lines(k$x, k$y, lty = 2)
} else if (fig == "fig4") {
  km_plot(read.csv(a[2]), "PFI.months", "PFI", xlab = "Time (months)",
          ylab = "Proportion of patients remaining progression-free")
} else if (fig == "fig5") {
  km_plot(read.csv(a[2]), "PFS", "progression")
}
invisible(dev.off())

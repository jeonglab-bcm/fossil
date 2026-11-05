# Presentation parameters of Figure 1, fitted to the published image (764 x 690 px JPEG).
# Measured from the image: the axis calibration (x150, x300, y0, y020).
# Fitted: raster resolution (R's default 12 pt text), legend position and size, fill colours.
fp <- list(
  width = 800, height = 740,          # device px
  pad_top = 40, crop = c(764, 690),   # the published frame: x 0..763, y pad_top..pad_top+689
  # Tick centres measured on the published image (intensity-weighted), plus 0.5 px: R puts
  # device coordinate v at the centre of pixel v - 0.5.
  x150 = 119.1, x300 = 743.27,
  y0 = 569.85, y020 = 77.7,
  res = 118, family = "Liberation Sans",
  mgp = c(3, 1, 0), xlab_line = 3, ylab_line = 2.95, ylab_px = 278,
  legend_px = c(572, -11), legend_xi = 1, legend_yi = 1, legend_cex = 1,
  # Fills: the hypergeometric bars (drawn first) take the colour sampled from the image,
  # (186, 182, 210). The empirical fill is the colour and alpha that give the sampled
  # (250, 182, 182) on white and the sampled overlap grey over the hypergeometric fill; the
  # overlap hue differs (the published colours went through a colour conversion).
  col_hyp = rgb(186, 182, 210, maxColorValue = 255),
  col_emp = rgb(246, 117, 117, 135, maxColorValue = 255)
)

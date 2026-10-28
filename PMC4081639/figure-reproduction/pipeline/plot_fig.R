suppressPackageStartupMessages({ library(ggplot2); library(tikzDevice); library(jsonlite) })
args <- commandArgs(trailingOnly = TRUE)
cfg <- fromJSON(args[1])
dat <- function(f) read.csv(file.path(cfg$datadir, f))

options(tikzMetricsDictionary = file.path(cfg$datadir, paste0("tikzMetrics_", cfg$font, "_", cfg$fig)),
        tikzDefaultEngine = "pdftex",
        tikzLwdUnit = if (is.null(cfg$lwdunit)) 72.27 / 96 else cfg$lwdunit)
nz <- function(v, d) if (is.null(v)) d else v
if (cfg$font == "times") {
  options(tikzLatexPackages = c(getOption("tikzLatexPackages"), "\\usepackage{mathptmx}\n"))
}

# ggplot2 0.9.3 theme_grey, restated for ggplot2 4.x; fills sampled from the published JPEGs
theme_grey093 <- function(base_size = 12) {
  theme(
    line = element_line(colour = "black", linewidth = 0.5, linetype = 1, lineend = "butt"),
    rect = element_rect(fill = "white", colour = "black", linewidth = 0.5, linetype = 1),
    text = element_text(family = "", face = "plain", colour = "black", size = base_size,
                        hjust = 0.5, vjust = 0.5, angle = 0, lineheight = 0.9, margin = margin(), debug = FALSE),
    axis.text = element_text(size = rel(0.8), colour = "grey50"),
    axis.text.x = element_text(vjust = 1, margin = margin(t = 0.1, unit = "cm")),
    axis.text.y = element_text(hjust = 1, margin = margin(r = nz(cfg$ytext_gap, 2.845))),
    axis.ticks = element_line(colour = "grey50"),
    axis.ticks.length = unit(0.15, "cm"),
    axis.title.x = element_text(margin = margin(t = cfg$xtitle_gap)),
    axis.title.y = element_text(angle = 90, size = nz(cfg$ytitle_size, base_size), hjust = nz(cfg$ytitle_hjust, 0.5), margin = margin(r = cfg$ytitle_gap)),
    legend.background = element_rect(colour = NA),
    legend.margin = margin(cfg$legend_pad, cfg$legend_pad, cfg$legend_pad, cfg$legend_pad),
    legend.box.spacing = unit(nz(cfg$legend_space, 5.67), "pt"),
    legend.justification = c(0.5, nz(cfg$legend_vjust, 0.5)),
    legend.key = element_rect(fill = cfg$key, colour = "white"),
    legend.key.size = unit(17.28, "pt"),
    legend.key.spacing = unit(0, "pt"),
    legend.text = element_text(size = rel(0.8)),
    legend.title = element_text(size = rel(0.8), face = "bold", hjust = 0),
    legend.position = "right",
    panel.background = element_rect(fill = cfg$panel, colour = NA),
    panel.border = element_blank(),
    panel.grid.major = element_line(colour = "white"),
    panel.grid.minor = element_line(colour = cfg$minor, linewidth = 0.25),
    panel.spacing = unit(0.25, "lines"),
    strip.background = element_rect(fill = cfg$strip, colour = NA),
    strip.text = element_text(size = rel(0.8), margin = margin(cfg$strip_pad, 0, cfg$strip_pad, 0)),
    plot.background = element_rect(colour = "white"),
    plot.title = element_text(size = rel(1.2), hjust = 0.5, margin = margin(b = cfg$title_gap)),
    plot.margin = unit(c(1, 1, 0.5, 0.5), "lines"),
    complete = TRUE
  )
}

sci <- function(x) format(x)

p <- switch(cfg$fig,
  "2" = ggplot(dat(if (is.null(cfg$f2)) "fig2_data.csv" else cfg$f2), aes(psi, error)) + geom_line() +
    scale_x_continuous(labels = sci) + labs(x = "$\\psi$", y = "log-lik error"),
  "4" = {
    d <- dat("fig4_data.csv")
    d$method <- factor(d$method, c("mesh", "aod_dirmult"), c("mesh", "aod,dirmult"))
    ggplot(d, aes(psi, error, linetype = method)) + geom_line() +
      scale_x_continuous(labels = sci) +
      scale_linetype_manual(values = c("solid", nz(cfg$dash, "22"))) +
      labs(x = "$\\psi$", y = "log-lik error", linetype = NULL)
  },
  "5" = {
    d <- dat("fig5_data.csv")
    d$method <- factor(d$method, c("VGAM", "mesh"))
    ggplot(d, aes(n, error, shape = method)) + geom_point(size = 2) +
      scale_shape_manual(values = c(0, 4)) +
      (if (is.null(cfg$ylim5)) NULL else scale_y_continuous(breaks = seq(-2000, 2000, 1000), minor_breaks = seq(-1500, 1500, 1000), expand = expansion(0))) +
      (if (is.null(cfg$ylim5)) NULL else coord_cartesian(ylim = cfg$ylim5)) +
      labs(x = "$n$", y = "log-lik error($10^{-14}$)", shape = NULL)
  },
  "6" = {
    d <- dat(nz(cfg$f6, "fig6_data.csv"))
    d$n <- factor(d$n, levels = sort(unique(d$n)), labels = as.character(sort(unique(d$n))))
    d$method <- factor(d$method, c("mesh", "VGAM"))
    ggplot(d, aes(method, runtime_us)) +
      geom_boxplot(outlier.colour = "black", outlier.size = 2, colour = "grey20") +
      facet_grid(. ~ n) +
      (if (is.null(cfg$ylim)) scale_y_log10() else scale_y_log10(breaks = c(1, 10, 100), minor_breaks = 10^c(-0.5, 0.5, 1.5, 2.5), expand = expansion(0))) +
      (if (is.null(cfg$ylim)) NULL else coord_cartesian(ylim = cfg$ylim)) +
      labs(x = NULL, y = "runtime ($\\mu$sec)", title = "$n$") +
      theme(axis.text.x = element_text(angle = 90, hjust = 1, vjust = 0.5))
  })

p <- p + theme_grey093() + if (cfg$fig == "6") theme(axis.text.x = element_text(angle = 90, hjust = 1, vjust = nz(cfg$xtext_vjust, 0.5), margin = margin(t = nz(cfg$xtext_gap, 2.85)))) else NULL

tikz(cfg$tex, width = cfg$W, height = cfg$H, standAlone = TRUE)
print(p)
invisible(dev.off())

# Fig. 2: per-dataset best-overlap F.score by method, one panel per implanted structure. The
# published figure is ggplot2 output at 300 dpi (1946 x 1355 px). Its text widths fit ggplot2
# 0.9.3's theme sizes at base_size 8.6 (axis titles 8.6 pt; tick labels, strips and legend 0.8 of
# that). The theme below follows it: white strips and panels with black borders, grey tick labels,
# no x tick labels, bold x title, 0.9.3 panel spacing and legend key size.
# Usage: Rscript plot_fig2.R <fig2_scores.csv> <out .png> [base_size]
suppressMessages(library(ggplot2))
a <- commandArgs(trailingOnly = TRUE)
base <- if (length(a) >= 3) as.numeric(a[3]) else 8.6

px <- function(n) unit(n * 72 / 300, "pt")
TITLE_GAP <- 32.5; PANEL_GAP <- 4; BOTTOM <- -4; STRIP_PAD <- 3.4; KEY_H <- 26.6; LEGEND_TITLE_GAP <- 5

d <- read.csv(a[1])
d$method <- factor(d$method, levels = c("GABi.block", "GABi.cor", "GABi.highvar", "ISA", "CC",
                                        "Plaid", "Bimax"))
d$structure <- factor(d$structure, levels = c("block", "cor", "highvar"))

p <- ggplot(d, aes(x = method, y = F.score, fill = method)) +
  geom_boxplot(outlier.size = 0.45, outlier.stroke = 0, linewidth = 0.3) +
  facet_grid(. ~ structure) +
  # The published panels span F.score -0.0489 to 1.0334: ticks 1.00 and 0.00 sit at rows 74.5 and
  # 1229 of the published image, and the panel runs from row 36 to row 1285.5.
  scale_y_continuous(limits = c(-0.0489, 1.0334), breaks = seq(0, 1, 0.25), expand = c(0, 0)) +
  labs(x = "Method", y = "F.score") +
  theme_bw(base_size = base, base_family = "Helvetica") +
  theme(strip.background = element_rect(fill = "white", colour = "black"),
        panel.border = element_rect(colour = "black"),
        panel.grid.major = element_line(colour = "grey97"),
        panel.grid.minor = element_line(colour = "grey99"),
        axis.text.x = element_blank(),
        axis.title.x = element_text(face = "bold", hjust = (854 - 103) / (1715 - 103), margin = margin(t = px(TITLE_GAP))),
        legend.title = element_text(face = "bold", size = rel(0.8), margin = margin(b = px(LEGEND_TITLE_GAP))),
        legend.key = element_blank(),
        panel.spacing = px(PANEL_GAP),
        plot.margin = margin(px(3), px(4), px(BOTTOM), 0),
        strip.text = element_text(margin = margin(px(STRIP_PAD), 0, px(STRIP_PAD), 0)),
        # Sizes measured on the published image, in pixels at 300 dpi.
        axis.ticks.length = px(6),
        axis.text.y = element_text(colour = "grey50", margin = margin(r = px(8))),
        axis.title.y = element_text(margin = margin(r = 0)),
        legend.key.width = px(20), legend.key.height = px(KEY_H), legend.key.spacing.y = unit(0, "pt"),
        legend.box.spacing = px(29), legend.margin = margin(0, 0, px(3), 0),
        legend.text = element_text(margin = margin(l = px(8))))

ggsave(a[2], p, width = 1946 / 300, height = 1355 / 300, dpi = 300, bg = "white")

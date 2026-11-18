# Run from PMC4168973/work (after prepare_data.R and pds.R): Rscript ../figure-reproduction/experiments/pam50_clusters.R
d <- readRDS("data/miller.rds"); pam <- read.csv("data/pam50_genes.csv")$symbol; x <- d$expr[intersect(pam, rownames(d$expr)), ]
ev <- d$clin$event
f <- function(lbl, h) { g <- cutree(h, 2); cat(sprintf("%-38s", lbl), table(g), " p", signif(suppressWarnings(chisq.test(table(g, ev))$p.value), 3), "\n") }
z <- t(scale(t(x)))
cat("paper p 7.46e-5\n")
f("euclid complete raw", hclust(dist(t(x))))
f("euclid complete z-scored genes", hclust(dist(t(z))))
f("euclid average z", hclust(dist(t(z)), "average"))
f("euclid ward.D2 z", hclust(dist(t(z)), "ward.D2"))
f("1-pearson complete raw", hclust(as.dist(1 - cor(x))))
f("1-pearson complete z", hclust(as.dist(1 - cor(z))))
f("1-pearson average z", hclust(as.dist(1 - cor(z)), "average"))
f("euclid ward.D2 raw", hclust(dist(t(x)), "ward.D2"))

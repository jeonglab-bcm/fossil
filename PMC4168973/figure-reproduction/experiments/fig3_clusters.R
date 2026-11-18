# Run from PMC4168973/work (after prepare_data.R and pds.R): Rscript ../figure-reproduction/experiments/fig3_clusters.R
d <- readRDS("data/miller.rds"); P <- read.csv("pds/miller.csv", check.names = FALSE)
pw <- c("KEGG_MELANOGENESIS","BIOCARTA_SRCRPTP_PATHWAY","BIOCARTA_AKAP13_PATHWAY","BIOCARTA_RARRXR_PATHWAY","BIOCARTA_VIP_PATHWAY","KEGG_FATTY_ACID_METABOLISM","BIOCARTA_G1_PATHWAY","KEGG_LINOLEIC_ACID_METABOLISM","KEGG_LYSOSOME","BIOCARTA_P53_PATHWAY","BIOCARTA_PYK2_PATHWAY","BIOCARTA_GABA_PATHWAY","BIOCARTA_FEEDER_PATHWAY","BIOCARTA_RNA_PATHWAY","BIOCARTA_IL5_PATHWAY")
x <- as.matrix(P[match(pw, P$pathway), -(1:2)]); ev <- d$clin$event; z <- t(scale(t(x)))
f <- function(lbl, h) { g <- cutree(h, 2); cat(sprintf("%-32s", lbl), table(g), " p", signif(suppressWarnings(chisq.test(table(g, ev))$p.value), 3), "\n") }
cat("paper p 1.99e-6\n")
f("euclid complete raw", hclust(dist(t(x)))); f("euclid complete z", hclust(dist(t(z))))
f("euclid ward.D2 raw", hclust(dist(t(x)), "ward.D2")); f("1-pearson complete z", hclust(as.dist(1 - cor(z))))
f("1-pearson average z", hclust(as.dist(1 - cor(z)), "average"))

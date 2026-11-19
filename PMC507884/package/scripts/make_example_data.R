# Write the bundled example data (run from the package folder):
#   Rscript scripts/make_example_data.R SZABO_XLS
# SZABO_XLS: gb-2004-5-8-r59-s1.xls, Additional data file 1 of Szabo et al. (2004).
# Needs readxl. Values are written unchanged (each reads back to the same double); only the layout
# changes: PUM is named PUM1 as in the paper, samples are T1-T80, POOL tissues get POOL_ names.
args <- commandArgs(TRUE)
x <- as.data.frame(readxl::read_excel(args[1], sheet = "Relative copy numbers"))
names(x)[names(x) == "PUM"] <- "PUM1"
names(x)[names(x) == "Sample"] <- "sample"
x$sample <- paste0("T", x$sample)
# Shortest decimal that reads back to the same double (15 significant digits suffice here; checked).
num <- names(x)[-1]
txt <- x; txt[num] <- lapply(x[num], function(v) { s <- as.character(v); stopifnot(identical(as.numeric(s), v)); s })
write.csv(txt, "inst/extdata/szabo2004_breast.csv", row.names = FALSE, quote = FALSE)

# Model 2 example: synthetic data from known parameters (Vandesompele et al.'s data carry no
# redistribution licence, so they are not bundled). Five genes, three tissue types of 60 samples.
set.seed(20041)
genes <- c("G1", "G2", "G3", "G4", "G5"); tis <- c("A", "B", "C"); nk <- 60
sigma <- c(G1 = 0.20, G2 = 0.25, G3 = 0.30, G4 = 0.40, G5 = 0.50)
varsigma <- c(A = 1, B = 1.5, C = 2)
CG <- rbind(A = c(0.6, -0.1, -0.3, 0.2, -0.4), B = c(-0.2, 0.3, 0.1, -0.5, 0.3), C = c(-0.4, -0.2, 0.2, 0.3, 0.1))
colnames(CG) <- genes
G <- c(2, 1, 0, -1, -2); Ck <- c(A = -0.5, B = 0, C = 0.5)
rows <- list()
for (k in tis) for (i in seq_len(nk)) {
  Ti <- rnorm(1, 0, 1)
  y <- 3 + Ck[k] + Ti + G + CG[k, ] + rnorm(5, 0, varsigma[k] * sigma)
  rows[[length(rows) + 1]] <- data.frame(sample = sprintf("%s%02d", k, i), tissue = k, t(signif(exp(y), 6)))
}
syn <- do.call(rbind, rows); names(syn)[3:7] <- genes
write.csv(syn, "inst/extdata/synthetic_tissues.csv", row.names = FALSE, quote = FALSE)
truth <- rbind(data.frame(parameter = "sigma", key = genes, value = unname(sigma)),
               data.frame(parameter = "varsigma", key = tis, value = unname(varsigma)),
               data.frame(parameter = "bias", key = as.vector(outer(tis, genes, paste, sep = ":")), value = as.vector(CG)))
write.csv(truth, "inst/extdata/synthetic_truth.csv", row.names = FALSE, quote = FALSE)

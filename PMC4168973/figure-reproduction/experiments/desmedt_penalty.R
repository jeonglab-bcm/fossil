# Run from PMC4168973/work: Rscript ../figure-reproduction/experiments/desmedt_penalty.R
# Desmedt's own pathway model at penalties below the cross-validated ones (4.7 to 6.2), in-sample.
suppressMessages({library(pdscox); library(penalized); library(survival)})
d <- readRDS("data/desmedt.rds"); P <- read.csv("pds/desmedt.csv", check.names = FALSE)
X <- t(as.matrix(P[, -(1:2)])); colnames(X) <- P$pathway
m <- read_series_matrix("downloads/GSE7390_series_matrix.txt.gz")
cat("ESR1 against ER status: r =", round(cor(d$expr["ESR1", ], d$clin$er), 2), "for the gene,", round(cor(m$expr["205225_at", ], as.numeric(m$characteristics[["er"]])), 2), "for probe 205225_at\n")
for (l in c(4.69, 3, 2, 1)) {
  f <- penalized(Surv(d$clin$time, d$clin$event), penalized = X, lambda1 = l, trace = FALSE)
  cf <- coefficients(f, "penalized"); cf <- cf[cf != 0]
  if (!length(cf)) { cat("lambda", l, ": no pathway kept\n"); next }
  pi <- drop(X[, names(cf), drop = FALSE] %*% cf)
  e <- evaluate_model(pi, d$clin$time, d$clin$event, quantile(pi, 1 - mean(d$clin$event)))
  cat("lambda", l, ":", length(cf), "pathways, log-rank p", signif(e$p, 3), "AUC", round(e$auc, 3), "\n")
}

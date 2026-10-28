# Figs 3 and 4 from the reconstructed TCGA bicluster (paper p. 11-12).
# Usage: Rscript make_fig34_data.R <matrix .rds> <samples .csv> <bicluster .json> <S2 probes>
#                                  <out fig3 .csv> <out fig4 .csv> <out summary .json>
suppressMessages({library(survival); library(jsonlite)})
a <- commandArgs(trailingOnly = TRUE)
x <- readRDS(a[1]); smp <- read.csv(a[2]); bc <- fromJSON(a[3], simplifyVector = FALSE)
s2 <- sub("\r$", "", readLines(a[4]))

best <- bc$solutions[[1]]
J <- match(unlist(best$samples), colnames(x))
I <- match(unlist(best$features), rownames(x))

# Control set as in S1's survival term: the l = min(|J|, |Y| - |J|) samples whose profile over the
# bicluster features is least correlated (absolute Pearson) with the first bicluster sample.
others <- setdiff(seq_len(ncol(x)), J)
ref <- x[I, J[1]]
r <- vapply(others, function(k) {
  ok <- !is.na(x[I, k]) & !is.na(ref)
  if (sum(ok) > 1) cor(x[I, k][ok], ref[ok]) else 2
}, 0)
K <- others[order(abs(r))[seq_len(min(length(J), length(others)))]]

# Fig. 3: pairwise Pearson correlation between all selected CpG sites, across each sample set.
pair_cors <- function(cols) {
  m <- x[I, cols]
  m <- m[rowSums(is.na(m)) == 0 & apply(m, 1, sd) > 0, , drop = FALSE]
  cc <- cor(t(m))
  cc[upper.tri(cc)]
}
cb <- pair_cors(J); ck <- pair_cors(K)
db <- density(cb); dk <- density(ck)
write.csv(rbind(data.frame(set = "bicluster", x = db$x, y = db$y),
                data.frame(set = "control", x = dk$x, y = dk$y)), a[5], row.names = FALSE)

# Fig. 4: progression-free survival of the two sets.
g <- rbind(data.frame(smp[J, ], group = "bicluster"), data.frame(smp[K, ], group = "control"))
write.csv(g, a[6], row.names = FALSE)
s <- survdiff(Surv(PFI.months, PFI) ~ group, data = g)
km <- summary(survfit(Surv(PFI.months, PFI) ~ group, data = g))$table
os <- survdiff(Surv(OS.months, OS) ~ group, data = g)

feat <- rownames(x)[I]
write_json(list(
  bicluster_samples = length(J), control_samples = length(K), features = length(I),
  features_in_S3 = length(feat), features_in_S2 = sum(feat %in% s2),
  score = best$score, n_solutions = length(bc$solutions), seconds = bc$seconds,
  pfs_logrank_p = pchisq(s$chisq, 1, lower.tail = FALSE),
  os_logrank_p = pchisq(os$chisq, 1, lower.tail = FALSE),
  pfs_median_months = setNames(as.list(km[, "median"]), c("bicluster", "control")),
  pair_cor_median = list(bicluster = median(cb), control = median(ck)),
  pair_cor_mode = list(bicluster = db$x[which.max(db$y)], control = dk$x[which.max(dk$y)]),
  paper = list(bicluster_samples = 21, control_samples = 21, features = 14382,
               pfs_logrank_p = 1e-5, pfs_median_months = list(bicluster = 85.4, control = 32))),
  a[7], auto_unbox = TRUE, digits = NA, pretty = TRUE)

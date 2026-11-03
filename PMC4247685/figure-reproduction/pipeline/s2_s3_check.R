# Tables S2 and S3 both claim to list the 14,382 CpG sites of the dysregulation bicluster. This
# measures how the two lists differ and which one behaves like a bicluster in TCGA.
# Usage: Rscript s2_s3_check.R <S2> <S3> <HumanMethylation27.gz> <out .json>
suppressMessages({library(data.table); library(jsonlite)})
a <- commandArgs(trailingOnly = TRUE)
s2 <- sub("\r$", "", readLines(a[1]))
s3t <- read.delim(a[2], row.names = 1, check.names = FALSE)
b <- as.matrix(s3t[-(1:4), ]); s3 <- rownames(b)
m <- fread(cmd = paste("gzip -dc", shQuote(a[3])))
probes <- m[[1]]; m <- as.matrix(m[, -1]); rownames(m) <- probes
m <- m[, substr(colnames(m), 14, 15) == "01"]

shared <- intersect(s2, s3); s2o <- setdiff(s2, s3); s3o <- setdiff(s3, s2)
all_sorted <- sort(probes)
pos <- match(s2, all_sorted) - match(s3, all_sorted)

# Row labels of S3 against TCGA: the mean beta of each S3 row should track the TCGA mean of the
# probe it is labelled with, and not the TCGA mean of the S2 probe at the same row.
tm <- rowMeans(m, na.rm = TRUE); vm <- rowMeans(b, na.rm = TRUE)
lab_s3 <- cor(vm, tm[s3], use = "complete.obs")
diffrow <- s2 != s3
lab_s2 <- cor(vm[diffrow], tm[s2[diffrow]], use = "complete.obs")

set.seed(1)
mean_abs_r <- function(ids, n = 600) {
  z <- m[ids, ]; z <- z[complete.cases(z), , drop = FALSE]; z <- z[apply(z, 1, sd) > 0, ]
  z <- z[sample(nrow(z), min(n, nrow(z))), ]
  cc <- cor(t(z)); mean(abs(cc[upper.tri(cc)]))
}
rnd <- sample(setdiff(probes, union(s2, s3)), 3000)
sdv <- apply(m, 1, sd, na.rm = TRUE)
res <- list(
  s2 = length(s2), s3 = length(s3), shared = length(shared), s2_only = length(s2o), s3_only = length(s3o),
  both_sorted = !is.unsorted(s2) && !is.unsorted(s3),
  rows_equal_until = which(s2 != s3)[1] - 1L,
  row_offset_range = range(abs(pos)),
  s3_labels_vs_tcga_mean_r = lab_s3, s2_labels_at_same_row_vs_tcga_mean_r = lab_s2,
  tcga_primary_tumours = ncol(m),
  tcga_mean_abs_r = list(shared = mean_abs_r(shared), s2_only = mean_abs_r(s2o),
                         s3_only = mean_abs_r(s3o), random = mean_abs_r(rnd)),
  tcga_median_sd = list(shared = median(sdv[shared], na.rm = TRUE), s2_only = median(sdv[s2o], na.rm = TRUE),
                        s3_only = median(sdv[s3o], na.rm = TRUE), random = median(sdv[rnd], na.rm = TRUE)))
write_json(res, a[4], auto_unbox = TRUE, digits = NA, pretty = TRUE)

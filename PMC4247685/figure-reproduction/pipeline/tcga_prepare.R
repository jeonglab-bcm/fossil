# TCGA input for the dysregulation-vs-outcome bicluster (paper p. 11-12).
# Usage: Rscript tcga_prepare.R <HumanMethylation27.gz> <OV_clinicalMatrix> <OV_survival.txt>
#                               <Table S3> <out matrix .rds> <out samples .csv>
suppressMessages({library(data.table); library(survival)})
a <- commandArgs(trailingOnly = TRUE)

m <- fread(cmd = paste("gzip -dc", shQuote(a[1])))
probes <- m[[1]]; m <- as.matrix(m[, -1]); rownames(m) <- probes
clin <- fread(a[2]); sv <- fread(a[3])

# Primary high-grade serous tumours (sample type 01, grade G3/G4) with a progression-free
# interval in the TCGA Pan-Cancer clinical resource.
hg <- clin[sample_type == "Primary Tumor" & neoplasm_histologic_grade %in% c("G3", "G4"), sampleID]
keep <- colnames(m)[substr(colnames(m), 14, 15) == "01"]
keep <- intersect(keep, intersect(hg, sv[!is.na(PFI.time) & !is.na(PFI), sample]))

# Row universe: the probe labels of Table S3, which carry the bicluster's beta-values. Table S2
# lists a different set from row 521 on (see README).
s3 <- sub("\r$", "", fread(a[4], select = 1L, skip = 5L, header = FALSE)[[1]])
x <- m[intersect(s3, rownames(m)), keep]
x <- x[rowSums(!is.na(x)) > 0, ]

# Xena stores beta-values to 4 decimals; the level-3 files the paper used carried more digits.
# Rounding creates ties, which switch R's Spearman test from its exact-series p-value to the
# t approximation. Spread each value uniformly over its rounding interval to restore tie-free data.
set.seed(2014)
nz <- !is.na(x)
x[nz] <- x[nz] + runif(sum(nz), -5e-5, 5e-5)

s <- sv[match(keep, sample)]
samples <- data.frame(sample = keep, grade = clin[match(keep, sampleID), neoplasm_histologic_grade],
                      PFI = s$PFI, PFI.months = s$PFI.time / 30.44, OS = s$OS,
                      OS.months = s$OS.time / 30.44)
saveRDS(x, a[5])
write.csv(samples, a[6], row.names = FALSE)
cat(sprintf("%d probes x %d tumours (%d probes in Table S3)\n", nrow(x), ncol(x), length(s3)))

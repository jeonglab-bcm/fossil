# Summarize the replicates of every setting.
#   Rscript summarize.R RUN_DIR [RUN_DIR ...] --out SUMMARY.csv --check CHECK.csv [--check-reps 3]
# SUMMARY.csv: per setting, test set, classifier and measure: replicates, missing, mean (NA when any
# replicate is NA, as the paper's tables), mean of the available replicates, SD and the 2.5th and
# 97.5th percentiles (the 95% prediction interval). Also nsel_all: the share of replicates whose
# 40 selected variables include all 20 that differ (alternative case, no MultDS).
# CHECK.csv: every value of the first replicates of every setting; CI reruns them and compares.
suppressPackageStartupMessages(library(multds))
args <- commandArgs(trailingOnly = TRUE)
opt <- function(flag, default) { i <- match(flag, args); if (is.na(i)) default else args[i + 1] }
out <- opt("--out", "summary.csv")
check <- opt("--check", "replicates_check.csv")
nck <- as.integer(opt("--check-reps", "3"))
dirs <- args[seq_len(min(which(startsWith(args, "--"))) - 1)]
files <- unlist(lapply(dirs, list.files, pattern = "\\.rds$", full.names = TRUE))
sm <- list()
ck <- list()
metrics <- c("PA", "PA1", "PA2", "PV1", "PV2", "AUC")
for (f in sort(files)) {
  r <- readRDS(f)
  s <- summarize_runs(r)
  if ("nsel_de" %in% names(r)) {
    first <- r[r$method == r$method[1] & r$test == r$test[1], ]
    s$nsel_all <- if (all(is.na(first$nsel_de))) NA_real_ else mean(first$nsel_de == 20)
  } else {
    s$nsel_all <- NA_real_
  }
  sm[[f]] <- s
  ck[[f]] <- r[r$rep <= nck, c("setting", "test", "method", "rep", metrics)]
}
sm <- do.call(rbind, sm)
num <- c("mean", "mean_avail", "sd", "q025", "q975", "q05", "q95", "nsel_all")
sm[num] <- lapply(sm[num], function(v) signif(v, 8))
write.csv(sm, out, row.names = FALSE, na = "NA")
ck <- do.call(rbind, ck)
ck[metrics] <- lapply(ck[metrics], function(v) signif(v, 10))
write.csv(ck[order(ck$setting, ck$test, ck$method, ck$rep), ], check, row.names = FALSE, na = "NA")
cat(sprintf("%d settings, %d summary rows, %d check rows\n", length(files), nrow(sm), nrow(ck)))

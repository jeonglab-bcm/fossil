# Simulation study of Ackermann and Strimmer (2009), Tables 2 to 6, with the package gseamod.
# One replicate = one simulated data set (600 genes, 20 samples, nine sets), analysed with every
# combination the tables report and a few variants used to test causes. Each replicate has its
# own seed, so any subset can be rerun and compared with the committed per-replicate p-values.
#
# Usage: Rscript simulate_tables.R OUTDIR FIRST LAST [CORES]
suppressMessages(library(gseamod))
args <- commandArgs(TRUE)
outdir <- args[1]
first <- as.integer(args[2]); last <- as.integer(args[3])
cores <- if (length(args) >= 4) as.integer(args[4]) else 1L
B <- 1000L
SEED0 <- 20090203L
dir.create(outdir, showWarnings = FALSE, recursive = TRUE)

one <- function(r) {
  d <- simulate_ackermann(seed = SEED0 + r)
  X <- d$X; y <- d$y; sets <- d$sets
  set.seed(SEED0 + 100000L + r)
  rs <- random_sets(nrow(X), 20L, B)
  pm <- permute_labels(y, B)
  run <- function(...) gsea(X, y, sets, B = B, perms = pm, rsets = rs, ...)$p
  cols <- list()
  # Table 2: gene-level statistic x transformation; mean, resampling
  for (g in c("t", "modt", "corr")) for (tr in c("none", "square", "ranksq", "binary", "lfdr")) {
    cols[[paste("T2", g, tr, sep = ".")]] <- run(gene = g, transform = tr, setstat = "mean", method = "resampling")
  }
  # Table 3: squared moderated t, resampling, six gene set statistics (mean is the Table 2 cell)
  for (st in c("maxmean", "median", "es", "condfdr", "wilcoxon")) {
    cols[[paste0("T3.", st)]] <- run(gene = "modt", transform = "square", setstat = st, method = "resampling")
  }
  # Table 4: mean of squared moderated t, four significance assessments (resampling is the Table 2 cell)
  for (me in c("parametric", "permutation", "restandardization")) {
    cols[[paste0("T4.", me)]] <- run(gene = "modt", transform = "square", setstat = "mean", method = me)
  }
  # Table 5: globaltest
  for (me in c("parametric", "resampling", "permutation", "restandardization")) {
    cols[[paste0("T5.", me)]] <- run(setstat = "globaltest", method = me)
  }
  # Table 6: Hotelling T2 with a shrinkage correlation
  for (me in c("resampling", "permutation", "restandardization")) {
    cols[[paste0("T6.", me)]] <- run(setstat = "hotelling", method = me)
  }
  # Variants for the text and the causes
  for (st in c("median", "wilcoxon")) {
    cols[[paste0("V.perm.", st)]] <- run(gene = "modt", transform = "square", setstat = st, method = "permutation")
  }
  for (g in c("t", "modt", "corr")) {
    cols[[paste("V.binary_lfdr02", g, sep = ".")]] <- run(gene = g, transform = "binary", setstat = "mean",
                                                          method = "resampling", binary_rule = "lfdr", binary_cutoff = 0.2)
  }
  cols[["V.condslope"]] <- run(gene = "modt", transform = "square", setstat = "condslope", method = "resampling")
  for (me in c("resampling", "permutation")) {
    cols[[paste0("V.hotelling_overall.", me)]] <- run(setstat = "hotelling", method = me, hotelling_center = "overall")
    cols[[paste0("V.hotelling_cov.", me)]] <- run(setstat = "hotelling", method = me, hotelling_shrink = "covariance")
  }
  cols[["V.wilcoxon.parametric"]] <- run(gene = "modt", transform = "square", setstat = "wilcoxon", method = "parametric")
  out <- data.frame(replicate = r, set = names(sets), cols, check.names = FALSE)
  write.csv(out, file.path(outdir, sprintf("rep_%03d.csv", r)), row.names = FALSE)
  r
}

reps <- first:last
if (cores > 1) {
  invisible(parallel::mclapply(reps, one, mc.cores = cores, mc.preschedule = FALSE))
} else {
  invisible(lapply(reps, one))
}
missing <- reps[!file.exists(file.path(outdir, sprintf("rep_%03d.csv", reps)))]
if (length(missing)) stop("replicates failed: ", paste(missing, collapse = " "))

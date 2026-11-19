# Figures 2 and 4, Table 7 and the Hedenfalk ES claim of Ackermann and Strimmer (2009): every gene
# set of the p53 or Hedenfalk data tested with the squared moderated t and eight gene set
# statistics, by gene sampling (resampling) and by sample label permutation, 1000 draws each.
# Random gene sets are drawn per set size with a seed of their own and the label permutations once
# per data set, so a run on any subset of sets gives the same p-values as the full run.
#
# Usage: Rscript real_data.R DATA.rds OUT.csv [CORES] [SETS]   (SETS: comma-separated set indices)
suppressMessages(library(gseamod))
args <- commandArgs(TRUE)
d <- readRDS(args[1])
out <- args[2]
cores <- if (length(args) >= 3) as.integer(args[3]) else 1L
B <- 1000L
SEED <- 20090203L
X <- d$X; y <- d$y; sets <- d$sets
pick <- if (length(args) >= 4) as.integer(strsplit(args[4], ",")[[1]]) else seq_along(sets)
sets <- sets[pick]
sizes <- sort(unique(lengths(sets)))
rsets <- lapply(sizes, function(m) { set.seed(SEED + m); random_sets(nrow(X), m, B)[[1]] })
names(rsets) <- as.character(sizes)
set.seed(SEED)
pm <- permute_labels(y, B)
jobs <- expand.grid(stat = c("mean", "median", "maxmean", "es", "wilcoxon", "condfdr", "globaltest", "hotelling"),
                    method = c("resampling", "permutation"), stringsAsFactors = FALSE)
run <- function(j) {
  r <- gsea(X, y, sets, gene = "modt", transform = "square", setstat = jobs$stat[j], method = jobs$method[j],
            B = B, perms = pm, rsets = rsets)
  r$p
}
res <- if (cores > 1) parallel::mclapply(seq_len(nrow(jobs)), run, mc.cores = cores, mc.preschedule = FALSE) else lapply(seq_len(nrow(jobs)), run)
bad <- vapply(res, function(r) !is.numeric(r), logical(1))
if (any(bad)) stop("jobs failed: ", paste(which(bad), collapse = " "), "\n", paste(sapply(res[bad], as.character), collapse = "\n"))
P <- do.call(cbind, res)
colnames(P) <- paste(jobs$stat, jobs$method, sep = ".")
write.csv(data.frame(index = pick, set = names(sets), size = lengths(sets), P, check.names = FALSE), out, row.names = FALSE)

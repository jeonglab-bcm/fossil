# Summarise the per-replicate results (output/sim) as in the paper's figures, with the package.
#   Rscript summarise_sim.R SIM_DIR summary.json
# True values: mean coefficient and empirical SE over the 20,000 complete-data cohorts.
suppressMessages(library(misscox))
a <- commandArgs(TRUE)
sim <- a[1]
read_dir <- function(d) {
  f <- sort(list.files(file.path(sim, d), pattern = "\\.csv\\.gz$", full.names = TRUE))
  if (!length(f)) return(NULL)
  do.call(rbind, lapply(f, function(x) utils::read.csv(gzfile(x), stringsAsFactors = FALSE)))
}
truth_fits <- read_dir("truth")
coefs <- c("X1", "X2", "X3", "X4", "X5", "X6", "X7", "X8d1", "X8d2")
truth <- vapply(coefs, function(v) mean(truth_fits[[v]]), 0)
emp_se <- vapply(coefs, function(v) sd(truth_fits[[v]]), 0)
rows <- list()
full <- NULL
for (mech in c("MAR", "MNAR", "MCAR", "COMBINED")) {
  r <- read_dir(mech)
  if (is.null(r)) next
  f <- r[r$method == "FULL", ]
  full <- rbind(full, f[!(f$rep %in% full$rep), ])
  rows[[mech]] <- r[r$method != "FULL", ]
}
res <- do.call(rbind, c(rows, list(full)))
s <- summarise_replicates(res, truth)
out <- list(truth = list(reps = nrow(truth_fits), mean = as.list(truth), empirical_se = as.list(emp_se)),
            paper_lp = as.list(paper_coefficients()),
            replicates = lapply(split(res$rep, paste(res$mechanism, res$method)), function(x) length(unique(x))),
            summary = s)
writeLines(jsonlite::toJSON(out, auto_unbox = TRUE, digits = 10, dataframe = "rows", pretty = FALSE),
           a[2])

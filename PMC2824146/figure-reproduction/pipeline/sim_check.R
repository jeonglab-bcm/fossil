# Rerun a few replicates from scratch and compare them with the committed per-replicate results.
#   Rscript sim_check.R SIM_DIR sim_check.json [REP]
# Checks replicate REP (default 1) under MAR (all nine methods) and MNAR, and the first 200
# true-value cohorts.
suppressMessages(library(misscox))
a <- commandArgs(TRUE)
sim <- a[1]; rep <- if (length(a) >= 3) as.integer(a[3]) else 1L
cv <- gbsg_covariates(); pr <- generation_parameters(cv)
sets <- list(MAR = method_labels(), MNAR = c("CC", "SI", "MICE", "MICE_PMM", "MICE_PMM_notrans", "AREG"))
committed_rows <- function(dir, rep) {
  f <- list.files(file.path(sim, dir), pattern = "\\.csv\\.gz$", full.names = TRUE)
  for (x in f) { d <- utils::read.csv(gzfile(x), stringsAsFactors = FALSE); if (rep %in% d$rep) return(d[d$rep == rep, ]) }
  NULL
}
compare <- function(fresh, old, label) {
  if (is.null(old)) return(list(study = label, rep = rep, rows = nrow(fresh),
                                differences = list("no committed rows for this replicate")))
  num <- intersect(names(fresh)[vapply(fresh, is.numeric, TRUE)], names(old))
  key <- function(d) paste(d$mechanism, d$level, d$method)
  old <- old[match(key(fresh), key(old)), ]
  diffs <- character(0)
  for (k in num) {
    rel <- abs(fresh[[k]] - old[[k]]) / pmax(abs(old[[k]]), 1e-300)
    bad <- which(!(abs(fresh[[k]] - old[[k]]) <= 1e-8 | rel <= 1e-6))
    if (length(bad)) diffs <- c(diffs, sprintf("%s %s: %s", label, k, paste(key(fresh)[bad][1:min(3, length(bad))], collapse = "; ")))
  }
  list(study = label, rep = rep, rows = nrow(fresh), differences = as.list(diffs))
}
out <- list()
for (mech in names(sets)) {
  fresh <- run_replicate(rep, pr, stats::setNames(list(sets[[mech]]), mech))
  out[[length(out) + 1]] <- compare(fresh, committed_rows(mech, rep), mech)
}
tf <- true_value_fits(200, pr)
tc <- utils::read.csv(gzfile(file.path(sim, "truth", "truth_1-5000.csv.gz")))[1:200, ]
d <- max(abs(as.matrix(tf) - as.matrix(tc[, names(tf)])))
out[[length(out) + 1]] <- list(study = "true values", rep = "1-200", rows = 200L,
  differences = if (d > 1e-8) list(sprintf("max abs difference %.3g", d)) else list())
res <- list(passed = all(vapply(out, function(o) length(o$differences) == 0, TRUE)), replicates = out)
writeLines(jsonlite::toJSON(res, auto_unbox = TRUE, pretty = TRUE), a[2])

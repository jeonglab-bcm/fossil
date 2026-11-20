# One chunk of the simulation study, with the package misscox.
#   Rscript run_sim.R sim   FIRST LAST MECHSET OUT.csv.gz [N] [M]
#   Rscript run_sim.R truth FIRST LAST OUT.csv.gz
# MECHSET: MAR (all nine methods), MNAR, MCAR or COMBINED (the methods the paper shows).
suppressMessages(library(misscox))
a <- commandArgs(TRUE)
cv <- gbsg_covariates()
pr <- generation_parameters(cv)
first <- as.integer(a[2]); last <- as.integer(a[3])
if (a[1] == "truth") {
  out <- true_value_fits(last - first + 1, pr, first = first)
  out <- cbind(rep = first:last, out)
  f <- a[4]
} else {
  shown <- c("CC", "SI", "MICE", "MICE_PMM", "MICE_PMM_notrans", "AREG", "MIX_notrunc")
  sets <- list(MAR = method_labels(),
               MNAR = c("CC", "SI", "MICE", "MICE_PMM", "MICE_PMM_notrans", "AREG"),
               MCAR = shown, COMBINED = shown)
  mech <- a[4]
  n <- if (length(a) >= 6) as.integer(a[6]) else 1000L
  m <- if (length(a) >= 7) as.integer(a[7]) else 20L
  mechs <- stats::setNames(list(sets[[mech]]), mech)
  out <- do.call(rbind, lapply(first:last, function(r) run_replicate(r, pr, mechs, n = n, m = m)))
  f <- a[5]
}
num <- vapply(out, is.numeric, TRUE)
out[num] <- lapply(out[num], function(v) signif(v, 10))
con <- gzfile(f, "w")
utils::write.csv(out, con, row.names = FALSE)
close(con)

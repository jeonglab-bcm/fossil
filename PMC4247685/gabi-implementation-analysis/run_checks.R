# Run every check in checks/ in its own R process and summarise.
#   Rscript run_checks.R            (from any directory)
#   GABI_SOURCES=/path/to/sources Rscript run_checks.R
self <- sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])
dir <- file.path(dirname(normalizePath(self)), "checks")
scripts <- sort(list.files(dir, pattern = "^[0-9]{2}_.*\\.R$", full.names = TRUE))
rscript <- file.path(R.home("bin"), "Rscript")
cat(R.version.string, "| GABi", as.character(packageVersion("GABi")),
    "| survival", as.character(packageVersion("survival")), "\n\n")
tot <- c(pass = 0, fail = 0)
for (s in scripts) {
  t0 <- Sys.time()
  out <- suppressWarnings(system2(rscript, shQuote(s), stdout = TRUE, stderr = FALSE))
  st <- attr(out, "status")
  lines <- grep("^(PASS|FAIL|SUMMARY|      )", out, value = TRUE)
  cat(lines, sep = "\n")
  np <- sum(startsWith(out, "PASS")); nf <- sum(startsWith(out, "FAIL"))
  if (!any(startsWith(out, "SUMMARY"))) { cat("FAIL  ", basename(s), " did not finish\n", sep = ""); nf <- nf + 1 }
  tot <- tot + c(np, nf)
  cat(sprintf("      (%.0f s)\n\n", as.numeric(difftime(Sys.time(), t0, units = "secs"))))
}
cat(sprintf("TOTAL: %d pass, %d fail in %d scripts\n", tot[["pass"]], tot[["fail"]], length(scripts)))
quit(save = "no", status = if (tot[["fail"]] > 0) 1 else 0)

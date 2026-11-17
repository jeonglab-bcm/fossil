# Run simulation settings and keep each replicate's metrics.
#   Rscript simulate.R OUTDIR [--family F[,F...]] [--reps 1:1000] [--cores 4] [--only REGEX]
# Writes OUTDIR/<setting>.rds (one data frame of replicates per setting); existing files with the
# same replicates are skipped, so an interrupted run resumes.
args <- commandArgs(trailingOnly = TRUE)
here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE))))
source(file.path(here, "settings.R"))
opt <- function(flag, default) { i <- match(flag, args); if (is.na(i)) default else args[i + 1] }
outdir <- args[1]
fams <- opt("--family", NA)
reps <- eval(parse(text = opt("--reps", "1:1000")))
cores <- as.integer(opt("--cores", "1"))
only <- opt("--only", NA)
dir.create(outdir, showWarnings = FALSE, recursive = TRUE)
S <- all_settings()
if (!is.na(fams)) S <- S[vapply(S, function(x) x$family %in% strsplit(fams, ",")[[1]], TRUE)]
if (!is.na(only)) S <- S[grepl(only, names(S))]
for (nm in names(S)) {
  f <- file.path(outdir, paste0(nm, ".rds"))
  todo <- reps[reps <= S[[nm]]$reps]
  if (file.exists(f)) {
    old <- readRDS(f)
    if (setequal(unique(old$rep), todo)) next
  }
  t0 <- Sys.time()
  r <- run_setting(S[[nm]], todo, cores = cores)
  saveRDS(r, f)
  cat(sprintf("%s %d reps %.1f s\n", nm, length(todo), as.numeric(Sys.time() - t0, units = "secs")))
}

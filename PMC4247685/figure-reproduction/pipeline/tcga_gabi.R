# GABi 0.1 with S1's dysregulation-vs-outcome model (getFitnesses, featureSelection.dysregSurv)
# on the TCGA matrix from tcga_prepare.R.
# Usage: Rscript tcga_gabi.R <S1 code> <matrix .rds> <samples .csv> <out .json> [seed] [cores] [variant]
#
# S1's getFitnesses takes -log(p) of R's Spearman cor.test without the 2e-16 floor that its own
# featureSelection.dysregSurv and cor.fitness apply. R returns p = 0 for the seed row against itself
# and, at n = 16-21, for a band of rho below 1 (0.836-0.865 at n = 21), so every candidate with such a
# row scores Inf, which GABi sets to 0; as published the model cannot score a 21-sample bicluster.
# Variant "floor" (default) adds that floor and nothing else. Variant "floor+jprime" also maps the
# correlation features to rows before choosing the comparison columns (S1 line 123), as the
# selection function does (S1 line 166).
suppressMessages({library(survival); library(jsonlite)})
here <- dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)))
source(file.path(here, "gabi_parallel.R"))
a <- commandArgs(trailingOnly = TRUE)
seed <- if (length(a) >= 5) as.integer(a[5]) else 1L
options(gabi.cores = if (length(a) >= 6) as.integer(a[6]) else max(1L, detectCores() - 2L))
variant <- if (length(a) >= 7) a[7] else "floor"

s1 <- sub("\r$", "", readLines(a[1]))
s1 <- s1[grep("Dysregulation-vs-outcome", s1):length(s1)]
patch <- function(src, from, to) {
  hit <- which(grepl(from, src, fixed = TRUE))[1]
  if (is.na(hit)) stop("S1 text not found: ", from)
  src[hit] <- sub(from, to, src[hit], fixed = TRUE)
  src
}
s1 <- patch(s1, "function(y)-log(y$p.value)", "function(y)-log(max(c(2e-16,y$p.value)))")
if (variant == "floor+jprime")
  s1 <- patch(s1, "if(useCor) survFeatures <- cor.features", "if(useCor) survFeatures <- rowsForCor[cor.features]")
eval(parse(text = s1))
x <- readRDS(a[2])
smp <- read.csv(a[3])
stopifnot(identical(smp$sample, colnames(x)))

# The paper does not report consistency, rho or alpha; these are GABi's default consistency and
# conventional thresholds.
fa <- list(consistency = 0.8, rho = 0.5, alpha = 0.05, surv = Surv(smp$PFI.months, smp$PFI))

set.seed(seed)
t0 <- proc.time()[["elapsed"]]
log <- capture.output(res <- GABi_parallel(x, fitnessFun = getFitnesses,
                                           featureSelFun = featureSelection.dysregSurv,
                                           fitnessArgs = fa))
el <- proc.time()[["elapsed"]] - t0

sols <- lapply(res, function(s) list(samples = colnames(x)[s$samples],
                                     features = rownames(x)[s$features], score = s$score))
sols <- sols[order(-vapply(sols, `[[`, 0, "score"))]
write_json(list(seed = seed, variant = variant, seconds = el, fitness_args = fa[c("consistency", "rho", "alpha")],
                gabi_log = log, solutions = sols), a[4], auto_unbox = TRUE, digits = NA)
cat(sprintf("%d solutions in %.0f s; best: %d samples, %d features, score %.2f\n", length(sols), el,
            length(sols[[1]]$samples), length(sols[[1]]$features), sols[[1]]$score))

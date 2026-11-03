# GABi.R:7-18 drops rows whose min-max scaled mean is < 1 - diffThreshold or > diffThreshold
# before any fitness evaluation. The paper does not describe this step.
source(file.path(dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])), "common.R"))

set.seed(1)
x <- matrix(rbinom(30 * 25, 1, 0.5), 30, 25)
x[1:6, ] <- 0
x[1:6, 1:2] <- 1          # a 6 x 2 block of 1s: scaled row mean 2/25 = 0.08
x[7, ] <- c(rep(1, 23), 0, 0) # scaled mean 0.92
x[8, ] <- 1                # invariant

grab <- function(chr) {    # reads diffRows from GABi's frame, as the S1 functions do
  assign(".dr", diffRows, envir = globalenv())
  sum(chr)
}
r <- quiet(GABi(x, fitnessFun = grab, featureSelFun = function(cols) 0, popsize = 8, nsubpops = 1, maxNgens = 1))
check("03.1", setequal(.dr, 9:30), "rows 1-8 are not passed to the fitness function",
      paste("diffRows =", paste(range(.dr), collapse = "..")))
check("03.2", any(grepl("6 constantly low features and 1 constantly high", r$log)),
      "GABi prints: 6 constantly low features and 1 constantly high")
check("03.3", identical(gabi_diffRows(x), .dr), "gabi_diffRows() in common.R reproduces the filter")

# Consequence for the block model: the planted 6 x 2 block of 1s cannot be returned.
s1 <- load_s1()
fa <- list(consistency = 0.99)
f <- bind(s1$block.fitness, x, fa)
sel <- bind(s1$block.selection, x, fa)
chr <- c(1, 1, rep(0, 23))
check("03.4", f(chr) == 2 * length(sel(1:2)) && !any(1:6 %in% sel(1:2)),
      "block.selection(columns 1-2) excludes the planted rows 1-6",
      paste("selected:", length(sel(1:2)), "rows, none of 1-6"))

# On Algorithm 2 data (rows scaled to [0, 1] after adding U(0,1) background), nothing is dropped,
# so the filter does not affect the Fig 2 benchmark.
source(file.path(ANALYSIS_DIR, "reference", "paper_models.R"))
set.seed(2)
dropped <- sapply(c("block", "cor", "highvar"), function(m)
  sum(replicate(100, { d <- alg2(m); nrow(d$x) - length(gabi_diffRows(d$x)) })))
check("03.5", all(dropped == 0), "no rows dropped in 100 Algorithm 2 datasets per model",
      paste(names(dropped), dropped, collapse = ", "))
done()

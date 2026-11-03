# Why GABi.block scores low on the block datasets: Algorithm 2 draws the block offset b from
# N(0, 1), so about half the implanted blocks are lower than their rows' other values, and the block
# model only looks for high values. Splits the benchmark's GABi.block scores by the sign of b and
# reruns GABi.block at lower consistency thresholds (the paper does not give the value).
# Usage: Rscript fig2_block_check.R <S1 code> <fig2_scores.csv> <out .json> [cores]
suppressMessages({library(GABi); library(parallel); library(jsonlite)})
a <- commandArgs(trailingOnly = TRUE)
cores <- if (length(a) >= 4) as.integer(a[4]) else 2L
s1 <- sub("\r$", "", readLines(a[1])); eval(parse(text = s1))
bench <- new.env()
src <- readLines(file.path(dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE))), "fig2_benchmark.R"))
# Reuse the benchmark's dataset generator and F-measure without running the benchmark.
keep <- grep("^(make_dataset|f_measure|best_overlap) <- function", src)
for (k in keep) { end <- k; depth <- 0
  repeat { depth <- depth + lengths(regmatches(src[end], gregexpr("\\{", src[end]))) -
             lengths(regmatches(src[end], gregexpr("\\}", src[end]))); if (depth == 0) break; end <- end + 1 }
  eval(parse(text = src[k:end]), envir = bench) }

# The block offset b: replay make_dataset's draws up to its rnorm(1).
offset <- vapply(1:40, function(i) {
  set.seed(1000L + i)
  p <- sample(1:100, 1); q <- sample(2:18, 1); runif(1); runif(100 * 20); sample(100, p); sample(20, q)
  rnorm(1)
}, 0)
sc <- read.csv(a[2]); s <- sc[sc$structure == "block" & sc$method == "GABi.block", ]
s <- s[order(s$dataset), ]
by_sign <- list(b_positive = median(s$F.score[offset > 0]), b_negative = median(s$F.score[offset <= 0]),
                n_positive = sum(offset > 0))

runs <- lapply(c(0.6, 0.7, 0.8), function(cons) {
  f <- unlist(mclapply(1:40, function(i) {
    d <- bench$make_dataset("block", 1000L + i)
    set.seed(10000L + i)
    invisible(capture.output(r <- suppressWarnings(GABi(d$x, fitnessFun = block.fitness,
      featureSelFun = block.selection, fitnessArgs = list(consistency = cons)))))
    bench$best_overlap(lapply(r, function(z) list(rows = z$features, cols = z$samples)), d$I, d$J)
  }, mc.cores = cores))
  list(consistency = cons, median = median(f), q1 = unname(quantile(f, 0.25)), q3 = unname(quantile(f, 0.75)),
       median_b_positive = median(f[offset > 0]))
})
write_json(list(offset = offset, benchmark_by_sign = by_sign, consistency_runs = runs), a[3],
           auto_unbox = TRUE, digits = NA, pretty = TRUE)

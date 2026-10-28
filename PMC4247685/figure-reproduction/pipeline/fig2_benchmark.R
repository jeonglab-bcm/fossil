# Fig. 2 benchmark: Algorithm 2 datasets (paper p. 9-10) and the seven methods of Fig. 2.
# Usage: Rscript fig2_benchmark.R <S1 code> <out.csv> [cores] [datasets per model] [models]
suppressMessages({library(GABi); library(biclust); library(isa2); library(parallel)})

args <- commandArgs(trailingOnly = TRUE)
s1_path <- args[1]
out_csv <- args[2]
cores <- if (length(args) >= 3) as.integer(args[3]) else max(1L, detectCores() - 2L)
n_sets <- if (length(args) >= 4) as.integer(args[4]) else 40L
models <- if (length(args) >= 5) strsplit(args[5], ",")[[1]] else c("block", "cor", "highvar")

# S1 defines block.*, cor.*, highvar.* and the dysregulation functions; GABi() rebinds their
# environment, so x, diffRows and fitnessArgs resolve inside the GA.
s1 <- sub("\r$", "", readLines(s1_path))
eval(parse(text = s1))

# Algorithm 2 with n = 100, m = 20, p ~ U{1..100}, q ~ U{2..18}, zeta ~ U(0, 1).
make_dataset <- function(model, seed) {
  set.seed(seed)
  n <- 100; m <- 20
  p <- sample(1:100, 1); q <- sample(2:18, 1); zeta <- runif(1)
  A <- matrix(runif(n * m), n, m)
  I <- sample(n, p); J <- sample(m, q)
  if (model == "block") A[I, J] <- A[I, J] + rnorm(1)
  if (model == "cor") A[I, J] <- sweep(A[I, J, drop = FALSE], 2, rnorm(q), "+")
  if (model == "highvar") A[I, J] <- A[I, J] + matrix(rnorm(p * q), p, q)
  A <- A + matrix(rnorm(n * m, 0, zeta), n, m)
  A <- t(apply(A, 1, function(r) (r - min(r)) / (max(r) - min(r))))
  list(x = A, I = I, J = J, p = p, q = q, zeta = zeta)
}

# Eq. 45 for one set pair; 0 when the sets do not overlap.
f_measure <- function(a, b) {
  k <- length(intersect(a, b))
  if (k == 0) return(0)
  2 * (k / length(a)) * (k / length(b)) / (k / length(a) + k / length(b))
}

# Best feature-F times sample-F over the recovered biclusters (paper p. 9).
best_overlap <- function(sols, I, J) {
  if (length(sols) == 0) return(0)
  max(vapply(sols, function(s) f_measure(s$rows, I) * f_measure(s$cols, J), 0))
}

from_biclust <- function(res) {
  if (res@Number == 0) return(list())
  lapply(seq_len(res@Number), function(k)
    list(rows = which(res@RowxNumber[, k]), cols = which(res@NumberxCol[k, ])))
}

# GABi 0.1 defaults apart from fitnessArgs, which the paper does not report.
fitness_args <- list(consistency = 0.8, rho = 0.5, alpha = 0.05)

run_gabi <- function(x, model) {
  ff <- get(paste0(model, ".fitness")); fs <- get(paste0(model, ".selection"))
  invisible(capture.output(res <- suppressWarnings(
    GABi(x, fitnessFun = ff, featureSelFun = fs, fitnessArgs = fitness_args))))
  lapply(res, function(s) list(rows = s$features, cols = s$samples))
}

run_method <- function(method, x) {
  switch(method,
    GABi.block = run_gabi(x, "block"),
    GABi.cor = run_gabi(x, "cor"),
    GABi.highvar = run_gabi(x, "highvar"),
    ISA = {
      invisible(capture.output(r <- isa(x)))
      lapply(seq_len(ncol(r$rows)), function(k)
        list(rows = which(r$rows[, k] != 0), cols = which(r$columns[, k] != 0)))
    },
    CC = from_biclust(biclust(x, method = BCCC())),
    Plaid = {
      invisible(capture.output(r <- biclust(x, method = BCPlaid(), verbose = FALSE)))
      from_biclust(r)
    },
    Bimax = from_biclust(biclust(binarize(x), method = BCBimax())))
}

methods <- c("GABi.block", "GABi.cor", "GABi.highvar", "ISA", "CC", "Plaid", "Bimax")
model_seed <- c(block = 1000L, cor = 2000L, highvar = 3000L)
tasks <- expand.grid(dataset = seq_len(n_sets), model = models, method = methods,
                     stringsAsFactors = FALSE)

res <- mclapply(seq_len(nrow(tasks)), function(i) {
  t <- tasks[i, ]
  d <- make_dataset(t$model, model_seed[[t$model]] + t$dataset)
  set.seed(model_seed[[t$model]] * 10L + t$dataset * 10L + match(t$method, methods))
  el <- system.time(sols <- tryCatch(run_method(t$method, d$x), error = function(e) list()))[["elapsed"]]
  data.frame(structure = t$model, dataset = t$dataset, method = t$method, p = d$p, q = d$q,
             zeta = d$zeta, n_solutions = length(sols), F.score = best_overlap(sols, d$I, d$J),
             seconds = el)
}, mc.cores = cores, mc.preschedule = FALSE)

out <- do.call(rbind, res)
write.csv(out, out_csv, row.names = FALSE)

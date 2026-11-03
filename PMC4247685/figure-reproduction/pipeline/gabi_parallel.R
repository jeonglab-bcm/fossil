# GABi 0.1 with fitness evaluation spread over forked workers. Every call
# apply(<population>, MARGIN = 1, fitnessFun) becomes par_rows(<population>, fitnessFun); selection,
# crossover, mutation and the RNG stream are untouched because the fitness functions draw no
# random numbers.
suppressMessages({library(GABi); library(parallel)})

par_rows <- function(pop, fun, cores = getOption("gabi.cores", 1L)) {
  if (cores <= 1L || nrow(pop) < 2L) return(apply(pop, MARGIN = 1, fun))
  unlist(mclapply(seq_len(nrow(pop)), function(i) fun(pop[i, ]), mc.cores = cores,
                  mc.set.seed = FALSE))
}

GABi_parallel <- local({
  n_swapped <- 0L
  swap <- function(e) {
    if (!is.call(e)) return(e)
    if (identical(e[[1]], as.name("apply")) && length(e) == 4L &&
        identical(e[[4]], as.name("fitnessFun"))) {
      n_swapped <<- n_swapped + 1L
      return(call("par_rows", swap(e[[2]]), as.name("fitnessFun")))
    }
    for (i in seq_along(e)[-1]) if (!is.null(e[[i]])) e[[i]] <- swap(e[[i]])
    e
  }
  f <- GABi::GABi
  body(f) <- swap(body(f))
  if (n_swapped != 3L) stop("expected 3 fitness apply() calls in GABi 0.1, found ", n_swapped)
  env <- new.env(parent = asNamespace("GABi"))
  env$par_rows <- par_rows
  environment(f) <- env
  f
})

# Migration (GABi.R:195-198, exchange_sols.R). Every experiod generations GABi calls
#   exchangeSols(demes, all_fitnesses, TRUE, FALSE)
# after reproduction has already replaced each deme, so all_fitnesses belongs to the previous population.
# exchangeSols takes row argmax(old fitness) of the new deme as the migrant, and writes the incoming migrant
# over the receiving deme's row argmax(old fitness). Demes are matched by a random permutation.
source(file.path(dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])), "common.R"))

.calls <- list()
trace_ns("exchangeSols",
         tracer = quote(assign(".in", list(demes = demes, fitnesses = fitnesses), envir = globalenv())),
         exit = quote(assign(".calls", c(.calls, list(c(.in, list(out = returnValue())))), envir = globalenv())))

fa <- list(consistency = 0.8, tabu = list(features = 0, samples = 0))
stats <- NULL
for (s in 1:4) {
  set.seed(s)
  x <- matrix(rbinom(60 * 16, 1, 0.5), 60, 16)
  f <- bind(getFitnesses.basic, x, fa)
  assign(".calls", list(), envir = globalenv())
  invisible(quiet(GABi(x, fitnessFun = getFitnesses.basic, popsize = 64, maxNgens = 60, convergenceGens = 1000)))
  for (cl in .calls) for (i in seq_along(cl$demes)) {
    k <- sort(cl$fitnesses[[i]], index.return = TRUE, decreasing = TRUE)$ix[1]
    stats <- rbind(stats, data.frame(
      k = k,
      migrant_fit = f(cl$demes[[i]][k, ]),
      deme_best_prev = max(cl$fitnesses[[i]]),
      elite_overwritten = !identical(cl$out[[i]][1, ], cl$demes[[i]][1, ])))
  }
}
untrace_ns("exchangeSols")

n <- nrow(stats)
not_best <- sum(stats$migrant_fit < stats$deme_best_prev)
check("06.1", n > 0, "exchangeSols was called every experiod = 10 generations", paste(n, "deme-migrations"))
check("06.2", not_best > 0, "some migrants are not their deme's best solution (index k != 1 after a new best)",
      sprintf("%d of %d migrants below the deme's best; all of them had k != 1", not_best, n))
check("06.3", all(stats$k[stats$migrant_fit < stats$deme_best_prev] != 1), "every such migrant came from k != 1")
check("06.4", sum(stats$elite_overwritten) > 0, "the receiving deme's elite (row 1) is overwritten when its k == 1",
      sprintf("%d of %d receiving demes lost row 1", sum(stats$elite_overwritten), n))
done()

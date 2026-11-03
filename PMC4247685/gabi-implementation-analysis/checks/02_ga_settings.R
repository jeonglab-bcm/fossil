# GA settings: defaults vs the paper's "Parameter setting" text, the initial solutions (q0),
# elitism, crossover and mutation.
source(file.path(dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])), "common.R"))

fm <- formals(GABi)
check("02.1", fm$popsize == 256, "default popsize is 256 (paper p5: 128 'is sufficient')")
check("02.2", fm$nsubpops == 4 && ceiling(fm$popsize / fm$nsubpops) == 64,
      "4 subpopulations of 64 (paper p5: up to 4, each with at least 32)")
check("02.3", fm$mfreq == 1, "mutation probability per bit is mfreq/ncol(x) = 1/n (paper p6: about 1/n)")
check("02.4", fm$xfreq == 0.5 && fm$maxNgens == 200,
      "xfreq = 0.5 and maxNgens = 200 (paper p5: 0.5-1 and 100-200)")
check("02.5", fm$convergenceGens == 40 && fm$experiod == 10 && fm$identityThreshold == 0.75 &&
        fm$diffThreshold == 0.9,
      "convergenceGens 40, experiod 10, identityThreshold 0.75, diffThreshold 0.9 (no values in the paper)")
check("02.6", !"q0" %in% names(fm), "no q0 argument (Algorithm 1 input)")

# Initial solutions: record every chromosome GABi evaluates in generation 1.
.rec <- list()
recorder <- function(chr) {
  assign(".rec", c(.rec, list(chr)), envir = globalenv())
  sum(chr)
}
set.seed(1)
x <- matrix(runif(30 * 12), 30, 12)
invisible(quiet(GABi(x, fitnessFun = recorder, popsize = 32, nsubpops = 2, maxNgens = 1)))
first <- .rec[seq_len(16)] # the first deme's 16 initial solutions
check("02.7", all(vapply(first, sum, 1) == 2), "every initial solution has exactly 2 columns set (q0 fixed at 2)")

# Elitism is always on: GABi.R:183,185 pass elitism=TRUE whatever keepBest is.
seen <- logical()
trace_ns("fps", quote(assign("seen", c(seen, elitism), envir = globalenv())))
set.seed(2)
invisible(quiet(GABi(x, fitnessFun = getFitnesses.basic, keepBest = FALSE, popsize = 32, maxNgens = 3)))
untrace_ns("fps")
check("02.8", length(seen) > 0 && all(seen), "keepBest=FALSE still runs fps(elitism=TRUE)",
      paste(length(seen), "fps calls"))
pop <- matrix(rbinom(20 * 12, 1, 0.5), 20, 12)
set.seed(3)
new <- reproduction(pop, xfreq = 0, mfreq = 1, xoverpoints = 1, pinvert = 0, elitism = TRUE)
check("02.9", identical(new[1, ], as.numeric(pop[1, ])) && all(new[-1, ] == 1 - pop[-1, ]),
      "row 1 (the elite) is exempt from mutation: with flip probability 1 every other bit flips")

# Crossover: one cut point, children are a prefix of one parent and the suffix of the other.
# Algorithm 1 line 15 says "swap randomly-sampled subset of this row's values".
set.seed(4)
n <- 12
contiguous <- replicate(2000, {
  par <- rbind(rep(1, n), rep(0, n))
  ch <- crossover(par, 1, 0)
  r <- rle(ch[1, ])
  length(r$lengths) == 2
})
check("02.10", all(contiguous), "crossover output is always parent A[1:k] + parent B[(k+1):n], 1 <= k < n",
      "2000 draws, n = 12")

set.seed(5)
big <- matrix(0, 2000, 20)
rate <- mean(mutation(big, 1 / 20))
check("02.11", abs(rate - 0.05) < 0.005, "mutation flips each bit with probability mfreq/n",
      sprintf("observed %.4f for 1/20", rate))

# Convergence (GABi.R:94-108, 192-194): a generation counts as stagnant when every deme's best chromosome
# (first argmax) is identical to one of the current best chromosomes; the GA stops once convergenceGens
# such generations accumulate without a reset. With a constant fitness each elite stays in row 1, so
# the run stops at generation convergenceGens + 2, unless a migration (every experiod = 10 generations)
# moves elites between demes first, which resets the counter.
conv <- function(cg) {
  set.seed(6)
  r <- quiet(GABi(x, fitnessFun = function(chr) 1, featureSelFun = function(cols) 0,
                  convergenceGens = cg, maxNgens = 200))
  g <- grep("population convergence", r$log, value = TRUE)
  if (length(g)) as.integer(sub(".*after ([0-9]+) generations.*", "\\1", g[1])) else NA
}
g9 <- conv(9); g11 <- conv(11)
check("02.12", identical(g9, 11L) && is.na(g11),
      "constant fitness: convergenceGens 9 stops at generation 11; convergenceGens 11 runs to maxNgens = 200",
      "the migration at generation 10 resets the counter while demes hold different elites")

# With a real fitness the demes end up sharing their best solution, and the rule then triggers.
s1 <- load_s1()
source(file.path(ANALYSIS_DIR, "reference", "paper_models.R"))
gens <- vapply(1:6, function(i) {
  set.seed(i)
  d <- alg2("block")
  r <- quiet(GABi(d$x, fitnessFun = s1$block.fitness, featureSelFun = s1$block.selection,
                  fitnessArgs = list(consistency = 0.7)))
  g <- grep("population convergence", r$log, value = TRUE)
  if (length(g)) as.numeric(sub(".*after ([0-9]+) generations.*", "\\1", g[1])) else NA
}, 1)
check("02.14", all(!is.na(gens) & gens < 200), "S1 block model, defaults, 6 Algorithm 2 datasets: converges before maxNgens",
      paste("stopped at generations", paste(gens, collapse = ", ")))

# Elitism has a hole: reproduction.R:17 calls sample(setdiff(1:popsize, xindex)). When exactly one row k
# is picked for crossover, sample(k) returns a permutation of 1:k, so rows 1..k (including the elite)
# are crossed over. Likely only in small demes.
trial <- function(n) {
  pop <- matrix(rbinom(n * 12, 1, 0.5), n, 12)
  s <- .Random.seed
  one <- sum(runif(n - 1) <= 0.5) == 1 # replays reproduction's first draw
  assign(".Random.seed", s, envir = globalenv())
  np <- reproduction(pop, 0.5, 0, 1, 0, TRUE)
  c(changed = !identical(np[1, ], as.numeric(pop[1, ])), one = one)
}
set.seed(7); r8 <- replicate(3000, trial(8))
set.seed(7); r64 <- replicate(3000, trial(64))
check("02.13", sum(r8["changed", ]) > 0 && all(r8["one", r8["changed", ] == 1] == 1) && sum(r64["changed", ]) == 0,
      "elite row changed by reproduction only when exactly one row was picked for crossover",
      sprintf("deme of 8: %d of 3000 generations; deme of 64 (default): 0 of 3000", sum(r8["changed", ])))
done()

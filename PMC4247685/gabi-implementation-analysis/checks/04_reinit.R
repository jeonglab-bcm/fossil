# GABi.R:115 re-initialises a deme whose fitnesses are all 0 with
#   demes[[j]][i,sample(ncol(x),2)]==1
# a comparison, not an assignment, so the deme stays all-zero. GABi then loops ~200 times and
# returns list() with the warning "cannot find biclusters".
source(file.path(dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])), "common.R"))

fixed <- patch(GABi, "demes[[j]][i, sample(ncol(x), 2)] == 1", "demes[[j]][i, sample(ncol(x), 2)] <- 1")

# Fitness 0 for the first 16 evaluations (the whole initial deme), sum(chr) afterwards.
.calls <- 0
.sums <- numeric()
fit <- function(chr) {
  assign(".calls", .calls + 1, envir = globalenv())
  assign(".sums", c(.sums, sum(chr)), envir = globalenv())
  if (.calls <= 16) 0 else sum(chr)
}
set.seed(1)
x <- matrix(runif(20 * 10), 20, 10)
run <- function(g) {
  assign(".calls", 0, envir = globalenv())
  assign(".sums", numeric(), envir = globalenv())
  set.seed(2)
  r <- quiet(g(x, fitnessFun = fit, featureSelFun = function(cols) 0, popsize = 16, nsubpops = 1, maxNgens = 5))
  c(r, list(sums = .sums))
}
a <- run(GABi)
b <- run(fixed)
check("04.1", all(a$sums[-(1:16)] == 0), "as published: every re-initialised solution has 0 columns",
      paste(length(a$sums) - 16, "re-init evaluations, all sum(chr) == 0"))
check("04.2", length(a$value) == 0 && "cannot find biclusters" %in% a$warnings,
      "as published: returns list() with warning 'cannot find biclusters'")
check("04.3", b$sums[17] == 2 && !any(b$sums == 0) && length(b$value) > 0,
      "with '<-' instead of '==': re-initialised solutions have 2 columns and GABi returns biclusters",
      paste(length(b$value), "biclusters"))

# When does a whole deme score 0? S1 cor.fitness on 2 columns: Spearman p = 1 for n = 2, so the
# score comes only from the 'all-high' block fallback. With consistency >= 1 that fallback is off.
s1 <- load_s1()
source(file.path(ANALYSIS_DIR, "reference", "paper_models.R"))
set.seed(3)
d <- alg2("cor", p = 30, q = 8, zeta = 0.2)
fa <- list(consistency = 1, rho = 0.5, alpha = 0.05)
f <- bind(s1$cor.fitness, d$x, fa)
two <- combn(20, 2)
s2 <- apply(two, 2, function(J) { chr <- rep(0, 20); chr[J] <- 1; f(chr) })
check("04.4", all(s2 == 0), "S1 cor.fitness is 0 for all 190 two-column solutions when consistency = 1")
set.seed(4)
r <- quiet(GABi(d$x, fitnessFun = s1$cor.fitness, featureSelFun = s1$cor.selection, fitnessArgs = fa,
                popsize = 32, maxNgens = 10))
check("04.5", length(r$value) == 0 && "cannot find biclusters" %in% r$warnings,
      "GABi with S1 cor model, consistency = 1, on an Algorithm 2 'cor' dataset returns nothing")
set.seed(4)
r2 <- quiet(fixed(d$x, fitnessFun = s1$cor.fitness, featureSelFun = s1$cor.selection, fitnessArgs = fa,
                  popsize = 32, maxNgens = 10))
check("04.6", length(r2$value) == 0,
      "the '<-' fix does not help there: re-initialised solutions also have 2 columns (q0 = 2)")
done()

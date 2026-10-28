# Final output (GABi.R:208-232): every positive-fitness solution of the final population, de-duplicated
# with overlap |A n B| / min(|A|, |B|) > identityThreshold on the sample sets.
# (a) GABi.R:215 seeds keptSols with fitness=fitnesses[1] instead of fitnesses[goodsols[1]]. The loop's
#     first pass replaces that entry, so the output does not change.
# (b) The de-duplication is greedy in population order, not "rank, then filter" (Algorithm 1 lines 27-30).
source(file.path(dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])), "common.R"))

dedup_block <- find_call(body(GABi), "if (length(goodsols) > 0)")
stopifnot(!is.null(dedup_block))
run_dedup <- function(population, fitnesses, identityThreshold = 0.75) {
  e <- new.env()
  e$population <- population
  e$fitnesses <- fitnesses
  e$goodsols <- which(fitnesses > 0)
  e$keepBest <- FALSE
  e$identityThreshold <- identityThreshold
  e$keptSols <- list()
  eval(dedup_block, e)
  e$keptSols
}
cols <- function(s) which(s == 1)
sol <- function(J, m = 10) { v <- numeric(m); v[J] <- 1; v }

# (a) row 1 has fitness 0, so keptSols[[1]] starts with the wrong fitness (0).
pop <- rbind(sol(1:3), sol(4:6), sol(7:9))
k <- run_dedup(pop, c(0, 5, 7))
check("05.1", length(k) == 2 && identical(sort(vapply(k, `[[`, 1, "fitness")), c(5, 7)),
      "fitnesses[1] in the seed entry is overwritten in the first pass (stored fitnesses 5 and 7)")

fixed <- patch(GABi, "fitness = fitnesses[1])", "fitness = fitnesses[goodsols[1]])")
same <- sapply(1:5, function(s) {
  set.seed(s)
  x <- matrix(rbinom(40 * 12, 1, 0.5), 40, 12)
  set.seed(100 + s); a <- quiet(GABi(x, fitnessFun = getFitnesses.basic, popsize = 32, maxNgens = 15))$value
  set.seed(100 + s); b <- quiet(fixed(x, fitnessFun = getFitnesses.basic, popsize = 32, maxNgens = 15))$value
  c(identical(a, b), length(a))
})
check("05.2", all(same[1, ] == 1) && all(same[2, ] > 0), "GABi output identical with fitnesses[goodsols[1]] (5 seeds)",
      paste("biclusters per run:", paste(same[2, ], collapse = ",")))

# (b) B and C are disjoint; A contains both. Fitness B > C > A.
B <- sol(1:4); C <- sol(5:8); A <- sol(1:8)
f <- c(B = 10, C = 9, A = 5)
keep_names <- function(k) sort(vapply(k, function(s) names(f)[f == s$fitness], ""))
o1 <- keep_names(run_dedup(rbind(B, C, A), f[c("B", "C", "A")]))
o2 <- keep_names(run_dedup(rbind(A, B, C), f[c("A", "B", "C")]))
# rank by fitness, then keep a solution unless it overlaps one already kept
rank_filter <- function(P, fit, th = 0.75) {
  keep <- integer()
  for (i in order(fit, decreasing = TRUE)) {
    ov <- vapply(keep, function(j) sum(P[i, ] & P[j, ]) / min(sum(P[i, ]), sum(P[j, ])), 1)
    if (!any(ov > th)) keep <- c(keep, i)
  }
  sort(names(fit)[keep])
}
check("05.3", identical(o1, "B") && identical(o2, c("B", "C")),
      "code output depends on population order: order B,C,A keeps {B}; order A,B,C keeps {B,C}")
check("05.4", identical(rank_filter(rbind(B, C, A), f), c("B", "C")),
      "rank-then-filter (Algorithm 1) keeps {B,C} in either order")
done()

# MaxLoop and the tabu list (paper p6). GABi.R:37 repeats the GA only while length(allSols) <= nSols,
# so with the default nSols = 0 a second loop never runs once anything is found. GABi.R:240-247 puts the
# returned features and samples in fitnessArgs$tabu, but none of the S1 functions reads it.
source(file.path(dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])), "common.R"))

loops <- function(r) sum(grepl("initialising population for GA loop", r$log))
set.seed(1)
x <- matrix(rbinom(40 * 12, 1, 0.5), 40, 12)
x[1:10, 1:4] <- 1 # planted block
set.seed(2)
a <- quiet(GABi(x, fitnessFun = getFitnesses.basic, maxLoop = 3, popsize = 32, maxNgens = 15))
check("07.1", loops(a) == 1 && length(a$value) > 0, "maxLoop = 3 with default nSols = 0 runs the GA once",
      paste(length(a$value), "biclusters from loop 1"))
set.seed(2)
b <- quiet(GABi(x, fitnessFun = getFitnesses.basic, maxLoop = 3, nSols = 1000, popsize = 32, maxNgens = 15))
check("07.2", loops(b) == 2 && length(b$value) == 0 && "cannot find biclusters" %in% b$warnings,
      "with nSols = 1000 loop 2 starts, scores 0 everywhere (tabu), and GABi.R:146 return(list()) drops loop 1's biclusters",
      paste(length(a$value), "biclusters from loop 1 discarded"))

s1 <- load_s1()
uses_tabu <- vapply(ls(s1), function(n) "tabu" %in% all.names(body(get(n, s1))), logical(1))
check("07.3", !any(uses_tabu), "no S1 function reads fitnessArgs$tabu",
      paste(names(uses_tabu), collapse = ", "))
check("07.4", "tabu" %in% all.names(body(getFitnesses.basic)), "the package's own getFitnesses.basic does read it")

# Same scores with an empty tabu list and with every sample and feature tabu.
set.seed(4)
x2 <- matrix(runif(30 * 10), 30, 10)
surv <- Surv(rexp(10), rbinom(10, 1, 0.7))
base <- list(consistency = 0.6, rho = 0.3, alpha = 0.5, surv = surv)
chr <- c(1, 1, 1, 1, 0, 1, 0, 0, 1, 0)
score <- function(fn, tabu) suppressWarnings(bind(s1[[fn]], x2, c(base, list(tabu = tabu)))(chr))
fns <- c("block.fitness", "cor.fitness", "highvar.fitness", "getFitnesses")
same <- vapply(fns, function(fn) identical(score(fn, list(features = 0, samples = 0)),
                                           score(fn, list(features = 1:30, samples = 1:10))), logical(1))
vals <- vapply(fns, score, 1, tabu = list(features = 0, samples = 0))
check("07.5", all(same) && all(vals > 0), "S1 fitness values are unchanged when every sample and feature is tabu",
      paste(sprintf("%s=%.3g", fns, vals), collapse = ", "))

# Consequence: with nSols set, loop 2 of the S1 block model returns the same bicluster again.
set.seed(3)
r <- quiet(GABi(x, fitnessFun = s1$block.fitness, featureSelFun = s1$block.selection,
                fitnessArgs = list(consistency = 0.99), maxLoop = 2, nSols = 1000, popsize = 64, maxNgens = 30))
key <- vapply(r$value, function(s) paste(s$samples, collapse = ","), "")
check("07.6", loops(r) == 2 && any(duplicated(key)), "S1 block model: loop 2 re-finds a loop-1 bicluster",
      paste("duplicated sample sets:", paste(unique(key[duplicated(key)]), collapse = " | ")))
done()

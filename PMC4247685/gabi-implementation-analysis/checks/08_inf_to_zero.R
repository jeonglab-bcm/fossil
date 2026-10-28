# GABi.R:79,88,209 set infinite (and NA) fitness to 0, so a solution whose score overflows is never
# selected or returned. S1 getFitnesses computes h as -log(1 - pchisq(chisq, 1)), which is Inf once the
# logrank chi-square exceeds about 70.1 (1 - pchisq rounds to 0).
source(file.path(dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])), "common.R"))

# (a) Any solution containing column 1 scores Inf.
set.seed(1)
x <- matrix(runif(20 * 12), 20, 12)
f_inf <- function(chr) if (chr[1] == 1) Inf else sum(chr)
set.seed(2)
r <- quiet(GABi(x, fitnessFun = f_inf, featureSelFun = function(cols) 0, popsize = 32, maxNgens = 10))
has1 <- vapply(r$value, function(s) 1 %in% s$samples, logical(1))
check("08.1", length(r$value) > 0 && !any(has1), "Inf-scoring solutions are treated as fitness 0 and never returned",
      paste(length(r$value), "biclusters, none containing column 1"))

# (b) Threshold at which -log(1 - pchisq(q, 1)) becomes Inf.
lo <- 50; hi <- 100
for (i in 1:60) { mid <- (lo + hi) / 2; if (1 - pchisq(mid, 1) == 0) hi <- mid else lo <- mid }
q0 <- hi
check("08.2", is.infinite(-log(1 - pchisq(q0 + 0.1, 1))) && is.finite(-pchisq(q0 + 0.1, 1, lower.tail = FALSE, log.p = TRUE)),
      sprintf("-log(1 - pchisq(q, 1)) = Inf for q > %.2f (logrank p < %.1e); the log.p form stays finite",
              q0, pchisq(q0, 1, lower.tail = FALSE)))

# (c) S1 dysregulation model with perfect survival separation between J and J'.
s1 <- load_s1()
set.seed(3)
n <- 200; J <- 1:100
xd <- matrix(runif(20 * n), 20, n)
xd[1:5, J] <- runif(5 * 100, 0.95, 1)   # consistently high on J: block branch
xd[6:20, J] <- runif(15 * 100, 0, 0.05) # low on J: excluded from both branches (see 11_dysreg_model.R)
time <- c(1:100, 1001:1100); event <- rep(1, n)
fa <- list(consistency = 0.8, rho = 0.5, alpha = 0.05, surv = Surv(time, event))
g <- bind(s1$getFitnesses, xd, fa)
chr <- as.numeric(seq_len(n) %in% J)
chisq <- survdiff(Surv(time, event) ~ chr)$chisq
check("08.3", is.infinite(g(chr)), "S1 getFitnesses returns Inf for a perfectly separated outcome, so GABi scores it 0",
      sprintf("logrank chisq = %.0f; log.p form would give h = %.1f", chisq,
              -pchisq(chisq, 1, lower.tail = FALSE, log.p = TRUE)))
done()

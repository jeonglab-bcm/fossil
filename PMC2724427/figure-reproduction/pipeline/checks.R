# Two checks of the logitbias package against the paper.
#   Rscript checks.R PER_N_CSV FIT_JSON OUT_JSON
# 1. Port check: simulate_population() against the R lines of Additional file 1, typed here as
#    printed there, on the same seed (the population must be identical).
# 2. The kernel-regression check of the Methods: a local plug-in kernel estimate of the mean
#    coefficient against n and of its first derivative (lokern::lokerns, the "kernel regression
#    estimators and automatically adapted local plug-in bandwidth" the paper describes), compared
#    with the derivative of the fitted curve beta + b1/n, which is -b1/n^2.
suppressPackageStartupMessages({library(logitbias); library(lokern)})
a <- commandArgs(TRUE)
s <- read.csv(a[1])
out <- a[3]
seed <- 2724427L

# --- 1. port check -------------------------------------------------------------------------
set.seed(seed)
x <- rnorm(100000, 2, 0.7)
z <- ifelse(x>2.5, rbinom(100000, 1, 0.6), rbinom(100000, 1, 0.4))
theta <- 0.1 + 2*x - 0.9*z
y <- ifelse(runif(100000) < plogis(theta), 1, 0)
simdata <- data.frame(y, x, z)
pop <- simulate_population(100000, seed = seed)
same <- identical(pop, simdata)
one <- simdata[sample(100000, 500),]  # the supplement's sampling line, for the record
port <- list(passed = same, detail = sprintf(
  "simulate_population(seed = %d) is identical to the R lines of Additional file 1 run on the same seed (100,000 rows: x, z and y all equal)%s",
  seed, if (same) "" else "; NOT identical"))

# --- 2. kernel derivative --------------------------------------------------------------------
fit <- fit_bias_curve(s, "means")
kern <- lapply(c(x = "x", z = "z"), function(tm) {
  d <- s[s$term == tm, ]
  b1 <- fit$estimate[fit$term == tm & fit$param == "inv_n"]
  b0 <- fit$estimate[fit$term == tm & fit$param == "intercept"]
  k0 <- lokerns(d$n, d$mean, deriv = 0, x.out = d$n)
  k1 <- lokerns(d$n, d$mean, deriv = 1, x.out = d$n)
  inner <- d$n >= 150 & d$n <= 1400
  par1 <- -b1 / d$n^2
  same_sign <- all(sign(k1$est[inner]) == sign(par1[inner]))
  ok <- inner & sign(k1$est) == sign(par1) & k1$est != 0
  slope <- if (sum(ok) > 10) unname(coef(lm(log(abs(k1$est[ok])) ~ log(d$n[ok])))[2]) else NA
  list(term = tm, n = d$n, kernel = k0$est, kernel_deriv = k1$est, parametric = b0 + b1 / d$n,
       parametric_deriv = par1, same_sign_150_1400 = same_sign, loglog_slope = slope,
       max_abs_gap = max(abs(k0$est - (b0 + b1 / d$n))),
       median_se_of_mean = median(d$sd / sqrt(d$used)))
})
num <- function(v) paste0("[", paste(format(signif(v, 12), digits = 12, trim = TRUE), collapse = ", "), "]")
kj <- vapply(kern, function(k) sprintf(
  '{"term": "%s", "same_sign_150_1400": %s, "loglog_slope": %s, "max_abs_gap": %s, "median_se_of_mean": %s, "n": %s, "kernel": %s, "kernel_deriv": %s, "parametric": %s, "parametric_deriv": %s}',
  k$term, tolower(k$same_sign_150_1400), format(signif(k$loglog_slope, 12)), format(signif(k$max_abs_gap, 12)),
  format(signif(k$median_se_of_mean, 12)), num(k$n), num(k$kernel), num(k$kernel_deriv), num(k$parametric),
  num(k$parametric_deriv)), "")
writeLines(sprintf('{"port": {"passed": %s, "detail": "%s"},\n "kernel": [%s],\n "lokern": "%s"}',
                   tolower(port$passed), port$detail, paste(kj, collapse = ",\n  "),
                   as.character(packageVersion("lokern"))), out)
cat("port", same, "\n")
for (k in kern) cat(k$term, "same sign", k$same_sign_150_1400, "slope", round(k$loglog_slope, 3), "\n")

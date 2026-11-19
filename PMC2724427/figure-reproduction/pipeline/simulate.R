# Run the simulation study of Nemes et al. (2009) with the logitbias package.
#   Rscript simulate.R OUTDIR [--seed S] [--cores C] [--light] [--x-sd SD --tag TAG]
# Writes OUTDIR/per_n.csv (per sample size and coefficient), OUTDIR/samples_fig.csv (every
# estimate at the six sizes of Figs 2 and 3) and OUTDIR/fit.json (Table 1 both ways, the
# population fit, the analytic first-order bias, the separation counts). With --light only
# fit.json is written, named seed_<S>.json (the seed-spread runs), or <TAG>_seed_<S>.json for a
# hypothesis test that changes the population (--x-sd: standard deviation of x).
suppressPackageStartupMessages(library(logitbias))
args <- commandArgs(TRUE)
out <- args[1]
opt <- function(name, default) { i <- match(name, args); if (is.na(i)) default else args[i + 1] }
seed <- as.integer(opt("--seed", "2724427"))
cores <- as.integer(opt("--cores", "1"))
light <- "--light" %in% args
x_sd <- as.numeric(opt("--x-sd", "0.7"))
tag <- opt("--tag", "")
dir.create(out, showWarnings = FALSE, recursive = TRUE)
fig_sizes <- c(100, 150, 300, 500, 750, 1000)

t0 <- proc.time()[["elapsed"]]
pop <- simulate_population(100000, seed = seed, x_sd = x_sd)
X <- cbind(1, pop$x, pop$z)
popfit <- glm.fit(X, pop$y, family = binomial())$coefficients
sim <- bias_simulation(pop, sizes = seq(100, 1500, 5), reps = 1000, seed = seed,
                       keep = if (light) NULL else fig_sizes, cores = cores)
s <- sim$summary
curve_means <- fit_bias_curve(s, "means")
curve_all <- fit_bias_curve(s, "all")
# Sensitivity of Table 1 to the rule for samples without a finite estimate: leave out only the
# fits R warns about, or keep every fit
s_warn <- s; s_warn$mean <- s_warn$mean_warning
s_keep <- s; s_keep$mean <- s_keep$mean_all
curve_warn <- fit_bias_curve(s_warn, "means")
curve_keepall <- fit_bias_curve(s_keep, "means")
six <- s[s$n %in% fig_sizes, c("n", "term", "mean", "sd", "median", "q1", "q3", "skewness", "used", "dropped")]
res <- list(
  seed = seed, x_sd = x_sd, population = list(N = nrow(pop), prevalence = mean(pop$y), p_x_gt_2_5 = mean(pop$x > 2.5),
                                 glm = setNames(as.list(unname(popfit)), c("intercept", "x", "z"))),
  analytic_b1 = list(at_population_fit = as.list(analytic_bias(pop)),
                     at_true_beta = as.list(analytic_bias(pop, c(0.1, 2, -0.9)))),
  table1 = list(means = curve_means, all = curve_all, means_warning_rule = curve_warn, means_every_fit_kept = curve_keepall),
  dropped = list(total = sum(s$dropped[s$term == "x"]), boundary = sum(s$boundary[s$term == "x"]), separated = sum(s$separated[s$term == "x"]),
                 not_converged = sum(s$not_converged[s$term == "x"]),
                 largest_n_with_drop = if (any(s$dropped > 0)) max(s$n[s$dropped > 0]) else NA,
                 by_n = s[s$term == "x" & s$dropped > 0, c("n", "dropped", "boundary", "separated", "not_converged")]),
  six_sizes = six)
secs <- round(proc.time()[["elapsed"]] - t0, 1)  # printed only, so a rerun writes the same files
num <- function(x) if (is.numeric(x)) signif(x, 15) else x
tojson <- function(x, ind = "") {
  nx <- paste0(ind, " ")
  if (is.data.frame(x)) return(tojson(lapply(seq_len(nrow(x)), function(i) as.list(x[i, , drop = FALSE])), ind))
  if (is.list(x)) {
    if (!is.null(names(x)) && all(names(x) != "")) {
      body <- vapply(names(x), function(k) paste0(nx, '"', k, '": ', tojson(x[[k]], nx)), "")
      return(paste0("{\n", paste(body, collapse = ",\n"), "\n", ind, "}"))
    }
    body <- vapply(x, function(v) paste0(nx, tojson(v, nx)), "")
    return(paste0("[\n", paste(body, collapse = ",\n"), "\n", ind, "]"))
  }
  if (length(x) == 0 || (length(x) == 1 && is.na(x))) return("null")
  if (length(x) > 1) return(paste0("[", paste(vapply(x, tojson, ""), collapse = ", "), "]"))
  if (is.character(x)) return(paste0('"', x, '"'))
  if (is.logical(x)) return(tolower(as.character(x)))
  format(num(x), digits = 15)
}
if (light) {
  res$six_sizes <- six[, c("n", "term", "mean", "sd", "median", "q1", "q3", "skewness")]
  writeLines(tojson(res), file.path(out, sprintf("%sseed_%d.json", if (nzchar(tag)) paste0(tag, "_") else "", seed)))
} else {
  writeLines(tojson(res), file.path(out, "fit.json"))
  w <- function(d, f) write.csv(data.frame(lapply(d, num)), file.path(out, f), row.names = FALSE)
  w(s, "per_n.csv")
  w(sim$samples, "samples_fig.csv")
}
cat(sprintf("seed %d: %.1f s\n", seed, secs))

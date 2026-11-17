# Every simulation setting of the reproduction (PMC3098087, Blagus and Lusa 2010).
# Each setting is one call of multds::simulation_settings(); its name sets its random seeds.
suppressPackageStartupMessages(library(multds))

K19 <- round(seq(0.05, 0.95, by = 0.05), 2)
K_RIGHT <- c(round(seq(0.05, 0.5, by = 0.05), 2), 0.95)   # Fig. 3 right panels
MU_GRID <- c(0, round(seq(0.1, 2, by = 0.1), 1), 3)        # Fig. 4 (read from the figure)
NINE <- classifier_names()
ALL <- classifier_names(thr = TRUE)
CHEAP <- c("1-NN", "3-NN", "5-NN", "DLDA", "DQDA", "PLR")
bal <- function(n) list(id = paste0("bal", n), ntest = n, k1test = 0.5)

all_settings <- function() {
  s <- list()
  # Replicates: 1,000 as in the paper for the settings behind the printed tables and Fig. 1
  # (null, p = 40; alternative, p = 1000, which is also Fig. 5's first column); 500 for every other
  # setting, to fit the compute budget. The comparison's Monte Carlo tolerance uses our SDs and counts.
  add <- function(family, x) {
    x$family <- family
    x$reps <- if (family == "hyp") 200L else if (grepl("^(null_p40|alt20_p1000)_", x$name)) 1000L else 500L
    s[[x$name]] <<- x
  }
  for (k in K19) {
    # Null case, p = 40, all variables (Fig. 1, Additional file 1, Fig. 2 p = 40).
    add("null", simulation_settings(sprintf("null_p40_k%.2f", k), p = 40, k1train = k, G = 40,
        tests = list(list(id = "match20", ntest = 20, k1test = k), bal(20), bal(500)), methods = ALL))
    for (p in c(1000, 10000))
      add("null", simulation_settings(sprintf("null_p%d_k%.2f", p, k), p = p, k1train = k, G = 40,
          tests = list(bal(20)), methods = ALL))
    # Alternative, pDE = 20, mu2 = 1 (Fig. 3 left, Additional files 3, 4, 11; Fig. 5 first column).
    for (p in c(40, 1000, 10000))
      add("alt20", simulation_settings(sprintf("alt20_p%d_k%.2f", p, k), p = p, p_de = 20, mu2 = 1,
          k1train = k, G = 40, tests = if (p == 1000) list(bal(20), bal(500)) else list(bal(20)),
          methods = ALL))
    # Corrections, p = 1000 (Fig. 5, Additional files 8 and 10).
    for (corr in c("over", "down"))
      add("corr", simulation_settings(sprintf("%s_p1000_k%.2f", corr, k), p = 1000, p_de = 20, mu2 = 1,
          k1train = k, G = 40, tests = list(bal(20), bal(500)), correction = corr, methods = NINE))
    add("multds", simulation_settings(sprintf("multds_p1000_k%.2f", k), p = 1000, p_de = 20, mu2 = 1,
        k1train = k, G = 40, tests = list(bal(20), bal(500)), correction = "multds", methods = CHEAP))
  }
  # Over-sampling, then centred variables (Additional file 9), test balanced or as imbalanced as training.
  for (k in K19)
    add("af9", simulation_settings(sprintf("af9_p1000_k%.2f", k), p = 1000, p_de = 20, mu2 = 1, k1train = k, G = 40,
        tests = list(bal(20), list(id = "match20", ntest = 20, k1test = k)), center = "variables",
        correction = "over", methods = NINE))
  # Alternative, pDE = p (Fig. 3 right, Additional file 5).
  for (k in K_RIGHT) for (p in c(40, 1000, 10000))
    add("altall", simulation_settings(sprintf("altall_p%d_k%.2f", p, k), p = p, p_de = p, mu2 = 1,
        k1train = k, G = 40, tests = list(bal(20)), methods = NINE))
  # Hypothesis test (not our result): the alternative case of Fig. 3 and Additional files 4 and 5
  # without centring the samples, 200 replicates each.
  for (k in K19) add("hyp", simulation_settings(sprintf("nocenter_alt20_p40_k%.2f", k), p = 40, p_de = 20, mu2 = 1,
      k1train = k, G = 40, center = "none", tests = list(bal(20)), methods = NINE))
  for (k in K_RIGHT) for (p in c(40, 1000, 10000))
    add("hyp", simulation_settings(sprintf("nocenter_altall_p%d_k%.2f", p, k), p = p, p_de = p, mu2 = 1,
        k1train = k, G = 40, center = "none", tests = list(bal(20)), methods = NINE))
  # Difference between classes and normalization (Fig. 4, Additional file 7).
  for (ctr in c("samples", "variables")) for (k in c(0.5, 0.6, 0.7, 0.8, 0.9)) for (mu in MU_GRID)
    add("mu", simulation_settings(sprintf("mu_%s_k%.1f_mu%.1f", ctr, k, mu), p = 1000, p_de = 20,
        mu2 = mu, k1train = k, G = 40, center = ctr, tests = list(bal(20)), methods = NINE))
  s
}

# One chunk of the simulation study (Figs 2 and 3): simulate the paper's data sets and run
# epiForest and the comparators on each, writing one JSON line per data set.
#
# usage: Rscript sim_study.R MODEL MAF R2 FIRST LAST OUT.jsonl [--methods chisq,lr,ef] [--ntree N]
#
# Every data set has its own seed (model * 100000 + MAF index * 10000 + r2 index * 1000 + rep), so
# chunks can run in any order and any one data set can be rerun alone. The method is the package
# epiforest (PMC2648748/package); this script only records what each method found.
suppressPackageStartupMessages({ library(epiforest); library(jsonlite) })
args <- commandArgs(trailingOnly = TRUE)
model <- as.integer(args[1]); maf <- as.numeric(args[2]); r2 <- as.numeric(args[3])
first <- as.integer(args[4]); last <- as.integer(args[5]); out <- args[6]
methods <- c("chisq", "lr", "ef")
if (length(args) >= 8 && args[7] == "--methods") methods <- strsplit(args[8], ",")[[1]]

LAMBDA <- c(0.3, 0.5, 1.0)
MAFS <- c(0.05, 0.1, 0.2, 0.5)
R2S <- c(0.7, 1.0)
ALPHA <- 0.05
L <- 1000

seed_of <- function(rep) model * 100000 + match(maf, MAFS) * 10000 + match(r2, R2S) * 1000 + rep

# smallest adjusted p over reported-or-not tests that contain SNP s, by order
min_p <- function(tests, s, col = "p_adj") {
  out <- c(NA, NA, NA)
  for (o in 1:3) {
    sub <- tests[tests$order == o, , drop = FALSE]
    if (!nrow(sub)) next
    has <- vapply(strsplit(sub$snps, ","), function(z) s %in% as.integer(z), TRUE)
    if (any(has)) out[o] <- min(sub[[col]][has])
  }
  out
}

# resume: skip data sets already written to OUT (a killed run leaves complete lines only)
done <- integer(0)
if (file.exists(out)) {
  lines <- readLines(out, warn = FALSE)
  lines <- lines[nzchar(lines)]
  done <- vapply(lines, function(l) tryCatch(fromJSON(l)$rep, error = function(e) NA_integer_), 1L)
}
ntree <- 500
if (length(args) >= 10 && args[9] == "--ntree") ntree <- as.integer(args[10])
con <- file(out, open = "a")
for (rep in setdiff(first:last, done)) {
  seed <- seed_of(rep)
  set.seed(seed, kind = "Mersenne-Twister", normal.kind = "Inversion", sample.kind = "Rejection")
  d <- simulate_dataset(model, LAMBDA[model], maf, r2, prevalence = 0.1, n_markers = L)
  dis <- d$disease
  rec <- list(model = model, maf = maf, r2 = r2, rep = rep, seed = seed, disease = dis)
  if ("chisq" %in% methods) {
    cs <- chisq_single(d$geno, d$status)
    rec$chisq <- list(p = cs$p[dis], found = (cs$p[dis] * L) < ALPHA)
  }
  if ("lr" %in% methods) {
    lr <- stepwise_lr(d$geno, d$status, eps = 0.1, alpha = ALPHA, max_order = 3, focus = dis)
    kept <- attr(lr, "kept")
    m <- vapply(dis, function(s) min_p(lr, s, "p"), numeric(3))      # raw p, rows = order
    found <- vapply(dis, function(s) s %in% identified_snps(lr), TRUE)
    rec$lr <- list(kept = dis %in% kept, p1 = m[1, ], p2min = m[2, ], p3min = m[3, ],
                   m2 = choose(length(kept), 2), m3 = choose(length(kept), 3), found = found)
  }
  if ("ef" %in% methods) {
    t0 <- proc.time()[["elapsed"]]
    ef <- epiforest(d$geno, d$status, ntree = ntree, window = 20, alpha = ALPHA, max_order = 3)
    cand <- ef$candidates
    # variant: Bonferroni over the candidates instead of all L markers
    hv <- hierarchical_tests(d$geno[, cand, drop = FALSE], d$status, n_markers = length(cand),
                             alpha = ALPHA, max_order = 3)
    found_l <- dis %in% cand[identified_snps(hv)]
    rep_tests <- ef$tests[ef$tests$reported, , drop = FALSE]
    joint <- any(vapply(strsplit(rep_tests$snps, ","), function(z) all(dis %in% as.integer(z)), TRUE))
    one_way <- vapply(dis, function(s) any(rep_tests$order == 1 & rep_tests$snps == as.character(s)), TRUE)
    rec$ef <- list(k = ef$swsfs$k, forests = ef$swsfs$forests,
                   errors = round(ef$swsfs$errors, 6),
                   rank = match(dis, ef$order), gini = unname(ef$gini[dis]),
                   in_candidates = dis %in% cand,
                   found = dis %in% ef$identified, found_joint = joint, found_one_way = one_way,
                   found_bonf_candidates = found_l,
                   n_identified = length(ef$identified),
                   n_false = length(setdiff(ef$identified, dis)),
                   seconds = round(proc.time()[["elapsed"]] - t0, 1))
  }
  writeLines(toJSON(rec, auto_unbox = TRUE, digits = NA), con)
  flush(con)
}
close(con)

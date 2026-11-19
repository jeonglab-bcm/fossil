# Every model, table and claim of Szabo et al. (2004), computed with the package hkselect from the
# paper's data (breast.csv) and Vandesompele et al.'s (vandesompele.csv).
#
#   Rscript analysis.R DATA_DIR OUT_DIR
#
# Writes OUT_DIR/analysis.json (all numbers) and OUT_DIR/fig3_bars.csv (bias and variance of each
# gene in each tissue type, for Fig. 3). Numbers are rounded to 10 significant digits so that a
# rerun on another machine writes the same file.
suppressPackageStartupMessages({ library(hkselect); library(nlme); library(jsonlite) })
args <- commandArgs(TRUE)
data_dir <- args[1]; out <- args[2]
dir.create(out, showWarnings = FALSE, recursive = TRUE)
sig10 <- function(x) if (is.numeric(x)) signif(x, 10) else x
r10 <- function(o) if (is.list(o)) lapply(o, r10) else sig10(o)

b <- read_expression(file.path(data_dir, "breast.csv"))
B <- b$expr
res <- list()

# ---- Model 1 (breast cancer, one tissue type)
f1 <- fit_model1(B, "gene")
sd <- gene_sd(f1)
ci <- gene_sd_ci(B)
res$model1 <- list(sd = as.list(sd), ci = lapply(split(ci[c("lower", "upper")], ci$gene), as.list),
                   bic = list(m1a = BIC(f1), m1b = BIC(fit_model1(B, "common")), m1c = BIC(fit_model1(B, "exchangeable"))),
                   rho_1c = unname(coef(fit_model1(B, "exchangeable")$modelStruct$corStruct, unconstrained = FALSE)))
ml <- tryCatch(gene_sd(fit_model1(B, "gene", method = "ML")), error = function(e) conditionMessage(e))
res$model1$ml <- if (is.character(ml)) list(error = ml) else as.list(ml)

# nlme's intervals() for each gene as the reference level of varIdent, under two contrast codings
# and two row orders: 24 equivalent parameterizations of Model 1a.
spread <- list()
genes <- colnames(B)
for (ct in c("contr.treatment", "contr.sum")) {
  op <- options(contrasts = c(ct, "contr.poly"))
  for (layout in c("gene_major", "sample_major")) for (g0 in genes) {
    gg <- c(g0, setdiff(genes, g0))
    d <- data.frame(sample = factor(rep(rownames(B), 6)), gene = factor(rep(gg, each = nrow(B)), levels = genes),
                    y = log(as.vector(B[, gg])))
    if (layout == "sample_major") d <- d[order(d$sample, match(d$gene, gg)), ]
    f <- gls(y ~ sample + gene, data = d, weights = varIdent(form = ~ 1 | gene))
    iv <- intervals(f, which = "var-cov")$sigma
    spread[[length(spread) + 1]] <- data.frame(contrasts = ct, layout = layout, gene = g0,
                                               lower = unname(iv[1]), upper = unname(iv[3]))
  }
  options(op)
}
spread <- do.call(rbind, spread)
res$model1$nlme_intervals <- lapply(split(spread, spread$gene), function(s)
  list(lower_min = min(s$lower), lower_max = max(s$lower), upper_min = min(s$upper), upper_max = max(s$upper), runs = nrow(s)))

# Table 2: both set-variance divisors; checks on the six-gene row
bs2 <- best_sets(sd, "size2"); bs1 <- best_sets(sd, "size")
res$table2 <- list(size2 = list(genes = bs2$genes, sd = bs2$sd), size = list(genes = bs1$genes, sd = bs1$sd))
row6 <- c()
for (ct in c("contr.treatment", "contr.sum")) {
  op <- options(contrasts = c(ct, "contr.poly"))
  for (g0 in genes) for (tol in c(1e-6, 1e-4, 1e-3)) {
    gg <- c(g0, setdiff(genes, g0))
    d <- data.frame(sample = factor(rep(rownames(B), 6)), gene = factor(rep(gg, each = nrow(B)), levels = genes),
                    y = log(as.vector(B[, gg])))
    f <- tryCatch(gls(y ~ sample + gene, data = d, weights = varIdent(form = ~ 1 | gene),
                      control = glsControl(tolerance = tol, msTol = tol, returnObject = TRUE)), error = function(e) NULL)
    if (!is.null(f)) row6 <- c(row6, set_sd(gene_sd(f), genes))
  }
  options(op)
}
t1_printed <- c(MRPL19 = 0.218, PUM1 = 0.265, PSMC4 = 0.288, SF3A1 = 0.393, ACTB = 0.448, GAPD = 0.519)
res$table2$row6_checks <- list(
  optimizer_min = min(row6), optimizer_max = max(row6), optimizer_runs = length(row6),
  from_printed_table1 = set_sd(t1_printed, names(t1_printed)),
  truncated = floor(bs2$sd * 1e4) / 1e4)

# p = 0.0014: microarray-selected genes against GAPD and ACTB
grp <- ifelse(genes %in% c("GAPD", "ACTB"), "classic", "microarray")
vt <- variance_group_test(B, grp)
res$group_test <- list(statistic = vt$statistic, df = vt$df, p = vt$p.value)
# Other readings of "a direct comparison", recorded as the alternatives tried
res$group_test$alternatives <- list(
  common_vs_two_groups = {
    d <- as_long(B); d$grp <- factor(grp[as.integer(d$gene)])
    full <- gls(y ~ sample + gene, data = d, weights = varIdent(form = ~ 1 | grp))
    pchisq(as.numeric(2 * (logLik(full) - logLik(fit_model1(B, "common")))), 1, lower.tail = FALSE)
  },
  t_test_on_sd = t.test(sd[grp == "microarray"], sd[grp == "classic"], var.equal = TRUE)$p.value,
  t_test_on_log_sd = t.test(log(sd[grp == "microarray"]), log(sd[grp == "classic"]), var.equal = TRUE)$p.value)

g <- genorm(B)
res$genorm_breast <- list(gene = g$gene, rank = g$rank, m = g$m)

# The M-value bounds of the paper: printed with sigma_j^2, derived with sigma_j
Rr <- max(outer(sd, sd, "/"))
Mmod <- sapply(genes, function(j) mean(sqrt(sd[j]^2 + sd[setdiff(genes, j)]^2)))
res$mvalue_bounds <- list(
  R = Rr, model_m = as.list(Mmod),
  holds_with_sigma = all(sd * sqrt(1 + 1 / Rr^2) <= Mmod & Mmod <= sd * sqrt(1 + Rr^2)),
  holds_with_sigma2_as_printed = all(sd^2 * sqrt(1 + 1 / Rr^2) <= Mmod & Mmod <= sd^2 * sqrt(1 + Rr^2)))
# "These standard deviation values are approximately equal to the coefficient of variation"
cv <- sqrt(exp(bs2$sd^2) - 1)
res$cv_check <- list(sd = bs2$sd, cv = cv, max_rel_diff = max(abs(cv / bs2$sd - 1)))

# ---- Model 2 (Vandesompele et al.'s data, five tissue types)
v <- read_expression(file.path(data_dir, "vandesompele.csv"))
V <- v$expr; tis <- factor(as.character(v$tissue), levels = c("BM", "FIB", "LEU", "NB", "POOL"))
f2 <- fit_model2(V, tis)
comp <- model2_components(f2)
res$model2 <- list(sigma = as.list(comp$sigma), varsigma = as.list(comp$varsigma), bic = comp$bic,
                   bias = lapply(split(comp$bias, row(comp$bias)), function(r) as.list(setNames(r, colnames(comp$bias)))))
names(res$model2$bias) <- rownames(comp$bias)
res$model2$competitors_bic <- lapply(c(common = "common", gene = "gene", tissue = "tissue",
                                       unstructured = "unstructured", exchangeable = "exchangeable"),
                                     function(s) tryCatch(BIC(fit_model2(V, tis, s)), error = function(e) NA))

m <- gene_mse(comp)
write.csv(data.frame(gene = m$gene, tissue = m$tissue, bias = sig10(m$bias), variance = sig10(m$variance)),
          file.path(out, "fig3_bars.csv"), row.names = FALSE)
res$fig3 <- list(gene = m$gene, tissue = m$tissue, bias2 = m$bias2, variance = m$variance, sign = sign(m$bias))

set_rows <- function(ms) list(genes = ms$genes, mse = ms$mse)
res$table4 <- list(sum_nested = set_rows(minimax_sets(comp, "sum", TRUE)),
                   sum_exact = set_rows(minimax_sets(comp, "sum", FALSE)),
                   mean_nested = set_rows(minimax_sets(comp, "mean", TRUE)))
# Sensitivity variant (not a reproduction): the same search with the paper's Table 3 standard
# deviations in place of ours, to see how much of the Table 4 difference they explain.
pub <- comp
pub$sigma[] <- c(ACTB = 0.460, B2M = 0.562, GAPD = 0.211, HMBS = 0.431, HPRT1 = 0.227, RPL13A = 0.339,
                 SDHA = 0.255, TBP = 0.339, UBC = 0.226, YWHAZ = 0.232)[names(pub$sigma)]
pub$varsigma[] <- c(BM = 1, FIB = 1.204, LEU = 1.879, NB = 1.582, POOL = 2.014)[names(pub$varsigma)]
res$table4$variant_published_table3 <- set_rows(minimax_sets(pub, "sum", TRUE))

pair <- c("ACTB", "TBP")
res$actb_tbp <- list(
  pool_sum = unname(attr(set_mse(comp, pair, "sum"), "by_tissue")["POOL"]),
  pool_mean = unname(attr(set_mse(comp, pair, "mean"), "by_tissue")["POOL"]),
  individual = as.list(setNames(m$mse[m$tissue == "POOL" & m$gene %in% pair], m$gene[m$tissue == "POOL" & m$gene %in% pair])),
  bias = as.list(comp$bias["POOL", pair]))

mr <- genorm_mean_rank(V, tis)
res$genorm_tissues <- list(gene = names(mr), mean_rank = unname(mr),
                           model2_order = names(sort(comp$sigma)))

writeLines(toJSON(r10(res), auto_unbox = TRUE, pretty = TRUE, digits = NA), file.path(out, "analysis.json"))
cat("analysis.json written\n")

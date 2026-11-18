# The models of Huang et al. 2014: the pathway-based genomic model (Table 2, Figs 3 and 4), the
# clinical and combined models (Table 2, Fig. 6), the per-set gene- and pathway-based models
# (Fig. 5), leave-one-out evaluations (Figs S2 and S4), pathway subsampling (Fig. S1) and NKI70
# (Fig. S3).
#   Rscript models.R DATA_DIR PDS_DIR OUT_DIR CORES MODE [COMMITTED_DIR] [NKI70_RDA]
# MODE full: every cross-validation run is computed (about 3 hours on 4 cores).
# MODE check: the penalties of the committed runs (COMMITTED_DIR/models/lambdas.json) are used, and
#   the first CHECK_RUNS runs of each model are recomputed and must equal them.
suppressPackageStartupMessages({library(pdscox); library(survival); library(jsonlite)})
a <- commandArgs(TRUE)
dd <- a[1]; pd <- a[2]; out <- a[3]; cores <- as.integer(a[4]); mode <- a[5]
committed <- if (length(a) >= 6) a[6] else NA
nki_rda <- if (length(a) >= 7) a[7] else NA
RUNS <- 250; S1_RUNS <- 25; S1_REPS <- 18; CHECK_RUNS <- 2
dir.create(file.path(out, "curves"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(out, "models"), recursive = TRUE, showWarnings = FALSE)

sets <- c("miller", "pawitan", "ivshina", "desmedt")
D <- lapply(setNames(sets, sets), function(s) readRDS(file.path(dd, paste0(s, ".rds"))))
for (s in sets) {
  cl <- D[[s]]$clin
  # Two Miller patients have a relapse status but no time; the paper counts their time as 0.
  cl$time[is.na(cl$time)] <- 0
  if (!is.null(cl$p53)) cl$p53[is.na(cl$p53)] <- 0
  D[[s]]$clin <- cl
}
read_pds <- function(s) {
  t <- read.csv(file.path(pd, paste0(s, ".csv")), check.names = FALSE)
  m <- as.matrix(t[, -(1:2)]); rownames(m) <- t$pathway
  t(m)
}
P <- lapply(setNames(sets, sets), read_pds)
common <- Reduce(intersect, lapply(P, colnames))
genes_all <- rownames(D$miller$expr)

committed_lambdas <- if (mode == "check") fromJSON(file.path(committed, "models", "lambdas.json")) else list()
lambda_log <- list(); check_log <- list()
fit <- function(name, x, time, event, runs = RUNS, seed = 1) {
  if (mode == "check" && !is.null(committed_lambdas[[name]])) {
    lam <- committed_lambdas[[name]]
    # Of the 72 subsampling models (Fig. S1), the first of each fraction is checked.
    if (!grepl("^S1_", name) || grepl("_01$", name)) {
      k <- seq_len(min(CHECK_RUNS, length(lam)))
      re <- cv_lambdas(x, time, event, runs = length(lam), seed = seed, which = k, cores = cores)
      check_log[[name]] <<- list(runs = length(k), equal = isTRUE(all.equal(re, lam[k], tolerance = 1e-8)))
    }
  } else {
    # Optional cache (environment variable LAMBDA_CACHE): a model's runs are saved once computed,
    # so an interrupted full run resumes; the runs are seeded, so the cache does not change them.
    cache <- Sys.getenv("LAMBDA_CACHE")
    cf <- if (nzchar(cache)) file.path(cache, paste0(name, ".rds"))
    if (!is.null(cf) && file.exists(cf)) {
      lam <- readRDS(cf)
    } else {
      lam <- cv_lambdas(x, time, event, runs = runs, seed = seed, cores = cores)
      if (!is.null(cf)) { dir.create(cache, showWarnings = FALSE, recursive = TRUE); saveRDS(lam, cf) }
    }
  }
  lambda_log[[name]] <<- lam
  cox_lasso(x, time, event, lambdas = lam)
}
ev <- function(pi, cl, cutoff) {
  e <- evaluate_model(pi, cl$time, cl$event, cutoff)
  list(p = e$p, auc = e$auc, n_high = e$n_high, group = e$group, roc = e$roc)
}
km_out <- function(e, cl, file) {
  f <- survfit(Surv(cl$time, cl$event) ~ e$group)
  st <- rep(sub("^[^=]*=", "", names(f$strata)), f$strata)
  write.csv(data.frame(group = st, time = f$time, surv = f$surv, n_censor = f$n.censor, n_event = f$n.event),
            file.path(out, "curves", file), row.names = FALSE)
}
roc_out <- function(e, file) write.csv(e$roc, file.path(out, "curves", file), row.names = FALSE)
summ <- function(e) list(p = e$p, auc = e$auc, n_high = e$n_high)
res <- list()

## Genomic model (Table 2, Figs 3 and 4): Miller PDS, unstandardized (0 to 1)
cl <- D$miller$clin
xg <- P$miller[, common]
gm <- fit("genomic", xg, cl$time, cl$event)
pi_tr <- prognostic_index(gm$coefficients, xg)
cut_g <- share_cutoff(pi_tr, 0.25)
uni <- univariate_cox(xg[, names(gm$coefficients), drop = FALSE], cl$time, cl$event)
res$genomic <- list(lambda = gm$lambda, coefficients = as.list(gm$coefficients), cutoff = cut_g,
                    hr = as.list(setNames(exp(gm$coefficients), names(gm$coefficients))),
                    univariate_p = as.list(setNames(uni$p, uni$feature)), sets = list())
for (s in sets) {
  e <- ev(prognostic_index(gm$coefficients, P[[s]][, common]), D[[s]]$clin, cut_g)
  res$genomic$sets[[s]] <- summ(e)
  km_out(e, D[[s]]$clin, sprintf("fig4_%s.csv", s)); roc_out(e, sprintf("fig4E_%s.csv", s))
}
# Sensitivity variant (never agreement): the paper's 15 pathways and coefficients on our PDS
paper_coef <- c(KEGG_MELANOGENESIS = 1.075908, BIOCARTA_SRCRPTP_PATHWAY = 0.914698,
  BIOCARTA_AKAP13_PATHWAY = 0.828364, BIOCARTA_RARRXR_PATHWAY = 0.670795, BIOCARTA_VIP_PATHWAY = 0.635108,
  KEGG_FATTY_ACID_METABOLISM = 0.520653, BIOCARTA_G1_PATHWAY = 0.520446,
  KEGG_LINOLEIC_ACID_METABOLISM = 0.368615, KEGG_LYSOSOME = 0.300587, BIOCARTA_P53_PATHWAY = 0.239062,
  BIOCARTA_PYK2_PATHWAY = 0.158405, BIOCARTA_GABA_PATHWAY = 0.139229, BIOCARTA_FEEDER_PATHWAY = 0.110334,
  BIOCARTA_RNA_PATHWAY = 0.037978, BIOCARTA_IL5_PATHWAY = 0.012039)
pc <- paper_coef[names(paper_coef) %in% common]
pi_pp <- prognostic_index(pc, xg); cut_pp <- share_cutoff(pi_pp, 0.25)
res$variant_paper_coefficients <- list(pathways_present = length(pc),
  univariate_p = as.list(setNames(univariate_cox(xg[, names(pc)], cl$time, cl$event)$p, names(pc))),
  sets = lapply(setNames(sets, sets), function(s) summ(ev(prognostic_index(pc, P[[s]][, common]), D[[s]]$clin, cut_pp))))

## Fig. 3: the paper's 15 pathways (Table 2) on our Miller PDS; two clusters; median-PDS correlation
f3 <- t(P$miller[, names(pc)])
g3 <- two_clusters(f3)
pam <- read.csv(file.path(dd, "pam50_genes.csv"))$symbol
pam_in <- intersect(pam, genes_all)
g1 <- two_clusters(D$miller$expr[pam_in, ])
res$fig3 <- list(chisq_pds_groups = chisq.test(table(g3, cl$event))$p.value,
                 cor_median_pds = cor(apply(f3, 2, median), cl$event),
                 cor_median_pam50 = cor(apply(D$miller$expr[pam_in, ], 2, median), cl$event))
res$fig1a <- list(pam50_genes_on_array = length(pam_in), chisq_pam50_groups = chisq.test(table(g1, cl$event))$p.value)
ours3 <- t(P$miller[, names(gm$coefficients), drop = FALSE])
if (nrow(ours3) >= 2) {
  g3o <- two_clusters(ours3)
  res$fig3_our_pathways <- list(chisq_pds_groups = chisq.test(table(g3o, cl$event))$p.value,
                                cor_median_pds = cor(apply(ours3, 2, median), cl$event))
}
saveRDS(list(fig1a = list(x = D$miller$expr[pam_in, ], groups = g1), fig3 = list(x = f3, groups = g3),
             clin = cl), file.path(out, "models", "heatmaps.rds"))

## Clinical and combined models (Table 2, Fig. 6). Each set is standardized on its own.
clin_feats <- c("er", "pgr", "p53", "grade", "node", "size_mm", "age")
xc <- clinical_matrix(cl, clin_feats)
cm <- fit("clinical", xc, cl$time, cl$event)
cut_c <- share_cutoff(prognostic_index(cm$coefficients, xc), 0.25)
xb <- cbind(standardize(xg), xc)
bm <- fit("combined", xb, cl$time, cl$event)
cut_b <- share_cutoff(prognostic_index(bm$coefficients, xb), 0.25)
iv <- D$ivshina$clin
xc_iv <- clinical_matrix(iv, intersect(names(cm$coefficients), colnames(iv)))
xb_iv <- cbind(standardize(P$ivshina[, common]), clinical_matrix(iv, intersect(clin_feats, colnames(iv))))
miss_c <- setdiff(names(cm$coefficients), colnames(xc_iv)); miss_b <- setdiff(names(bm$coefficients), colnames(xb_iv))
e_list <- list(
  genomic_miller = ev(pi_tr, cl, cut_g),
  genomic_ivshina = ev(prognostic_index(gm$coefficients, P$ivshina[, common]), iv, cut_g),
  combined_miller = ev(prognostic_index(bm$coefficients, xb), cl, cut_b),
  combined_ivshina = if (length(miss_b) == 0) ev(prognostic_index(bm$coefficients, xb_iv), iv, cut_b),
  clinical_miller = ev(prognostic_index(cm$coefficients, xc), cl, cut_c),
  clinical_ivshina = if (length(miss_c) == 0) ev(prognostic_index(cm$coefficients, xc_iv), iv, cut_c))
for (k in names(e_list)) if (!is.null(e_list[[k]])) {
  set <- sub("^.*_", "", k)
  km_out(e_list[[k]], D[[set]]$clin, sprintf("fig6_%s.csv", k)); roc_out(e_list[[k]], sprintf("fig6G_%s.csv", k))
}
res$clinical <- list(lambda = cm$lambda, coefficients = as.list(cm$coefficients),
                     hr = as.list(exp(cm$coefficients)), missing_in_ivshina = miss_c)
res$combined <- list(lambda = bm$lambda, coefficients = as.list(bm$coefficients),
                     hr = as.list(exp(bm$coefficients)), missing_in_ivshina = miss_b,
                     genomic_pathways_kept = sum(names(gm$coefficients) %in% names(bm$coefficients)),
                     clinical_selected = intersect(clin_feats, names(bm$coefficients)))
res$fig6 <- lapply(Filter(Negate(is.null), e_list), summ)

## Fig. 5: gene- and pathway-based models trained on each set, cutoff at the set's relapse share
pi5 <- list()
for (s in sets) {
  c5 <- D[[s]]$clin; share <- mean(c5$event == 1)
  xp <- P[[s]][, common]
  pm <- if (s == "miller") gm else fit(paste0("pathway_", s), xp, c5$time, c5$event)
  xgn <- t(D[[s]]$expr)
  gn <- fit(paste0("gene_", s), xgn, c5$time, c5$event)
  pip <- prognostic_index(pm$coefficients, xp); pig <- prognostic_index(gn$coefficients, xgn)
  ep <- ev(pip, c5, share_cutoff(pip, share)); eg <- ev(pig, c5, share_cutoff(pig, share))
  km_out(ep, c5, sprintf("fig5_%s_pathway.csv", s)); km_out(eg, c5, sprintf("fig5_%s_gene.csv", s))
  roc_out(ep, sprintf("fig5I_%s_pathway.csv", s)); roc_out(eg, sprintf("fig5I_%s_gene.csv", s))
  res$fig5[[s]] <- list(pathway = c(summ(ep), n_features = length(pm$coefficients)),
                        gene = c(summ(eg), n_features = length(gn$coefficients)))
  pi5[[s]] <- list(pathway = pip, gene = pig)
}

## Figs S2 and S4: leave one out, no refit
loo <- list()
for (s in sets) for (m in c("pathway", "gene")) {
  c5 <- D[[s]]$clin
  loo[[paste("S2", s, m, sep = "_")]] <- loo_evaluate(pi5[[s]][[m]], c5$time, c5$event)
}
pis4 <- list(miller = list(pathway = pi_tr, combined = prognostic_index(bm$coefficients, xb),
                           clinic = prognostic_index(cm$coefficients, xc)))
if (length(miss_b) == 0 && length(miss_c) == 0)
  pis4$ivshina <- list(pathway = prognostic_index(gm$coefficients, P$ivshina[, common]),
                       combined = prognostic_index(bm$coefficients, xb_iv),
                       clinic = prognostic_index(cm$coefficients, xc_iv))
for (s in names(pis4)) for (m in names(pis4[[s]]))
  loo[[paste("S4", s, m, sep = "_")]] <- loo_evaluate(pis4[[s]][[m]], D[[s]]$clin$time, D[[s]]$clin$event)
loo_df <- do.call(rbind, lapply(names(loo), function(k) cbind(key = k, loo[[k]])))
write.csv(loo_df, file.path(out, "curves", "loo.csv"), row.names = FALSE)
tt <- function(a, b) t.test(a, b)$p.value
res$loo <- list()
for (s in sets) {
  A <- loo[[paste("S2", s, "pathway", sep = "_")]]; B <- loo[[paste("S2", s, "gene", sep = "_")]]
  res$loo[[paste0("S2_", s)]] <- list(
    pathway_median_mlog10p = median(-log10(A$p)), gene_median_mlog10p = median(-log10(B$p)),
    pathway_median_auc = median(A$auc), gene_median_auc = median(B$auc),
    t_p_mlog10p = tt(-log10(A$p), -log10(B$p)), t_p_auc = tt(A$auc, B$auc))
}
for (s in names(pis4)) {
  L <- lapply(c(pathway = "pathway", combined = "combined", clinic = "clinic"), function(m) loo[[paste("S4", s, m, sep = "_")]])
  res$loo[[paste0("S4_", s)]] <- c(
    lapply(L, function(d) list(median_mlog10p = median(-log10(d$p)), median_auc = median(d$auc))),
    list(t_p_combined_vs_pathway_auc = tt(L$combined$auc, L$pathway$auc),
         t_p_pathway_vs_clinic_auc = tt(L$pathway$auc, L$clinic$auc),
         t_p_combined_vs_pathway_mlog10p = tt(-log10(L$combined$p), -log10(L$pathway$p)),
         t_p_pathway_vs_clinic_mlog10p = tt(-log10(L$pathway$p), -log10(L$clinic$p))))
}

## Fig. S1: random 1/2 to 1/16 of the pathways, 18 draws each, S1_RUNS cross-validation runs each
set.seed(20140929)
draws <- list()
for (fr in c(2, 4, 8, 16)) for (r in seq_len(S1_REPS))
  draws[[sprintf("%d_%d", fr, r)]] <- sort(sample(common, floor(length(common) / fr)))
s1 <- NULL
for (fr in c(2, 4, 8, 16)) for (r in seq_len(S1_REPS)) {
  keep <- draws[[sprintf("%d_%d", fr, r)]]
  nm <- sprintf("S1_%d_%02d", fr, r)
  m1 <- fit(nm, xg[, keep], cl$time, cl$event, runs = S1_RUNS, seed = 1000 * fr + r)
  pi1 <- prognostic_index(m1$coefficients, xg[, keep])
  e1 <- ev(pi1, cl, share_cutoff(pi1, 0.25))
  s1 <- rbind(s1, data.frame(fraction = paste0("1/", fr), rep = r, n_pathways = length(keep),
                             n_selected = length(m1$coefficients), p = e1$p, auc = e1$auc))
}
write.csv(s1, file.path(out, "curves", "figS1.csv"), row.names = FALSE)
res$s1 <- list(median_auc = as.list(tapply(s1$auc, s1$fraction, median)[c("1/2", "1/4", "1/8", "1/16")]),
               auc_range = range(s1$auc),
               t_p_half_vs_quarter = tt(s1$auc[s1$fraction == "1/2"], s1$auc[s1$fraction == "1/4"]))

## Fig. S3: NKI70 on Miller
if (!is.na(nki_rda) && file.exists(nki_rda)) {
  env <- new.env(); load(nki_rda, envir = env)
  sg <- env$sig.gene70
  sig <- data.frame(symbol = as.character(sg$HUGO.gene.symbol), good_profile = sg$average.good.prognosis.profile)
  nk <- nki70_score(D$miller$expr, sig)
  g <- factor(ifelse(nk$poor, "higher", "lower"), levels = c("lower", "higher"))
  r <- roc_auc(nk$score, cl$event)
  roc_out(list(roc = r$curve), "figS3_nki70.csv"); roc_out(e_list$genomic_miller, "figS3_pathway.csv")
  res$nki70 <- list(genes = length(nk$genes), n_poor = sum(nk$poor), p = logrank_p(cl$time, cl$event, g),
                    auc = r$auc, auc_binary = roc_auc(as.numeric(nk$poor), cl$event)$auc)
}

res$pathways_scored <- lapply(P, ncol); res$pathways_common <- length(common)
write_json(res, file.path(out, "models.json"), auto_unbox = TRUE, pretty = TRUE, digits = NA)
write_json(lambda_log, file.path(out, "models", "lambdas.json"), digits = NA)
write_json(check_log, file.path(out, "lambda_check.json"), auto_unbox = TRUE, pretty = TRUE)

# Variants that test the causes of differences (results_notes.json, "hypotheses"):
#  - simulation: stronger within-set correlation (rho 0.8, 0.9) for the correlated sets, mean,
#    Wilcoxon and Hotelling with resampling (Tables 2, 3 and 6);
#  - simulation: false positive rates for set 3 on 400 more data sets;
#  - p53, cond. FDR (review of PR #89): the local fdr fdrtool gives the p53 genes, and other
#    readings of the statistic, counted at p <= 0.01 and 0.05 with 200 random sets (resampling);
#  - Hedenfalk: other preprocessing (sets of 10 or more genes; one clone per symbol instead of the
#    mean of its clones), counts of sets with p <= 0.01 for the mean of squared moderated t.
# Usage: Rscript variants.R DOWNLOADS OUT.json [CORES]
suppressMessages(library(gseamod))
args <- commandArgs(TRUE)
dl <- args[1]; out <- args[2]
cores <- if (length(args) >= 3) as.integer(args[3]) else 1L
B <- 1000L

sim <- lapply(c(0.6, 0.8, 0.9), function(rho) {
  P <- parallel::mclapply(1:100, function(r) {
    d <- simulate_ackermann(seed = 20090203L + r, rho = rho)
    set.seed(20090203L + 100000L + r)
    rs <- random_sets(600, 20L, B)
    run <- function(...) gsea(d$X, d$y, d$sets, B = B, rsets = rs, method = "resampling", ...)$p
    cbind(mean = run(setstat = "mean"), wilcoxon = run(setstat = "wilcoxon"), hotelling = run(setstat = "hotelling"))
  }, mc.cores = cores)
  A <- simplify2array(P)
  r <- apply(A <= 0.05, 1:2, mean)
  rownames(r) <- paste0("set", 1:9)
  list(rho = rho, rates = lapply(as.data.frame(r), function(v) setNames(as.list(v), rownames(r))))
})

# Set 3 (no effect) on 400 more data sets: false positive rates of globaltest (parametric and
# permutation) and of the mean of squared mod.t (permutation), B = 200.
null3 <- parallel::mclapply(101:500, function(r) {
  d <- simulate_ackermann(seed = 30000L + r)
  s3 <- d$sets["set3"]
  c(globaltest_parametric = gsea(d$X, d$y, s3, setstat = "globaltest", method = "parametric")$p,
    globaltest_permutation = gsea(d$X, d$y, s3, setstat = "globaltest", method = "permutation", B = 200, seed = r)$p,
    mean_permutation = gsea(d$X, d$y, s3, setstat = "mean", method = "permutation", B = 200, seed = r)$p)
}, mc.cores = cores)
null3 <- as.list(colMeans(do.call(rbind, null3) <= 0.05))

# p53, cond. FDR readings: ours (mean of 1 - fdr_S), the mean fitted membership probability
# pi_S, and the mean gain fdr - fdr_S; the mean of squared mod.t for reference.
p53 <- readRDS(file.path(dirname(out), "p53_for_variants.rds"))
pg <- gene_stats(p53$X, p53$y, "modt"); ps <- as.numeric(pg)^2; pN <- nrow(p53$X)
pf <- fdrtool::fdrtool(as.numeric(pg), statistic = "normal", plot = FALSE, verbose = FALSE)$lfdr
cf_stat <- function(I, kind) {
  m <- nrow(I); fit <- gseamod:::logistic_fit(ps, I); Z <- matrix(fit$z[I], m)
  pis <- plogis(sweep(sweep(Z, 2, fit$b, "*"), 2, fit$a, "+")); F <- matrix(pf[I], m)
  switch(kind, mean = colMeans(matrix(ps[I], m)), ours = colMeans(1 - pmin(F * (m / pN) / pis, 1)),
         pi_mean = colMeans(pis), gain = colMeans(F - pmin(F * (m / pN) / pis, 1)))
}
set.seed(20090203L)
kinds <- c("mean", "ours", "pi_mean", "gain")
idx <- lapply(p53$sets, function(v) match(v, rownames(p53$X)))
Imats <- lapply(idx, function(i) unname(cbind(i, vapply(1:200, function(b) sample.int(pN, length(i)), integer(length(i))))))
cfp <- parallel::mclapply(kinds, function(k) vapply(Imats, function(I) { v <- cf_stat(I, k); mean(v[-1] >= v[1]) }, numeric(1)),
                          mc.cores = cores)
p53_condfdr <- c(list(genes_lfdr_below_0.2 = sum(pf < 0.2), median_lfdr = median(pf), random_sets = 200),
                 setNames(lapply(cfp, function(p) list(p01 = sum(p <= 0.01), p05 = sum(p <= 0.05))), kinds))

e <- new.env()
load(gzcon(gzfile(file.path(dl, "hedenfalk.rda.gz"))), envir = e)
gmt <- read_gmt(file.path(dl, "c2.symbols.gmt"))
map <- read.delim(file.path(dl, "hedenfalk_image2unigene.tsv"), header = FALSE, colClasses = "character",
                  col.names = c("clone", "cluster", "symbol"))
ncl <- tapply(map$cluster, map$clone, function(v) length(unique(v)))
sym <- tapply(map$symbol, map$clone, function(v) paste(sort(unique(v[v != ""])), collapse = ","))
okc <- names(ncl)[ncl == 1 & sym != "" & !grepl(",", sym)]
clone <- as.character(e$hedenfalk.imagecloneid)
symbol <- ifelse(clone %in% okc, sym[clone], NA)
sel <- e$hedenfalk.mutation %in% c("BRCA1", "BRCA2")
Hs <- t(e$hedenfalk[sel, ])
y <- as.numeric(e$hedenfalk.mutation[sel] == "BRCA2")
mapped <- !is.na(symbol)
grp <- symbol[mapped]
Xmean <- rowsum(Hs[mapped, ], grp, reorder = FALSE) / as.vector(table(factor(grp, levels = unique(grp))))
first <- mapped & !duplicated(symbol)
Xfirst <- Hs[first, ]; rownames(Xfirst) <- symbol[first]
count <- function(X, lo) {
  sets <- lapply(gmt, function(v) intersect(v, rownames(X)))
  sets <- sets[lengths(sets) >= lo & lengths(sets) <= 500]
  p <- sapply(c("resampling", "permutation"), function(me)
    gsea(X, y, sets, setstat = "mean", method = me, B = B, seed = 20090203L)$p)
  list(genes = nrow(X), sets = length(sets), resampling = sum(p[, 1] <= 0.01), permutation = sum(p[, 2] <= 0.01))
}
hed <- list(mean_of_clones_15 = count(Xmean, 15), mean_of_clones_10 = count(Xmean, 10),
            first_clone_15 = count(Xfirst, 15))
jsonlite::write_json(list(simulation = sim, null_set3 = c(null3, data_sets = 400), p53_condfdr = p53_condfdr, hedenfalk = hed), out, auto_unbox = TRUE, pretty = TRUE, digits = NA)

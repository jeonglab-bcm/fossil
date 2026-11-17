# Variants that test the causes of differences (results_notes.json, "hypotheses"):
#  - simulation: stronger within-set correlation (rho 0.8, 0.9) for the correlated sets, mean,
#    Wilcoxon and Hotelling with resampling (Tables 2, 3 and 6);
#  - simulation: false positive rates for set 3 on 400 more data sets;
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
Xmean <- rowsum(Hs[mapped, ], symbol[mapped]) / as.vector(table(symbol[mapped])[sort(unique(symbol[mapped]))])
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
jsonlite::write_json(list(simulation = sim, null_set3 = c(null3, data_sets = 400), hedenfalk = hed), out, auto_unbox = TRUE, pretty = TRUE, digits = NA)

# Preprocess the two experimental data sets of Ackermann and Strimmer (2009).
#
# p53 (NCI-60, Subramanian et al. 2005): the GSEA collapsed-symbol file (10,100 genes x 50 cell
# lines). Keep genes whose maximum is at least 5 on the log2 scale AND whose max/min ratio is at
# least 2 (the paper: "filtered out genes that showed maximum signal intensities of less than 5 on
# log2 scale and a variation of less than 2-fold"), then log2. Gene sets: C2 sets with 15 to 500
# genes among the filtered genes.
#
# Hedenfalk (BRCA1 vs BRCA2): strimmerlab's hedenfalk.rda (3,226 clones x 22 samples, log
# ratios). Keep the 7 BRCA1 and 8 BRCA2 samples. Map each IMAGE clone to a gene symbol through
# UniGene build 236 (the last build, 2013): clones whose IMAGE id lies in exactly one UniGene
# cluster that has a gene symbol; clones of the same symbol are averaged. Gene sets: C2 sets with
# 15 to 500 genes among the mapped genes (the rule the paper states for p53).
#
# Usage: Rscript prepare_data.R DOWNLOADS OUTDIR
suppressMessages(library(gseamod))
library(jsonlite)
args <- commandArgs(TRUE)
dl <- args[1]; out <- args[2]
dir.create(out, showWarnings = FALSE, recursive = TRUE)
gmt <- read_gmt(file.path(dl, "c2.symbols.gmt"))
pick_sets <- function(genes, lo = 15, hi = 500) {
  s <- lapply(gmt, function(v) intersect(v, genes))
  s[lengths(s) >= lo & lengths(s) <= hi]
}

## p53
raw <- read_gct(file.path(dl, "P53_collapsed_symbols.gct"))
cls <- read_cls(file.path(dl, "P53.cls"))
mx <- apply(raw, 1, max); mn <- apply(raw, 1, min)
keep <- log2(mx) >= 5 & mx / mn >= 2
X <- log2(raw[keep, ])
y <- as.numeric(cls == "MUT")
sets <- pick_sets(rownames(X))
saveRDS(list(X = X, y = y, sets = sets), file.path(out, "p53.rds"))
sz <- lengths(sets)
probe_header <- strsplit(readLines(file.path(dl, "P53_hgu95av2.gct"), n = 2)[2], "\t")[[1]]
p53 <- list(probe_sets = as.integer(probe_header[1]), probe_samples = as.integer(probe_header[2]), collapsed_genes = nrow(raw), samples = ncol(raw),
            wild_type = sum(cls == "WT"), mutant = sum(cls == "MUT"),
            genes_after_filter = nrow(X), keep_max_only = sum(log2(mx) >= 5), keep_fold_only = sum(mx / mn >= 2),
            keep_either = sum(log2(mx) >= 5 | mx / mn >= 2),
            c2_sets = length(gmt), gene_sets = length(sets), min_set_size = min(sz), max_set_size = max(sz))

## Hedenfalk
e <- new.env()
load(gzcon(gzfile(file.path(dl, "hedenfalk.rda.gz"))), envir = e)
H <- e$hedenfalk                                  # samples x clones
mut <- e$hedenfalk.mutation
clone <- as.character(e$hedenfalk.imagecloneid)
map <- read.delim(file.path(dl, "hedenfalk_image2unigene.tsv"), header = FALSE, colClasses = "character",
                  col.names = c("clone", "cluster", "symbol"))
ncl <- tapply(map$cluster, map$clone, function(v) length(unique(v)))
sym <- tapply(map$symbol, map$clone, function(v) paste(sort(unique(v[v != ""])), collapse = ","))
ok_clone <- names(ncl)[ncl == 1 & sym != "" & !grepl(",", sym)]
symbol <- ifelse(clone %in% ok_clone, sym[clone], NA)
sel <- mut %in% c("BRCA1", "BRCA2")
Hs <- t(H[sel, ])                                # clones x 15
mapped <- !is.na(symbol)
Xh <- rowsum(Hs[mapped, ], symbol[mapped]) / as.vector(table(symbol[mapped])[sort(unique(symbol[mapped]))])
yh <- as.numeric(mut[sel] == "BRCA2")
setsh <- pick_sets(rownames(Xh))
saveRDS(list(X = Xh, y = yh, sets = setsh), file.path(out, "hedenfalk.rds"))
szh <- lengths(setsh)
hed <- list(samples_total = nrow(H), brca1 = sum(mut == "BRCA1"), brca2 = sum(mut == "BRCA2"), clones = ncol(H),
            clones_with_unigene = sum(clone %in% names(ncl)), clones_mapped = sum(mapped),
            genes_mapped = nrow(Xh), gene_sets = length(setsh), min_set_size = min(szh), max_set_size = max(szh),
            gene_sets_min10 = length(pick_sets(rownames(Xh), 10)))
write_json(list(p53 = p53, hedenfalk = hed), file.path(out, "datasets.json"), auto_unbox = TRUE, pretty = TRUE)
cat(toJSON(list(p53 = p53, hedenfalk = hed), auto_unbox = TRUE, pretty = TRUE), "\n")

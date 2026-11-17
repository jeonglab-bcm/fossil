# Childhood leukemia data (Den Boer et al. 2009; GEO GSE13425): TEL-AML1
# against hyperdiploid, achieved FDR and power after filtering (Figs 7 and S5).
#
# Usage: Rscript leukemia.R <series_matrix.txt.gz> <draws> <out.json>
#
# The truth is the set of probe sets limma calls at BH 5% on all 88 samples.
# For each subset size (8, 16, 24 per group) a random subset is drawn
# (set.seed(size), then draw d of `draws` with set.seed(1000 * size + d)), limma is
# fitted to the subset with all probe sets, the filter (computed on the subset) removes a
# fraction of the probe sets, and the moderated p-values of the rest are BH-corrected at 5%.
suppressMessages({library(filterfdr); library(limma); library(jsonlite)})
args <- commandArgs(TRUE)
path <- args[1]; draws <- as.integer(args[2]); out <- args[3]

con <- gzfile(path); lines <- readLines(con); close(con)
chr <- strsplit(grep("^!Sample_characteristics_ch1", lines, value = TRUE)[1], "\t")[[1]][-1]
chr <- sub(".*subtype: ", "", gsub('"', "", chr))
gsm <- gsub('"', "", strsplit(grep("^!Sample_geo_accession", lines, value = TRUE), "\t")[[1]][-1])
start <- grep("^!series_matrix_table_begin", lines) + 1
end <- grep("^!series_matrix_table_end", lines) - 1
tab <- read.delim(text = lines[start:end], check.names = FALSE, row.names = 1)
stopifnot(identical(colnames(tab), gsm))
# 44 TEL-AML1: the 43 "TEL-AML1" samples and the one "TEL-AML1 (+hyperdiploidy)"
tel <- which(chr %in% c("TEL-AML1", "TEL-AML1 (+hyperdiploidy)"))
hyp <- which(chr == "Hyperdiploid")
stopifnot(length(tel) == 44, length(hyp) == 44)
x <- as.matrix(tab[, c(tel, hyp)])

fit_p <- function(x, group) {
  design <- model.matrix(~ group)
  fit <- eBayes(lmFit(x, design))
  list(p = fit$p.value[, 2], fc = abs(fit$coefficients[, 2]))
}
grp <- factor(rep(c("TEL", "HYP"), each = 44), levels = c("TEL", "HYP"))
whole <- fit_p(x, grp)
truth <- p.adjust(whole$p, "BH") <= 0.05

F10 <- seq(0, 0.9, 0.1)
one_subset <- function(idx_tel, idx_hyp) {
  xs <- x[, c(idx_tel, 44 + idx_hyp)]
  g <- factor(rep(c("TEL", "HYP"), c(length(idx_tel), length(idx_hyp))), levels = c("TEL", "HYP"))
  fp <- fit_p(xs, g)
  stats <- list(foldchange = fp$fc, signal = rowMeans(xs), variance = apply(xs, 1, var))
  lapply(stats, function(st) {
    t(sapply(F10, function(fr) {
      keep <- filter_keep(st, fr)
      rej <- rep(FALSE, nrow(xs))
      rej[keep] <- p.adjust(fp$p[keep], "BH") <= 0.05
      r <- sum(rej)
      c(fraction = fr, fdr = if (r == 0) 0 else sum(rej & !truth) / r,
        power = sum(rej & truth) / sum(truth), rejected = r)
    }))
  })
}
res <- list(features = nrow(x), samples = c(tel = length(tel), hyp = length(hyp)),
            whole_calls = sum(truth), main = list(), draws = list())
for (n in c(8, 16, 24)) {
  set.seed(n)
  res$main[[paste0("n", n)]] <- one_subset(sample(44, n), sample(44, n))
  res$draws[[paste0("n", n)]] <- lapply(seq_len(draws), function(d) {
    set.seed(1000 * n + d)
    one_subset(sample(44, n), sample(44, n))
  })
}
writeLines(toJSON(res, digits = NA, auto_unbox = TRUE), out)

# Tests of why Model 2's standard deviations (Table 3) come out about 2.5% below the printed ones.
#
#   Rscript hypotheses.R DATA_DIR OUT_JSON [CORES]
#
# Each hypothesis is a variant fit of Model 2 on Vandesompele et al.'s data; its distance from
# Table 3 is the sum over the 14 free parameters (10 sigma_j, 4 varsigma_k) of |log(ours/printed)|.
# The main fit is about 0.26 away. Slow (about 100 fits, 20 minutes on one core): the pipeline
# reruns it with --full and reads the committed output otherwise.
suppressPackageStartupMessages({ library(hkselect); library(nlme); library(jsonlite); library(parallel) })
args <- commandArgs(TRUE)
cores <- if (length(args) > 2) as.integer(args[3]) else 1L
v <- read_expression(file.path(args[1], "vandesompele.csv"))
V <- v$expr; tis <- factor(as.character(v$tissue), levels = c("BM", "FIB", "LEU", "NB", "POOL"))
pub_s <- c(ACTB = 0.460, B2M = 0.562, GAPD = 0.211, HMBS = 0.431, HPRT1 = 0.227, RPL13A = 0.339,
           SDHA = 0.255, TBP = 0.339, UBC = 0.226, YWHAZ = 0.232)
pub_t <- c(BM = 1, FIB = 1.204, LEU = 1.879, NB = 1.582, POOL = 2.014)
dist <- function(s, t) sum(abs(log(s[names(pub_s)] / pub_s))) + sum(abs(log(t[names(pub_t)][-1] / pub_t[-1])))
summ <- function(name, s, t, note = NULL) c(list(name = name, distance = dist(s, t),
  sigma = as.list(round(s[names(pub_s)], 4)), varsigma = as.list(round(t[names(pub_t)], 4))), if (!is.null(note)) list(note = note))
from_comp <- function(cmp) list(s = cmp$sigma, t = cmp$varsigma)

out <- list()
main <- from_comp(model2_components(fit_model2(V, tis)))
out$main <- summ("Model 2 by REML (our fit)", main$s, main$t)
ml <- from_comp(model2_components(fit_model2(V, tis, method = "ML")))
out$variants <- list(summ("maximum likelihood instead of REML", ml$s, ml$t))

# Sample effects random instead of fixed (lme), tissue by gene fixed
d <- as_long(V, tis)
vf <- varComb(varIdent(form = ~ 1 | gene), varIdent(form = ~ 1 | tissue))
f <- lme(y ~ tissue * gene, random = ~ 1 | sample, data = d, weights = vf, control = lmeControl(msMaxIter = 200))
co <- coef(f$modelStruct$varStruct, unconstrained = FALSE, allCoef = TRUE)
s <- f$sigma * co[paste0("A.", levels(d$gene))] * co["B.BM"]; names(s) <- levels(d$gene)
t <- co[paste0("B.", levels(tis))] / co["B.BM"]; names(t) <- levels(tis)
out$variants[[2]] <- summ("random sample effects (lme)", s, t)

# No tissue-by-gene term (the bias goes into the error)
f <- gls(y ~ sample + gene, data = d, weights = vf)
co <- coef(f$modelStruct$varStruct, unconstrained = FALSE, allCoef = TRUE)
s <- f$sigma * co[paste0("A.", levels(d$gene))] * co["B.BM"]; names(s) <- levels(d$gene)
t <- co[paste0("B.", levels(tis))] / co["B.BM"]; names(t) <- levels(tis)
out$variants[[3]] <- summ("no tissue-by-gene effect", s, t)

# log10 instead of natural logs: scales every sigma by 1/log(10), the multipliers not at all
out$variants[[4]] <- summ("log10 instead of natural logarithms", main$s / log(10), main$t)

# One sample left out (a sample missing from, or different in, the authors' copy of the data)
drop1 <- mclapply(rownames(V), function(smp) {
  keep <- rownames(V) != smp
  cmp <- from_comp(model2_components(fit_model2(V[keep, ], droplevels(tis[keep]))))
  data.frame(sample = smp, distance = dist(cmp$s, cmp$t))
}, mc.cores = cores)
drop1 <- do.call(rbind, drop1)
drop1 <- drop1[order(drop1$distance), ]
out$drop_one <- list(best = head(drop1, 5), runs = nrow(drop1),
                     note = "Model 2 refitted without each of the 85 samples in turn; the five closest to Table 3")
writeLines(toJSON(out, auto_unbox = TRUE, pretty = TRUE, digits = 6), args[2])
cat("main", out$main$distance, "best variant", min(sapply(out$variants, `[[`, "distance")),
    "best drop-one", drop1$distance[1], drop1$sample[1], "\n")

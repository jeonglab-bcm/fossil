# Write the package's example data (inst/extdata). Run from the package folder:
#   Rscript scripts/make_example_data.R DATA_DIR
# DATA_DIR is the reproduction's prepared data (figure-reproduction pipeline, prepare_data.R),
# which holds the Miller clinical table built from breastCancerUPP and the GSE4922 clinical file.
a <- commandArgs(TRUE)
ext <- "inst/extdata"
dir.create(ext, showWarnings = FALSE, recursive = TRUE)

# 1. Miller (GSE3494) clinical table, 236 patients with a relapse status
m <- readRDS(file.path(a[1], "miller.rds"))$clin
cl <- data.frame(tumour = m$tumour, time = round(m$time, 6), event = m$event, age = m$age, er = m$er,
                 pgr = m$pgr, size_mm = m$size_mm, grade = m$grade, node = m$node, p53 = m$p53)
write.csv(cl, file.path(ext, "miller_clinical.csv"), row.names = FALSE, na = "")

# 2. Synthetic expression: 150 tumours, three gene sets of 12 genes, 40 background genes.
#    Gene g of set k: 8 + 0.9 * activity_k + N(0, 0.5). Hazard: exp(1.0 * activity_A + 0.7 * activity_B);
#    set C carries no risk. Exponential times (rate 0.08 per year at activity 0), censored at
#    a uniform 4 to 12 years.
set.seed(20140929)
n <- 150
act <- matrix(rnorm(3 * n), n, 3, dimnames = list(NULL, c("SET_A", "SET_B", "SET_C")))
genes <- list(SET_A = sprintf("GA%02d", 1:12), SET_B = sprintf("GB%02d", 1:12), SET_C = sprintf("GC%02d", 1:12))
x <- NULL
for (k in names(genes)) for (g in genes[[k]]) x <- rbind(x, 8 + 0.9 * act[, k] + rnorm(n, sd = 0.5))
x <- rbind(x, matrix(8 + rnorm(40 * n, sd = 0.7), 40, n))
rownames(x) <- c(unlist(genes), sprintf("BG%02d", 1:40))
colnames(x) <- sprintf("S%03d", 1:n)
rate <- 0.08 * exp(1.0 * act[, "SET_A"] + 0.7 * act[, "SET_B"])
t_event <- rexp(n, rate)
t_cens <- runif(n, 4, 12)
surv <- data.frame(sample = colnames(x), time = round(pmin(t_event, t_cens), 4),
                   event = as.integer(t_event <= t_cens))
write.csv(data.frame(gene = rownames(x), round(x, 3), check.names = FALSE),
          file.path(ext, "synthetic_expression.csv"), row.names = FALSE)
write.csv(surv, file.path(ext, "synthetic_survival.csv"), row.names = FALSE)
writeLines(vapply(names(genes), function(k) paste(c(k, "synthetic", genes[[k]]), collapse = "\t"), ""),
           file.path(ext, "synthetic_sets.gmt"))
write.csv(data.frame(sample = colnames(x), round(act, 4)), file.path(ext, "synthetic_truth.csv"), row.names = FALSE)
write.csv(data.frame(set = names(genes), log_hazard_ratio = c(1.0, 0.7, 0)), file.path(ext, "synthetic_effects.csv"),
          row.names = FALSE, quote = FALSE)

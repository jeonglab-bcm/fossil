# Prepare the four data sets of Huang et al. 2014 (PMC4168973) from the downloaded GEO series
# matrices, the GSE4922 clinical file and the breastCancerUPP clinical table.
#   Rscript prepare_data.R DOWNLOADS OUTDIR
# Writes OUTDIR/<set>.rds (list: expr = genes x samples matrix of log2 values, clin = data.frame),
# OUTDIR/genesets.rds (the 403 KEGG + BioCarta gene sets) and OUTDIR/datasets.json (counts).
suppressPackageStartupMessages({library(pdscox); library(jsonlite)})
args <- commandArgs(TRUE)
dl <- args[1]; out <- args[2]
dir.create(out, showWarnings = FALSE, recursive = TRUE)

annot <- read_gpl_annot(file.path(dl, "GPL96.annot.gz"))

# Miller (GSE3494, training): clinical data from breastCancerUPP (the Uppsala series with RFS),
# p53 status from the GSE4922 clinical file (same tumours, matched by tumour ID).
upp_env <- new.env()
load(file.path(dl, "breastCancerUPP", "data", "upp.rda"), envir = upp_env)
upp <- Biobase::pData(upp_env$upp)
g4922 <- read.delim(file.path(dl, "GSE4922_Clinical_file_for_both_Uppsala_Singapore_Samples.txt"),
                    check.names = FALSE, stringsAsFactors = FALSE)
names(g4922) <- c("gsm", "cohort", "index", "grade", "sws", "p1", "p3", "dfs_time", "dfs_event",
                  "all", "er_endo", "no_sys", "er", "ln", "p53", "age", "size_mm")
g4922 <- g4922[g4922$cohort == "Uppsala", ]
g4922$tumour <- sub("^X", "", g4922$index)

m <- read_series_matrix(file.path(dl, "GSE3494-GPL96_series_matrix.txt.gz"))
tum <- sub("^X", "", sub(" .*$", "", m$samples$title))
upp$tumour <- as.character(upp$id)
cl <- upp[match(tum, upp$tumour), ]
keep <- !is.na(cl$e.rfs)
p53 <- g4922$p53[match(tum, g4922$tumour)]
miller_clin <- data.frame(
  sample = m$samples$geo_accession, tumour = tum,
  time = cl$t.rfs / 365, event = cl$e.rfs, age = cl$age,
  er = cl$er, pgr = cl$pgr, size_mm = cl$size * 10, grade = cl$grade, node = cl$node,
  p53 = ifelse(p53 == "p53+", 1, ifelse(p53 == "p53-", 0, NA)),
  stringsAsFactors = FALSE)[keep, ]
miller <- list(name = "Miller", expr = probes_to_genes(m$expr[, keep], annot), clin = miller_clin)

# Pawitan (GSE1456, test set 1)
m <- read_series_matrix(file.path(dl, "GSE1456-GPL96_series_matrix.txt.gz"))
ch <- m$characteristics
num <- function(x) suppressWarnings(as.numeric(x))
# Time: the earlier of relapse and death (its mean, 5.959 years, is Table 1's; SURV_RELAPSE alone
# gives 6.196). Event: RELAPSE (40 relapses, as in Table 1).
pawitan_clin <- data.frame(sample = m$samples$geo_accession,
  time = pmin(num(ch[["SURV_RELAPSE"]]), num(ch[["SURV_DEATH"]])), event = num(ch[["RELAPSE"]]),
  time_relapse = num(ch[["SURV_RELAPSE"]]),
  grade = num(ch[["ELSTON"]]), stringsAsFactors = FALSE)
pawitan <- list(name = "Pawitan", expr = probes_to_genes(m$expr, annot), clin = pawitan_clin)

# Ivshina (GSE4922 Uppsala, test set 2)
m <- read_series_matrix(file.path(dl, "GSE4922-GPL96_series_matrix.txt.gz"))
tum <- sub("^X", "", sub("^A ", "", m$samples$title))
gm <- g4922[match(tum, g4922$tumour), ]
keep <- !is.na(gm$cohort)
iv_clin <- data.frame(sample = m$samples$geo_accession, tumour = tum,
  time = num(gm$dfs_time), event = num(gm$dfs_event), age = num(gm$age),
  er = ifelse(gm$er == "ER+", 1, ifelse(gm$er == "ER-", 0, NA)),
  size_mm = num(gm$size_mm), grade = num(gm$grade),
  node = ifelse(gm$ln == "LN+", 1, ifelse(gm$ln == "LN-", 0, NA)),
  p53 = ifelse(gm$p53 == "p53+", 1, ifelse(gm$p53 == "p53-", 0, NA)),
  stringsAsFactors = FALSE)[keep, ]
ivshina <- list(name = "Ivshina", expr = probes_to_genes(m$expr[, keep], annot), clin = iv_clin)

# Desmedt (GSE7390, test set 3)
m <- read_series_matrix(file.path(dl, "GSE7390_series_matrix.txt.gz"))
ch <- m$characteristics
des_clin <- data.frame(sample = m$samples$geo_accession,
  time = num(ch[["t.rfs"]]) / 365, event = num(ch[["e.rfs"]]), age = num(ch[["age"]]),
  er = num(ch[["er"]]), size_mm = num(ch[["size"]]) * 10, grade = num(ch[["grade"]]),
  node = num(ch[["node"]]), stringsAsFactors = FALSE)
desmedt <- list(name = "Desmedt", expr = probes_to_genes(m$expr, annot), clin = des_clin)

sets <- list(miller = miller, pawitan = pawitan, ivshina = ivshina, desmedt = desmedt)
for (s in names(sets)) saveRDS(sets[[s]], file.path(out, paste0(s, ".rds")))

gs <- c(read_gmt(file.path(dl, "c2.cp.biocarta.v6.0.symbols.gmt")),
        read_gmt(file.path(dl, "c2.cp.kegg.v6.0.symbols.gmt")))
saveRDS(gs, file.path(out, "genesets.rds"))
pam_env <- new.env(); load(file.path(dl, "genefu", "data", "pam50.rda"), envir = pam_env)
write.csv(data.frame(symbol = rownames(pam_env$pam50$centroids)), file.path(out, "pam50_genes.csv"), row.names = FALSE)
file.copy(file.path(dl, "genefu", "data", "sig.gene70.rda"), file.path(out, "sig.gene70.rda"), overwrite = TRUE)

# Shared arrays between GSE3494 and GSE4922 (same Uppsala tumours)
shared <- intersect(miller$clin$tumour, ivshina$clin$tumour)
same_values <- sum(vapply(shared, function(t) {
  a <- miller$expr[, miller$clin$sample[miller$clin$tumour == t]]
  b <- ivshina$expr[, ivshina$clin$sample[ivshina$clin$tumour == t]]
  isTRUE(all.equal(a, b))
}, logical(1)))
info <- list(
  sets = lapply(sets, function(s) list(samples = ncol(s$expr), genes = nrow(s$expr),
                                       relapse = sum(s$clin$event == 1, na.rm = TRUE))),
  genesets = length(gs),
  miller_ivshina_shared_tumours = length(shared),
  miller_ivshina_identical_arrays = same_values)
write_json(info, file.path(out, "datasets.json"), auto_unbox = TRUE, pretty = TRUE)

# Table 3 (genomic model columns) and the gene coverage numbers of the Discussion.
#   Rscript table3.R DATA_DIR OUT_DIR
# Table 3 is computed from the paper's Table 2 (pathways and coefficients) and MSigDB v6.0; the
# coverage numbers from the 403 gene sets and the U133A genes of the Miller data.
suppressPackageStartupMessages({library(pdscox); library(jsonlite)})
a <- commandArgs(TRUE)
gs <- readRDS(file.path(a[1], "genesets.rds"))
coef <- c(KEGG_MELANOGENESIS = 1.075908, BIOCARTA_SRCRPTP_PATHWAY = 0.914698,
  BIOCARTA_AKAP13_PATHWAY = 0.828364, BIOCARTA_RARRXR_PATHWAY = 0.670795, BIOCARTA_VIP_PATHWAY = 0.635108,
  KEGG_FATTY_ACID_METABOLISM = 0.520653, BIOCARTA_G1_PATHWAY = 0.520446,
  KEGG_LINOLEIC_ACID_METABOLISM = 0.368615, KEGG_LYSOSOME = 0.300587, BIOCARTA_P53_PATHWAY = 0.239062,
  BIOCARTA_PYK2_PATHWAY = 0.158405, BIOCARTA_GABA_PATHWAY = 0.139229, BIOCARTA_FEEDER_PATHWAY = 0.110334,
  BIOCARTA_RNA_PATHWAY = 0.037978, BIOCARTA_IL5_PATHWAY = 0.012039)
w <- pathway_gene_weights(gs, exp(coef))
w_hr <- pathway_gene_weights(gs, c(KEGG_MELANOGENESIS = 2.93266, BIOCARTA_SRCRPTP_PATHWAY = 2.49602,
  BIOCARTA_AKAP13_PATHWAY = 2.28957, BIOCARTA_RARRXR_PATHWAY = 1.95579, BIOCARTA_VIP_PATHWAY = 1.88723,
  KEGG_FATTY_ACID_METABOLISM = 1.68313, BIOCARTA_G1_PATHWAY = 1.68278, KEGG_LINOLEIC_ACID_METABOLISM = 1.44573,
  KEGG_LYSOSOME = 1.35065, BIOCARTA_P53_PATHWAY = 1.27006, BIOCARTA_PYK2_PATHWAY = 1.17164,
  BIOCARTA_GABA_PATHWAY = 1.14939, BIOCARTA_FEEDER_PATHWAY = 1.11665, BIOCARTA_RNA_PATHWAY = 1.03871,
  BIOCARTA_IL5_PATHWAY = 1.01211))
starred <- names(coef)[c(1:7, 10, 11, 14)]
m <- readRDS(file.path(a[1], "miller.rds"))
pg <- unique(unlist(gs))
on_array <- intersect(pg, rownames(m$expr))
mean_log2 <- rowMeans(m$expr)
out <- list(
  genes = setNames(lapply(seq_len(nrow(w)), function(i) list(count = w$count[i], weighted = w$weighted[i])), w$gene),
  weighted_from_printed_hr = setNames(as.list(w_hr$weighted), w_hr$gene),
  rank = setNames(as.list(rank(-round(w$weighted, 6), ties.method = "min")), w$gene),
  starred_pathway_counts = setNames(as.list(vapply(w$gene, function(g) sum(vapply(gs[starred], function(s) g %in% s, logical(1))), numeric(1))), w$gene),
  coverage = list(pathways = length(gs), genes_in_pathways = length(pg), genes_in_pathways_on_array = length(on_array),
                  genes_in_pathways_expressed = sum(mean_log2[on_array] > 7),
                  genes_on_array = nrow(m$expr), genes_on_array_expressed = sum(mean_log2 > 7),
                  share_of_expressed_genes_covered = sum(mean_log2[on_array] > 7) / sum(mean_log2 > 7)))
write_json(out, file.path(a[2], "table3.json"), auto_unbox = TRUE, pretty = TRUE, digits = NA)

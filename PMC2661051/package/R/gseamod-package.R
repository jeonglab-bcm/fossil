#' gseamod: modular gene set enrichment analysis
#'
#' The modular framework of Ackermann M and Strimmer K (2009). A general
#' modular framework for gene set enrichment analysis. BMC Bioinformatics
#' 10:47. doi:10.1186/1471-2105-10-47. Rebuilt from the paper's text in the
#' fossil repository (folder PMC2661051); the authors' R code is lost.
#'
#' Main entry point: \code{\link{gsea}}. Building blocks:
#' \code{\link{gene_stats}}, \code{\link{transform_stats}},
#' \code{\link{set_stats}}, \code{\link{global_stats}},
#' \code{\link{hotelling_stats}}. Simulation: \code{\link{simulate_ackermann}}
#' and \code{\link{detection_rates}}.
#'
#' @keywords internal
"_PACKAGE"

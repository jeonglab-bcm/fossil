#' Pathway deregulation scores
#'
#' Turns a genes x samples matrix into a pathways x samples matrix of pathway
#' deregulation scores (PDS) with \code{pathifier::quantify_pathways_deregulation}.
#' The data sets of the paper have no normal samples, so pathifier is run
#' without normals: each principal curve starts from the first principal
#' component and the score is the position along the curve from one end,
#' scaled to 0 to 1. Which end is 0 is arbitrary in pathifier; with
#' \code{orient = "mean"} each score is flipped, if needed, so that it rises
#' with the mean standardized expression of the pathway's genes.
#'
#' @param expr genes x samples matrix of log2 expression, gene symbols as row names.
#' @param genesets named list of gene symbol vectors.
#' @param normalize normalize between arrays with \code{limma::normalizeBetweenArrays}
#'   first: \code{"quantile"} (default), \code{"scale"} or \code{"none"}.
#' @param attempts,min_exp,min_std,maximize_stability passed to pathifier.
#' @param orient \code{"mean"} or \code{"pathifier"} (keep pathifier's ends).
#' @param seed random seed for pathifier's subsamplings (\code{NULL}: leave the RNG alone).
#'   The subsamplings are drawn once and shared by all pathways, so the score of a
#'   pathway does not depend on which other pathways are scored with it.
#' @param cores pathways are scored in parallel on this many cores (\code{parallel::mclapply}).
#' @param logfile pathifier's log file.
#' @return pathways x samples matrix; pathways pathifier skips are left out. Attribute
#'   \code{flipped} marks the pathways whose ends were swapped by \code{orient = "mean"}.
#' @export
pathway_scores <- function(expr, genesets, normalize = c("quantile", "scale", "none"),
                           attempts = 100, min_exp = 4, min_std = 0.4,
                           maximize_stability = TRUE, orient = c("mean", "pathifier"),
                           seed = 1, cores = 1, logfile = "") {
  normalize <- match.arg(normalize)
  orient <- match.arg(orient)
  if (normalize != "none") {
    expr <- limma::normalizeBetweenArrays(expr, method = normalize)
  }
  if (!is.null(seed)) set.seed(seed)
  n <- ncol(expr)
  m <- floor(0.8 * n)
  samplings <- t(vapply(seq_len(attempts), function(a) sort(sample(n, m)), numeric(m)))
  genes <- rownames(expr)
  one <- function(i) {
    res <- pathifier::quantify_pathways_deregulation(
      expr, genes, genesets[i], names(genesets)[i], attempts = attempts,
      maximize_stability = maximize_stability, logfile = logfile,
      samplings = samplings, min_exp = min_exp, min_std = min_std)
    if (length(res$sucess) == 0) return(NULL)
    list(score = as.vector(res$scores[[1]]), genes = res$genesinpathway[[1]])
  }
  idx <- seq_along(genesets)
  parts <- if (cores > 1) parallel::mclapply(idx, one, mc.cores = cores, mc.preschedule = FALSE)
           else lapply(idx, one)
  names(parts) <- names(genesets)
  parts <- parts[!vapply(parts, is.null, logical(1))]
  sc <- do.call(rbind, lapply(parts, `[[`, "score"))
  rownames(sc) <- names(parts)
  colnames(sc) <- colnames(expr)
  res <- list(genesinpathway = lapply(parts, `[[`, "genes"))
  flipped <- stats::setNames(rep(FALSE, nrow(sc)), rownames(sc))
  if (orient == "mean") {
    clipped <- pmax(expr, min_exp)
    for (p in rownames(sc)) {
      g <- intersect(res$genesinpathway[[p]], genes)
      z <- t(scale(t(clipped[g, , drop = FALSE])))
      z[!is.finite(z)] <- 0
      if (stats::cor(sc[p, ], colMeans(z)) < 0) {
        sc[p, ] <- 1 - sc[p, ]
        flipped[p] <- TRUE
      }
    }
  }
  attr(sc, "flipped") <- flipped
  sc
}

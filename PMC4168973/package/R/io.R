#' Read a GEO series matrix
#'
#' Reads the expression table and the sample header lines of a GEO series
#' matrix file (plain or gzipped).
#'
#' @param path file path.
#' @return A list with \code{expr} (probes x samples numeric matrix),
#'   \code{samples} (data frame with \code{geo_accession} and \code{title}) and
#'   \code{characteristics} (data frame, one column per \code{key: value} key
#'   found in the \code{!Sample_characteristics_ch1} lines).
#' @export
read_series_matrix <- function(path) {
  lines <- readLines(path, warn = FALSE)
  b <- grep("^!series_matrix_table_begin", lines)
  e <- grep("^!series_matrix_table_end", lines)
  unq <- function(x) gsub('^"|"$', "", x)
  field <- function(key) {
    l <- grep(paste0("^!Sample_", key, "\t"), lines, value = TRUE)
    lapply(strsplit(l, "\t"), function(v) unq(v[-1]))
  }
  tab <- utils::read.delim(text = lines[(b + 1):(e - 1)], check.names = FALSE,
                           stringsAsFactors = FALSE, quote = '"')
  expr <- as.matrix(tab[, -1])
  rownames(expr) <- tab[[1]]
  storage.mode(expr) <- "double"
  samples <- data.frame(geo_accession = field("geo_accession")[[1]],
                        title = field("title")[[1]], stringsAsFactors = FALSE)
  ch <- field("characteristics_ch1")
  chars <- list()
  for (v in ch) {
    has <- grepl(": ", v)
    if (!any(has)) next
    key <- sub(":.*$", "", v[which(has)[1]])
    val <- ifelse(has, sub("^[^:]*: ?", "", v), NA)
    chars[[key]] <- val
  }
  list(expr = expr, samples = samples,
       characteristics = as.data.frame(chars, check.names = FALSE, stringsAsFactors = FALSE))
}

#' Read a GEO platform annotation file
#'
#' @param path a GEO \code{GPLxxx.annot} file (plain or gzipped).
#' @return A data frame with columns \code{probe} and \code{symbol}; probes
#'   without a symbol or with several (\code{///}) are left out.
#' @export
read_gpl_annot <- function(path) {
  lines <- readLines(path, warn = FALSE)
  b <- grep("^!platform_table_begin", lines)
  e <- grep("^!platform_table_end", lines)
  tab <- utils::read.delim(text = lines[(b + 1):(e - 1)], check.names = FALSE,
                           stringsAsFactors = FALSE, quote = "")
  out <- data.frame(probe = tab[["ID"]], symbol = tab[["Gene symbol"]], stringsAsFactors = FALSE)
  out[out$symbol != "" & !grepl("///", out$symbol), ]
}

#' Collapse probes to genes
#'
#' Maps probe rows to gene symbols and, for a gene with several probes, takes
#' the geometric mean of the probes' log2 values, as the paper describes.
#'
#' @param expr probes x samples matrix of log2 values.
#' @param annot data frame with \code{probe} and \code{symbol}
#'   (\code{\link{read_gpl_annot}}).
#' @param floor values below this are set to it before the geometric mean
#'   (log2 values are positive for MAS5 data; the floor guards against zero).
#' @return genes x samples matrix, rows sorted by symbol.
#' @export
probes_to_genes <- function(expr, annot, floor = 1e-3) {
  a <- annot[annot$probe %in% rownames(expr), ]
  x <- expr[a$probe, , drop = FALSE]
  x[x < floor] <- floor
  lx <- log(x)
  s <- rowsum(lx, a$symbol, reorder = TRUE)
  n <- as.vector(table(a$symbol)[rownames(s)])
  exp(s / n)
}

#' Read a GMT gene set file
#'
#' @param path file path.
#' @return A named list of character vectors.
#' @export
read_gmt <- function(path) {
  l <- strsplit(readLines(path, warn = FALSE), "\t")
  sets <- lapply(l, function(v) unique(v[-(1:2)][v[-(1:2)] != ""]))
  stats::setNames(sets, vapply(l, `[`, "", 1))
}

#' Path to a bundled example file
#'
#' @param name file name in the package's \code{extdata} folder; \code{NULL}
#'   lists the files.
#' @return A file path, or the file names.
#' @export
example_path <- function(name = NULL) {
  if (is.null(name)) return(dir(system.file("extdata", package = "pdscox")))
  path <- system.file("extdata", name, package = "pdscox")
  if (path == "") stop("no example file ", name)
  path
}

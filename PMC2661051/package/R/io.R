#' Read GSEA file formats
#'
#' \code{read_gct} reads a GCT expression file (genes in rows),
#' \code{read_cls} a categorical CLS class file and \code{read_gmt} a GMT
#' gene set file.
#'
#' @param path file path.
#' @return \code{read_gct}: a numeric matrix with gene names as row names.
#'   \code{read_cls}: a character vector of class labels.
#'   \code{read_gmt}: a named list of character vectors.
#' @export
read_gct <- function(path) {
  x <- utils::read.delim(path, skip = 2, check.names = FALSE, stringsAsFactors = FALSE)
  m <- as.matrix(x[, -(1:2)])
  rownames(m) <- x[[1]]
  m
}

#' @rdname read_gct
#' @export
read_cls <- function(path) {
  l <- readLines(path, warn = FALSE)
  strsplit(trimws(l[3]), "[[:space:]]+")[[1]]
}

#' @rdname read_gct
#' @export
read_gmt <- function(path) {
  l <- strsplit(readLines(path, warn = FALSE), "\t")
  sets <- lapply(l, function(v) unique(v[-(1:2)][v[-(1:2)] != ""]))
  stats::setNames(sets, vapply(l, `[`, "", 1))
}

#' Path to a bundled example file
#'
#' @param name file name in the package's \code{extdata} folder; empty to
#'   list the files.
#' @export
example_path <- function(name = NULL) {
  if (is.null(name)) return(dir(system.file("extdata", package = "gseamod")))
  path <- system.file("extdata", name, package = "gseamod")
  if (path == "") stop("no example file ", name)
  path
}

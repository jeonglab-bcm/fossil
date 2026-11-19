#' Path to a bundled example file
#'
#' @param name File name in the package's `extdata` folder, or missing to list them.
#' @export
example_path <- function(name = NULL) {
  if (is.null(name)) return(dir(system.file("extdata", package = "hkselect")))
  p <- system.file("extdata", name, package = "hkselect", mustWork = FALSE)
  if (!nzchar(p)) stop("no example file ", name)
  p
}

#' Read an expression table
#'
#' Reads a CSV file with one row per sample: a sample-name column, an optional `tissue` column,
#' and one column per gene with positive expression levels (relative copy numbers).
#'
#' @param path CSV file.
#' @param sample Name of the sample column.
#' @return List with `expr` (numeric matrix, samples by genes, row names the samples) and
#'   `tissue` (factor in order of first appearance, or NULL).
#' @export
read_expression <- function(path, sample = "sample") {
  x <- utils::read.csv(path, check.names = FALSE, stringsAsFactors = FALSE)
  if (!sample %in% names(x)) stop("no column ", sample)
  tissue <- if ("tissue" %in% names(x)) factor(x$tissue, levels = unique(x$tissue)) else NULL
  genes <- setdiff(names(x), c(sample, "tissue"))
  expr <- as.matrix(x[genes]); rownames(expr) <- x[[sample]]
  list(expr = check_expr(expr), tissue = tissue)
}

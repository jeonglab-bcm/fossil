#' Path to a bundled example file
#'
#' @param name File name in the package's \code{extdata} folder.
#' @export
example_path <- function(name = "example_genotypes.csv") {
  p <- system.file("extdata", name, package = "epiforest")
  if (!nzchar(p)) stop("no bundled file named ", name)
  p
}

#' Read a genotype table
#'
#' A CSV file with a \code{status} column (1 case, 0 control) and one column per SNP holding 0, 1
#' or 2 copies of the minor allele.
#'
#' @param path File path.
#' @return A list with \code{geno} (integer matrix with SNP names) and \code{status}.
#' @export
read_genotypes <- function(path) {
  d <- utils::read.csv(path, check.names = FALSE)
  if (!"status" %in% names(d)) stop("the file needs a 'status' column")
  status <- as.integer(d$status)
  geno <- as.matrix(d[, setdiff(names(d), "status"), drop = FALSE])
  storage.mode(geno) <- "integer"
  .check_geno(geno, status)
  list(geno = geno, status = status)
}

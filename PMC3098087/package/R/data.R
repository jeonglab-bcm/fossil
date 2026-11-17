#' Simulate two-class data as in Blagus and Lusa (2010)
#'
#' Independent N(0, 1) variables; in Class 2 the first `p_de` variables have mean `mu2`.
#' Class 1 samples come first.
#'
#' @param n1,n2 samples in Class 1 and Class 2.
#' @param p number of variables.
#' @param p_de number of variables whose mean differs (0 for the null case).
#' @param mu2 mean of the differing variables in Class 2.
#' @return A list with `x` (n x p matrix) and `y` (integer labels 1 and 2).
#' @export
simulate_data <- function(n1, n2, p, p_de = 0, mu2 = 0) {
  n <- n1 + n2
  x <- matrix(rnorm(n * p), nrow = n, ncol = p)
  if (p_de > 0 && n2 > 0 && mu2 != 0) {
    rows <- n1 + seq_len(n2)
    x[rows, seq_len(p_de)] <- x[rows, seq_len(p_de)] + mu2
  }
  list(x = x, y = c(rep(1L, n1), rep(2L, n2)))
}

#' Mean-center samples or variables
#'
#' "samples" subtracts each sample's mean over all variables; "variables" subtracts each
#' variable's mean over the samples of `x`; "none" returns `x`. The paper centers the training
#' and the test set separately.
#'
#' @param x numeric matrix, samples in rows.
#' @param how one of "samples", "variables", "none".
#' @export
center_data <- function(x, how = c("samples", "variables", "none")) {
  how <- match.arg(how)
  if (how == "samples") return(x - rowMeans(x))
  if (how == "variables") return(sweep(x, 2, colMeans(x)))
  x
}

#' Two-sample t statistics with equal variances, one per column
#'
#' @param x numeric matrix, samples in rows.
#' @param y labels 1 and 2.
#' @export
t_statistics <- function(x, y) {
  i1 <- y == 1
  i2 <- !i1
  n1 <- sum(i1)
  n2 <- sum(i2)
  if (n1 < 2 || n2 < 2) stop("each class needs at least two samples")
  m1 <- colMeans(x[i1, , drop = FALSE])
  m2 <- colMeans(x[i2, , drop = FALSE])
  ss1 <- colSums(sweep(x[i1, , drop = FALSE], 2, m1)^2)
  ss2 <- colSums(sweep(x[i2, , drop = FALSE], 2, m2)^2)
  sp2 <- (ss1 + ss2) / (n1 + n2 - 2)
  (m1 - m2) / sqrt(sp2 * (1 / n1 + 1 / n2))
}

#' Select the G variables with the largest absolute t statistic
#'
#' @param x numeric matrix, samples in rows.
#' @param y labels 1 and 2.
#' @param G number of variables to keep; all variables when `G >= ncol(x)`.
#' @return Column indices of the selected variables, largest |t| first.
#' @export
select_variables <- function(x, y, G = 40) {
  p <- ncol(x)
  if (G >= p) return(seq_len(p))
  order(-abs(t_statistics(x, y)))[seq_len(G)]
}

#' Path to a bundled example file
#' @param name file name in `inst/extdata`.
#' @export
example_path <- function(name) {
  path <- system.file("extdata", name, package = "multds")
  if (!nzchar(path)) stop("no example file named ", name)
  path
}

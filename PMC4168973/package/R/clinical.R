#' Code clinical features for the clinical and combined models
#'
#' Codes grade (1 to 3), tumour size (mm), p53 (1 = mutant), lymph node
#' status (1 = positive), ER and PgR status (1 = positive) and age as numbers,
#' fills missing values with the column median (the paper does not say how
#' it handled them), and standardizes each column to mean 0 and standard
#' deviation 1, as the paper does before the combined model.
#'
#' @param clin data frame with any of the columns \code{grade}, \code{size_mm},
#'   \code{p53}, \code{node}, \code{er}, \code{pgr}, \code{age}.
#' @param features which of these to use.
#' @param center,scale optional centering and scaling values (from the training
#'   set) to apply instead of the data's own.
#' @return samples x features matrix with attributes \code{center} and \code{scale}.
#' @export
clinical_matrix <- function(clin, features = c("grade", "size_mm", "p53", "node"),
                            center = NULL, scale = NULL) {
  x <- as.matrix(clin[, features, drop = FALSE])
  storage.mode(x) <- "double"
  for (j in seq_len(ncol(x))) {
    v <- x[, j]
    v[is.na(v)] <- stats::median(v, na.rm = TRUE)
    x[, j] <- v
  }
  standardize(x, center, scale)
}

#' Standardize columns
#'
#' @param x numeric matrix.
#' @param center,scale optional values to use instead of the column means and
#'   standard deviations.
#' @return The standardized matrix with attributes \code{center} and \code{scale}.
#' @export
standardize <- function(x, center = NULL, scale = NULL) {
  if (is.null(center)) center <- colMeans(x)
  if (is.null(scale)) scale <- apply(x, 2, stats::sd)
  scale[scale == 0] <- 1
  z <- sweep(sweep(x, 2, center), 2, scale, "/")
  attr(z, "center") <- center
  attr(z, "scale") <- scale
  z
}

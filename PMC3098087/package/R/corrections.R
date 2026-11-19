#' Over-sampling and down-sizing
#'
#' `oversample()` replicates max(n1, n2) - min(n1, n2) randomly chosen minority samples (with
#' replacement), giving a training set of 2 max(n1, n2). `downsize()` keeps min(n1, n2) randomly
#' chosen majority samples, giving 2 min(n1, n2).
#' @param y labels 1 and 2.
#' @return Row indices of the corrected training set.
#' @export
oversample <- function(y) {
  n1 <- sum(y == 1)
  n2 <- sum(y == 2)
  if (n1 == n2) return(seq_along(y))
  minority <- if (n1 < n2) 1L else 2L
  idx <- which(y == minority)
  extra <- idx[sample.int(length(idx), abs(n1 - n2), replace = TRUE)]
  c(seq_along(y), extra)
}

#' @rdname oversample
#' @export
downsize <- function(y) {
  n1 <- sum(y == 1)
  n2 <- sum(y == 2)
  if (n1 == n2) return(seq_along(y))
  minority <- if (n1 < n2) 1L else 2L
  keep_min <- which(y == minority)
  maj <- which(y != minority)
  keep_maj <- maj[sample.int(length(maj), length(keep_min))]
  sort(c(keep_min, keep_maj))
}

#' Multiple down-sizing (MultDS)
#'
#' Asymmetric bagging with variable selection inside each bag: `B` down-sized training sets keep
#' every minority sample and a random subset of the majority class of the same size; in each, the
#' `G` variables with the largest |t| are selected and the classifiers are trained; each test sample
#' goes to the class with more votes. With `B` odd there are no ties.
#'
#' @param methods classifier names.
#' @param xtr,xte training and test matrices (all variables; selection happens inside).
#' @param ytr training labels.
#' @param G variables to select in each down-sized set.
#' @param B number of down-sized training sets (101 in the paper).
#' @param center centering applied to each down-sized training set ("variables") or nothing
#'   (samples are centered beforehand, which does not depend on the training set).
#' @return As [fit_predict()]; `score` is the share of votes for Class 1.
#' @export
multds_predict <- function(methods, xtr, ytr, xte, G = 40, B = 101,
                           center = c("none", "variables")) {
  center <- match.arg(center)
  votes <- matrix(0, nrow(xte), length(methods), dimnames = list(NULL, methods))
  for (b in seq_len(B)) {
    idx <- downsize(ytr)
    xb <- xtr[idx, , drop = FALSE]
    yb <- ytr[idx]
    if (center == "variables") xb <- center_data(xb, "variables")
    sel <- select_variables(xb, yb, G)
    fp <- fit_predict(methods, xb[, sel, drop = FALSE], yb, xte[, sel, drop = FALSE])
    for (m in methods) votes[, m] <- votes[, m] + (fp[[m]]$pred == 1L)
  }
  stats::setNames(lapply(methods, function(m) {
    share <- votes[, m] / B
    list(pred = ifelse(share > 0.5, 1L, ifelse(share < 0.5, 2L, sample(1:2, length(share), TRUE))),
         score = share)
  }), methods)
}

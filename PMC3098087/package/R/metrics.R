#' Area under the ROC curve
#'
#' The Mann-Whitney form (ties count one half), equal to the C index of `Hmisc::somers2`.
#' @param score larger means Class 1.
#' @param truth labels 1 and 2.
#' @return The AUC, or NA when the test set holds one class only.
#' @export
auc_score <- function(score, truth) {
  pos <- truth == 1
  n1 <- sum(pos)
  n2 <- sum(!pos)
  if (n1 == 0 || n2 == 0) return(NA_real_)
  r <- rank(score)
  (sum(r[pos]) - n1 * (n1 + 1) / 2) / (n1 * n2)
}

#' Predictive values (Eq. 6)
#' @param pa1,pa2 class-specific predictive accuracies.
#' @param kappa1 proportion of Class 1 in the population.
#' @return `c(PV1, PV2)`; NA where the denominator is zero.
#' @export
predictive_values <- function(pa1, pa2, kappa1) {
  d1 <- kappa1 * pa1 + (1 - kappa1) * (1 - pa2)
  d2 <- (1 - kappa1) * pa2 + kappa1 * (1 - pa1)
  c(PV1 = if (is.na(d1) || d1 == 0) NA_real_ else kappa1 * pa1 / d1,
    PV2 = if (is.na(d2) || d2 == 0) NA_real_ else (1 - kappa1) * pa2 / d2)
}

#' Evaluate predictions on a test set
#'
#' @param truth,pred labels 1 and 2.
#' @param score larger means Class 1 (for the AUC).
#' @param kappa1 assumed proportion of Class 1 in the population, for the predictive values
#'   (the training proportion unless stated, as in the paper).
#' @return Named vector: PA, PA1, PA2, PV1, PV2, AUC.
#' @export
evaluate <- function(truth, pred, score, kappa1) {
  pa1 <- if (any(truth == 1)) mean(pred[truth == 1] == 1) else NA_real_
  pa2 <- if (any(truth == 2)) mean(pred[truth == 2] == 2) else NA_real_
  c(PA = mean(pred == truth), PA1 = pa1, PA2 = pa2, predictive_values(pa1, pa2, kappa1),
    AUC = auc_score(score, truth))
}

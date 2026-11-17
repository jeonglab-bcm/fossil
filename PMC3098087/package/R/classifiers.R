#' Names of the classifiers
#'
#' The nine classifiers of the paper, and the two threshold variants (RF-THR, PLR-THR).
#' @param thr include RF-THR and PLR-THR.
#' @export
classifier_names <- function(thr = FALSE) {
  base <- c("1-NN", "3-NN", "5-NN", "DLDA", "DQDA", "RF", "SVM", "PAM", "PLR")
  if (thr) c(base, "RF-THR", "PLR-THR") else base
}

diag_da <- function(xtr, ytr, xte, pool) {
  i1 <- ytr == 1
  i2 <- !i1
  n <- length(ytr)
  m1 <- colMeans(xtr[i1, , drop = FALSE])
  m2 <- colMeans(xtr[i2, , drop = FALSE])
  v1 <- apply(xtr[i1, , drop = FALSE], 2, var)
  v2 <- apply(xtr[i2, , drop = FALSE], 2, var)
  if (pool) {
    vp <- ((sum(i1) - 1) * v1 + (sum(i2) - 1) * v2) / (n - 2)
    d1 <- colSums((t(xte) - m1)^2 / vp)
    d2 <- colSums((t(xte) - m2)^2 / vp)
  } else {
    d1 <- colSums((t(xte) - m1)^2 / v1) + sum(log(v1))
    d2 <- colSums((t(xte) - m2)^2 / v2) + sum(log(v2))
  }
  # Eq. 1 and 2: Class 1 when its discriminant is not larger (ties go to Class 1, as in
  # sma::stat.diag.da, which takes the first minimum).
  list(pred = ifelse(d1 <= d2, 1L, 2L), score = d2 - d1)
}

#' Diagonal linear and quadratic discriminant analysis (Eq. 1 and 2)
#'
#' The rules of `sma::stat.diag.da` (pool = 1 and pool = 0), with the difference of the two
#' discriminants as a score (larger means Class 1).
#' @param xtr,xte training and test matrices, samples in rows.
#' @param ytr training labels 1 and 2.
#' @export
dlda <- function(xtr, ytr, xte) diag_da(xtr, ytr, xte, pool = TRUE)

#' @rdname dlda
#' @export
dqda <- function(xtr, ytr, xte) diag_da(xtr, ytr, xte, pool = FALSE)

knn_fit <- function(xtr, ytr, xte, k) {
  pr <- class::knn(xtr, xte, factor(ytr, levels = 1:2), k = k, prob = TRUE)
  pred <- as.integer(as.character(pr))
  prob <- attr(pr, "prob")
  list(pred = pred, score = ifelse(pred == 1L, prob, 1 - prob))
}

rf_fit <- function(xtr, ytr, xte, k1) {
  n <- length(ytr)
  w <- c(sum(ytr == 1), sum(ytr == 2)) / n
  fit <- randomForest::randomForest(xtr, factor(ytr, levels = 1:2), classwt = w)
  prob <- predict(fit, xte, type = "prob")[, "1"]
  pred <- as.integer(as.character(predict(fit, xte, type = "response")))
  list(rf = list(pred = pred, score = prob),
       thr = list(pred = ifelse(prob > k1, 1L, 2L), score = prob))
}

svm_fit <- function(xtr, ytr, xte) {
  n <- length(ytr)
  w <- c("1" = sum(ytr == 1) / n, "2" = sum(ytr == 2) / n)
  fit <- e1071::svm(xtr, factor(ytr, levels = 1:2), kernel = "linear", scale = FALSE,
                    class.weights = w)
  pr <- predict(fit, xte, decision.values = TRUE)
  dv <- attr(pr, "decision.values")
  # Decision values are oriented by the label order of the fit ("1/2" or "2/1").
  sgn <- if (colnames(dv)[1] == "1/2") 1 else -1
  list(pred = as.integer(as.character(pr)), score = sgn * dv[, 1])
}

pam_fit <- function(xtr, ytr, xte) {
  dat <- list(x = t(xtr), y = factor(ytr, levels = 1:2))
  utils::capture.output(fit <- pamr::pamr.train(dat))
  # The largest threshold with the smallest training error.
  thr <- max(fit$threshold[fit$errors == min(fit$errors)])
  pred <- as.integer(as.character(pamr::pamr.predict(fit, t(xte), thr, type = "class")))
  post <- pamr::pamr.predict(fit, t(xte), thr, type = "posterior")
  list(pred = pred, score = post[, "1"])
}

plr_fit <- function(xtr, ytr, xte, k1) {
  y01 <- ifelse(ytr == 1, 1, 0)
  fit <- stepPlr::plr(xtr, y01, lambda = 1)
  p <- as.numeric(stepPlr::predict.plr(fit, newx = xte, type = "response"))
  pred <- ifelse(p > 0.5, 1L, ifelse(p < 0.5, 2L, sample(1:2, length(p), replace = TRUE)))
  list(plr = list(pred = as.integer(pred), score = p),
       thr = list(pred = ifelse(p > k1, 1L, 2L), score = p))
}

#' Train classifiers and predict a test set
#'
#' @param methods classifier names from [classifier_names()].
#' @param xtr,xte training and test matrices (samples in rows, selected variables only).
#' @param ytr training labels 1 and 2.
#' @return A named list; each element has `pred` (labels 1 and 2) and `score` (larger means
#'   Class 1, used for the AUC).
#' @export
fit_predict <- function(methods, xtr, ytr, xte) {
  if (length(unique(ytr)) != 2) stop("the training set needs both classes")
  xtr <- as.matrix(xtr)
  xte <- as.matrix(xte)
  k1 <- mean(ytr == 1)
  out <- list()
  for (m in methods) {
    if (!is.null(out[[m]])) next
    res <- switch(m,
      "1-NN" = knn_fit(xtr, ytr, xte, 1),
      "3-NN" = knn_fit(xtr, ytr, xte, 3),
      "5-NN" = knn_fit(xtr, ytr, xte, 5),
      "DLDA" = dlda(xtr, ytr, xte),
      "DQDA" = dqda(xtr, ytr, xte),
      "SVM" = svm_fit(xtr, ytr, xte),
      "PAM" = pam_fit(xtr, ytr, xte),
      "RF" = , "RF-THR" = {
        r <- rf_fit(xtr, ytr, xte, k1)
        if ("RF" %in% methods) out[["RF"]] <- r$rf
        if ("RF-THR" %in% methods) out[["RF-THR"]] <- r$thr
        NULL
      },
      "PLR" = , "PLR-THR" = {
        r <- plr_fit(xtr, ytr, xte, k1)
        if ("PLR" %in% methods) out[["PLR"]] <- r$plr
        if ("PLR-THR" %in% methods) out[["PLR-THR"]] <- r$thr
        NULL
      },
      stop("unknown classifier ", m))
    if (!is.null(res)) out[[m]] <- res
  }
  out[methods]
}

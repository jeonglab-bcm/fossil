# The motivating data: German Breast Cancer Study Group 2 (Sauerbrei et al. 1999), as
# TH.data::GBSG2. The covariates follow Table 1 of Marshall et al. (2010).

#' Covariates of the motivating breast cancer data
#'
#' Codes GBSG2 as the eight covariates of Table 1 of Marshall et al. (2010): X1 age,
#' X2 positive lymph nodes, X3 progesterone receptor (fmol), X4 oestrogen receptor (fmol),
#' X5 hormonal treatment (1 = yes), X6 menopausal status (1 = post), X7 tumour grade
#' (1 = grade II or III), X8 tumour size (mm), with recurrence-free survival `time`
#' (days) and `status` (1 = event).
#'
#' @param data A data frame with the columns of `TH.data::GBSG2`. When `NULL`, the
#'   data are loaded from the TH.data package.
#' @return A data frame with columns X1 to X8, time and status, on the original scales.
#' @export
gbsg_covariates <- function(data = NULL) {
  if (is.null(data)) {
    if (!requireNamespace("TH.data", quietly = TRUE))
      stop("gbsg_covariates() needs the TH.data package, or pass the data")
    env <- new.env()
    utils::data("GBSG2", package = "TH.data", envir = env)
    data <- env$GBSG2
  }
  need <- c("horTh", "age", "menostat", "tsize", "tgrade", "pnodes", "progrec",
            "estrec", "time", "cens")
  miss <- setdiff(need, names(data))
  if (length(miss)) stop("data lacks columns: ", paste(miss, collapse = ", "))
  data.frame(
    X1 = as.numeric(data$age),
    X2 = as.numeric(data$pnodes),
    X3 = as.numeric(data$progrec),
    X4 = as.numeric(data$estrec),
    X5 = as.integer(as.character(data$horTh) == "yes"),
    X6 = as.integer(as.character(data$menostat) == "Post"),
    X7 = as.integer(as.character(data$tgrade) != "I"),
    X8 = as.numeric(data$tsize),
    time = as.numeric(data$time),
    status = as.integer(data$cens)
  )
}

#' Transform the covariates as in Table 1
#'
#' log for X2 and X8, log(x + 1) for X3 and X4; the others unchanged.
#' @param x A data frame from [gbsg_covariates()].
#' @return A data frame with X1 to X8 on the transformed scale.
#' @export
transform_covariates <- function(x) {
  data.frame(X1 = x$X1, X2 = log(x$X2), X3 = log(x$X3 + 1), X4 = log(x$X4 + 1),
             X5 = x$X5, X6 = x$X6, X7 = x$X7, X8 = log(x$X8))
}

#' Tumour size group (Table 1): 1 = up to 20 mm, 2 = 21 to 30 mm, 3 = over 30 mm
#' @param size Tumour size in mm.
#' @return Integer group 1, 2 or 3.
#' @export
size_group <- function(size) {
  as.integer(cut(size, c(-Inf, 20, 30, Inf), labels = FALSE))
}

#' Sample skewness, b1 = m3 / s^3 with the n - 1 standard deviation
#'
#' The definition that gives the skewness values printed in the paper's text.
#' @param x A numeric vector.
#' @param type 1 (g1, moments), 2 (G1, SAS and SPSS) or 3 (b1, the default).
#' @return The skewness.
#' @export
skewness <- function(x, type = 3) {
  x <- x[is.finite(x)]
  n <- length(x)
  m <- mean(x)
  g1 <- mean((x - m)^3) / mean((x - m)^2)^1.5
  switch(as.character(type),
         "1" = g1,
         "2" = g1 * sqrt(n * (n - 1)) / (n - 2),
         "3" = g1 * ((n - 1) / n)^1.5,
         stop("type must be 1, 2 or 3"))
}

#' Fit the full Cox model of the paper
#'
#' All eight covariates with linear terms and X8 as two dummies (21 to 30 mm, over 30 mm).
#' @param x A data frame with X1 to X7, the tumour size group `X8g` (1 to 3) or the
#'   size `X8` in mm, and time and status.
#' @param ties Tie handling passed to [survival::coxph()].
#' @return A `coxph` fit.
#' @export
fit_full_cox <- function(x, ties = "efron") {
  g <- if (!is.null(x$X8g)) x$X8g else size_group(x$X8)
  x$X8d1 <- as.integer(g == 2)
  x$X8d2 <- as.integer(g == 3)
  survival::coxph(survival::Surv(time, status) ~ X1 + X2 + X3 + X4 + X5 + X6 + X7 +
                    X8d1 + X8d2, data = x, ties = ties, x = TRUE)
}

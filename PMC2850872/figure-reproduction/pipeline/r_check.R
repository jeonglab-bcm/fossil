# Check the Python method against independent R implementations, on the reproduction's own split:
#   survey::svyglm   design-based logistic regression (the stand-in for SUDAAN 9) -> beta
#   pROC::roc.test   DeLong test of the SVM and logistic AUCs                      -> AUCs, p
#   e1071::svm       LIBSVM through R, with the C and gamma our grid search chose   -> decision values
#
# Usage: Rscript r_check.R CHECK_DIR OUT.json
# CHECK_DIR holds, per scheme S (I, II), the files written by run_models.py:
#   r_input_S.csv  (train/test flag, balanced flag, y, design variables, features, python scores)
#   r_params_S.json (kernel, C, gamma, python beta)
suppressPackageStartupMessages({
  library(survey)
  library(pROC)
  library(e1071)
  library(jsonlite)
})
args <- commandArgs(trailingOnly = TRUE)
dir <- args[1]
out <- args[2]
options(survey.lonely.psu = "adjust")
res <- list(versions = list(R = as.character(getRversion()),
                            survey = as.character(packageVersion("survey")),
                            pROC = as.character(packageVersion("pROC")),
                            e1071 = as.character(packageVersion("e1071"))))
for (s in c("I", "II")) {
  d <- read.csv(file.path(dir, paste0("r_input_", s, ".csv")))
  p <- fromJSON(file.path(dir, paste0("r_params_", s, ".json")))
  feats <- grep("^f_", names(d), value = TRUE)
  tr <- d[d$set == "train", ]
  te <- d[d$set == "test", ]
  # Design-based logistic regression on the whole training set, six-year MEC weights.
  des <- svydesign(ids = ~sdmvpsu, strata = ~sdmvstra, weights = ~weight_mec6, nest = TRUE, data = tr)
  f <- as.formula(paste("case ~", paste(feats, collapse = " + ")))
  fit <- svyglm(f, design = des, family = quasibinomial())
  beta <- unname(coef(fit))
  lp <- as.vector(cbind(1, as.matrix(te[, feats])) %*% beta)
  r_svm <- roc(te$case, te$svm_score, levels = c(0, 1), direction = "<", quiet = TRUE)
  r_mlr <- roc(te$case, lp, levels = c(0, 1), direction = "<", quiet = TRUE)
  dl <- roc.test(r_svm, r_mlr, method = "delong", paired = TRUE)
  # LIBSVM through e1071 on the balanced training sample, same kernel, C and gamma.
  bal <- tr[tr$balanced == 1, ]
  y <- factor(ifelse(bal$case == 1, "case", "non"), levels = c("case", "non"))
  kern <- c(linear = "linear", poly = "polynomial", rbf = "radial", sigmoid = "sigmoid")[[p$kernel]]
  m <- svm(x = as.matrix(bal[, feats]), y = y, kernel = kern, cost = p$C, gamma = p$gamma,
           degree = 3, coef0 = 0, scale = FALSE, tolerance = 0.001, shrinking = TRUE)
  dv <- attr(predict(m, as.matrix(te[, feats]), decision.values = TRUE), "decision.values")
  # e1071 orients the decision value by the first level of y ("case").
  dv <- as.vector(dv[, 1]) * ifelse(colnames(dv)[1] == "case/non", 1, -1)
  res[[s]] <- list(
    beta_r = beta,
    beta_python = p$beta,
    beta_max_abs_diff = max(abs(beta - unlist(p$beta))),
    auc_svm_r = as.numeric(auc(r_svm)),
    auc_mlr_r = as.numeric(auc(r_mlr)),
    delong_p_r = unname(dl$p.value),
    delong_z_r = unname(dl$statistic),
    e1071_auc = as.numeric(auc(roc(te$case, dv, levels = c(0, 1), direction = "<", quiet = TRUE))),
    e1071_vs_python_max_abs_diff = max(abs(dv - te$svm_score)),
    e1071_vs_python_cor = cor(dv, te$svm_score)
  )
}
write_json(res, out, auto_unbox = TRUE, digits = NA, pretty = TRUE)
cat(toJSON(res, auto_unbox = TRUE, digits = 8, pretty = TRUE), "\n")

# Expected output for the bundled example, from implementations independent of this package:
#   e1071::svm      LIBSVM's C++ code through R    -> test decision values (RBF, C = 2, gamma = 2)
#   survey::svyglm  weighted logistic regression   -> beta
#   pROC            AUCs and the DeLong test       -> auc_svm, auc_logistic, delong_p
#
# Usage (from PMC2850872/package):
#   Rscript scripts/expected_from_r.R src/diabclass/data/nhanes_example.csv src/diabclass/data
# Tested with R 4.3.3, e1071 1.7-16, survey 4.5, pROC 1.19.1.
suppressPackageStartupMessages({
  library(e1071)
  library(survey)
  library(pROC)
  library(jsonlite)
})
args <- commandArgs(trailingOnly = TRUE)
d <- read.csv(args[1])
outdir <- args[2]
race <- c(nh_white = -1, nh_black = -0.5, mexican_american = 0, other = 0.5, other_hispanic = 1)
X <- cbind(
  family_history = ifelse(d$family_history == 1, 1, -1),
  age = d$age / 100,
  race = unname(race[d$race]),
  weight = d$weight / 200,
  height = d$height / 200,
  waist = d$waist / 200,
  bmi = d$bmi / 100,
  hypertension = ifelse(d$hypertension == 1, 1, -1)
)
tr <- d$set == "train"
te <- d$set == "test"
C <- 2
gamma <- 2
y <- factor(ifelse(d$case[tr] == 1, "case", "non"), levels = c("case", "non"))
m <- svm(x = X[tr, ], y = y, kernel = "radial", cost = C, gamma = gamma, scale = FALSE,
         tolerance = 1e-5, shrinking = TRUE)
dv <- attr(predict(m, X[te, ], decision.values = TRUE), "decision.values")
dv <- as.vector(dv[, 1]) * ifelse(colnames(dv)[1] == "case/non", 1, -1)
dat <- data.frame(case = d$case, X, w = d$weight_mec6)
des <- svydesign(ids = ~1, weights = ~w, data = dat[tr, ])
fit <- svyglm(case ~ family_history + age + race + weight + height + waist + bmi + hypertension,
              design = des, family = quasibinomial(), control = glm.control(epsilon = 1e-12, maxit = 100))
beta <- unname(coef(fit))
lp <- as.vector(cbind(1, X[te, ]) %*% beta)
p <- 1 / (1 + exp(-lp))
r1 <- roc(d$case[te], dv, levels = c(0, 1), direction = "<", quiet = TRUE)
r2 <- roc(d$case[te], p, levels = c(0, 1), direction = "<", quiet = TRUE)
dl <- roc.test(r1, r2, method = "delong", paired = TRUE)
write.csv(data.frame(id = d$id[te], decision_value = sprintf("%.8f", dv), case = d$case[te]),
          file.path(outdir, "nhanes_example_expected_svm.csv"), row.names = FALSE, quote = FALSE)
write_json(list(
  source = "R e1071 (LIBSVM), survey::svyglm, pROC; see scripts/expected_from_r.R",
  versions = list(R = as.character(getRversion()), e1071 = as.character(packageVersion("e1071")),
                  survey = as.character(packageVersion("survey")), pROC = as.character(packageVersion("pROC"))),
  svm = list(kernel = "rbf", C = C, gamma = gamma),
  beta = beta, auc_svm = as.numeric(auc(r1)), auc_logistic = as.numeric(auc(r2)),
  delong_p = unname(dl$p.value)
), file.path(outdir, "nhanes_example_expected.json"), auto_unbox = TRUE, digits = NA, pretty = TRUE)
cat("written\n")

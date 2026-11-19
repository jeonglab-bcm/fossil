# multds

Class prediction for high-dimensional class-imbalanced data: the classifiers, corrections and
measures of Blagus and Lusa (2010), rebuilt as an R package.

> Blagus R, Lusa L. Class prediction for high-dimensional class-imbalanced data.
> *BMC Bioinformatics* 11:523 (2010). [doi:10.1186/1471-2105-11-523](https://doi.org/10.1186/1471-2105-11-523)

The authors released no code. This package is written from the paper's Methods: t-test variable
selection on the training set (`select_variables`), nine classifiers (1-, 3- and 5-NN with
`class::knn`, DLDA and DQDA as in `sma::stat.diag.da`, random forest with `randomForest`, linear SVM
with `e1071::svm`, PAM with `pamr`, penalized logistic regression with `stepPlr::plr`, and the
threshold variants RF-THR and PLR-THR), over-sampling, down-sizing and multiple down-sizing
(`multds_predict`, asymmetric bagging with selection inside each bag), the predictive accuracies,
predictive values and AUC (`evaluate`), and the simulation design (`run_replicate`).

## Install

```r
remotes::install_github("jeonglab-bcm/fossil/PMC3098087/package")
```

## Quick start

```r
library(multds)
train <- read.csv(example_path("train.csv"))
test <- read.csv(example_path("test.csv"))
x <- center_data(as.matrix(train[, -1]), "samples")
xt <- center_data(as.matrix(test[, -1]), "samples")
set.seed(1)
fp <- multds_predict(c("DLDA", "PLR"), x, train$class, xt, G = 40, B = 101)
evaluate(test$class, fp$DLDA$pred, fp$DLDA$score, kappa1 = mean(train$class == 1))
```

The tutorial is in [`tutorial/TUTORIAL.md`](tutorial/TUTORIAL.md) (rendered from
`vignettes/tutorial.Rmd`).

## Why R

The paper's classifiers are R packages (class, randomForest, e1071, pamr, stepPlr, and sma for
DLDA and DQDA). A Python port would swap them for look-alikes that do not give the same
predictions, so the package is in R and depends on them; DLDA and DQDA are rewritten because sma no
longer installs, and are checked against its `stat.diag.da` (identical predictions on 18,000 test
samples, `figure-reproduction/output/port_check.json`).

## Choices the paper does not state

- Ties: DLDA and DQDA give ties to Class 1 (as `stat.diag.da`); PLR breaks ties at 0.5 at random
  (as stated); MultDS uses an odd number of bags.
- Scores for the AUC: the share of neighbour votes (k-NN), the difference of the discriminants
  (DLDA, DQDA), the forest's vote share (RF), the decision value (SVM), the posterior (PAM) and the
  fitted probability (PLR).
- SVM: cost 1 (the default) and class weights equal to the class proportions, as the text says.
- Over-sampling draws the replicated minority samples with replacement.

## Reproduction

The paper's simulations and the breast cancer application, rerun with this package:
[`PMC3098087/`](https://github.com/jeonglab-bcm/fossil/tree/main/PMC3098087).

## Licence

MIT. The package contains no code of the authors (none was released) and no code of sma.

multds tutorial
================

## What it does

Classifiers trained on class-imbalanced, high-dimensional data put most
new samples in the majority class, and selecting variables on the
training set makes it worse. multds rebuilds the classifiers, the
corrections (over-sampling, down-sizing and multiple down-sizing,
MultDS) and the measures of Blagus and Lusa (2010) so you can check a
classifier on your own data.

Blagus R, Lusa L. Class prediction for high-dimensional class-imbalanced
data. *BMC Bioinformatics* 11:523 (2010). <doi:10.1186/1471-2105-11-523>

## Install

``` r
remotes::install_github("jeonglab-bcm/fossil/PMC3098087/package")
```

``` r
library(multds)
packageVersion("multds")
#> [1] '0.1.0'
```

## Example input

A synthetic training set with 8 samples in Class 1 and 32 in Class 2,
and a balanced test set; 300 variables, the first 20 shifted by 0.8 in
Class 2.

``` r
train <- read.csv(example_path("train.csv"))
test <- read.csv(example_path("test.csv"))
dim(train)
#> [1]  40 301
table(train$class)
#> 
#>  1  2 
#>  8 32
table(test$class)
#> 
#>  1  2 
#> 10 10
train[1:3, 1:6]
#>   class    v001    v002   v003    v004    v005
#> 1     1 -0.9674 -1.5711 0.9392  0.7825  0.2491
#> 2     1  0.7043  1.1471 1.0937 -2.3148  0.5099
#> 3     1  0.0156 -0.2612 0.1957  0.4539 -1.5351
```

## Run the method

Centre each sample, select the 40 variables with the largest \|t\| on
the training set, and train DLDA and DQDA. Then the same with MultDS:
101 balanced training sets (all 8 Class 1 samples and 8 random Class 2
samples each), variables selected in each, a majority vote.

``` r
x <- center_data(as.matrix(train[, -1]), "samples")
xt <- center_data(as.matrix(test[, -1]), "samples")
sel <- select_variables(x, train$class, G = 40)
plain <- fit_predict(c("DLDA", "DQDA"), x[, sel], train$class, xt[, sel])
set.seed(1)
bagged <- multds_predict(c("DLDA", "DQDA"), x, train$class, xt, G = 40, B = 101)
k1 <- mean(train$class == 1)
round(rbind(
  "DLDA" = evaluate(test$class, plain$DLDA$pred, plain$DLDA$score, k1),
  "DQDA" = evaluate(test$class, plain$DQDA$pred, plain$DQDA$score, k1),
  "DLDA, MultDS" = evaluate(test$class, bagged$DLDA$pred, bagged$DLDA$score, k1),
  "DQDA, MultDS" = evaluate(test$class, bagged$DQDA$pred, bagged$DQDA$score, k1)), 2)
#>                PA PA1 PA2  PV1  PV2  AUC
#> DLDA         0.60 0.2 1.0 1.00 0.83 0.73
#> DQDA         0.50 0.0 1.0   NA 0.80 0.52
#> DLDA, MultDS 0.60 0.3 0.9 0.43 0.84 0.73
#> DQDA, MultDS 0.65 0.4 0.9 0.50 0.86 0.67
```

PA1 and PA2 are the predictive accuracies in Class 1 (the minority of
the training set) and Class 2; PV1 and PV2 the predictive values (Eq. 6,
with the training proportion of Class 1 as the population’s); AUC from
the scores. Compare PA1 without and with MultDS.

## Compare with the expected output

The expected selection comes from `stats::t.test`, and the expected
classes from `sma::stat.diag.da`, the function the paper used (see
`inst/extdata/README.md`).

``` r
expected_sel <- read.csv(example_path("expected_selected.csv"))
expected <- read.csv(example_path("expected_predictions.csv"))
same_sel <- setequal(colnames(x)[sel], expected_sel$variable)
n_dlda <- sum(plain$DLDA$pred == expected$DLDA)
n_dqda <- sum(plain$DQDA$pred == expected$DQDA)
cat(sprintf("Selected variables match: %s\nDLDA: %d of %d test samples match\nDQDA: %d of %d test samples match\n",
            same_sel, n_dlda, nrow(expected), n_dqda, nrow(expected)))
#> Selected variables match: TRUE
#> DLDA: 20 of 20 test samples match
#> DQDA: 20 of 20 test samples match
stopifnot(same_sel, n_dlda == nrow(expected), n_dqda == nrow(expected))
```

## Your own data

- Input: a numeric matrix with samples in rows and variables in columns,
  and labels 1 and 2.
- `center_data(x, "samples")` centres each sample (the paper’s default);
  centre the training and test sets separately. `"variables"` centres
  each variable and, in the paper, made imbalance worse.
- `select_variables(x, y, G)` keeps the G variables with the largest
  \|t\|; use it on the training set only.
- `fit_predict(methods, xtr, ytr, xte)` trains any of
  `classifier_names(thr = TRUE)` and returns, for each, `pred` (1 or 2)
  and `score` (larger means Class 1).
- `multds_predict()` runs MultDS with selection inside each balanced
  set; `downsize()` and `oversample()` return the rows of a single
  balanced training set.
- `evaluate(truth, pred, score, kappa1)` gives PA, PA1, PA2, PV1, PV2
  and AUC.
- `run_replicate()` and `run_setting()` run the paper’s simulation for
  any setting.

## The reproduction

The paper’s simulations and the breast cancer application are rerun with
this package in
[PMC3098087/figure-reproduction](https://github.com/jeonglab-bcm/fossil/tree/main/PMC3098087/figure-reproduction),
with the results page at
<https://jeonglab-bcm.github.io/fossil/PMC3098087/>.

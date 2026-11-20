misscox tutorial
================

## What it does

misscox rebuilds the simulation study of Marshall, Altman, Royston and
Holder (2010). It simulates prognostic cohorts like the German Breast
Cancer Study Group 2 data, deletes values of four covariates under MCAR,
MAR, MNAR or a combined mechanism, handles the missing data by complete
case analysis, single imputation or one of seven multiple imputation
methods, and fits the full Cox model with Rubin’s rules.

Marshall A, Altman DG, Royston P, Holder RL. Comparison of techniques
for handling missing covariate data within prognostic modelling studies:
a simulation study. *BMC Medical Research Methodology* 10:7 (2010).
<doi:10.1186/1471-2288-10-7>

## Install

``` r
remotes::install_github("jeonglab-bcm/fossil/PMC2824146/package")
```

``` r
library(misscox)
packageVersion("misscox")
#> [1] '0.1.0'
```

## Example input

The missingness design of the paper: the share of the incomplete cases
that miss each covariate, and each pair.

``` r
shares <- read.csv(example_path("missing_shares.csv"))
shares
#>        term share
#> 1        X3  0.70
#> 2        X2  0.55
#> 3        X5  0.20
#> 4        X8  0.10
#> 5 X2 and X3  0.35
#> 6 X5 and X2  0.10
#> 7 X8 and X3  0.05
```

And one simulated cohort of 1000 cases with 25% of cases made incomplete
under MAR.

``` r
x <- read.csv(example_path("example_cohort_mar25.csv"))
dim(x)
#> [1] 1000   10
head(x)
#>         X1        X2        X3        X4 X5 X6 X7 X8g        time status
#> 1 47.61286  2.481885 796.85030  27.70220  0  0  1   3   191.32690      0
#> 2 52.99994 13.904680  24.38085  29.04303  0  0  1   3    13.16238      1
#> 3 63.23062        NA        NA  30.75776  0  1  0   1 11076.40000      0
#> 4 55.21842  3.435015        NA  72.12158  1  1  1   3  4284.71500      1
#> 5 51.01565  2.276181   3.54417  18.44656  1  0  1   3  5290.49800      0
#> 6 67.70154  2.314044 330.85280 132.03690  0  0  1   3  2202.40700      1
colSums(is.na(x))
#>     X1     X2     X3     X4     X5     X6     X7    X8g   time status 
#>      0    167    180      0     62      0      0     30      0      0
mean(!complete.cases(x))
#> [1] 0.28
```

## Run the method

The odds ratios between the missingness indicators (Table 3) follow from
the design: the shares become whole cases of 1000, rounded half up.

``` r
t3 <- table3_odds_ratios()
t3
#>     pair      pct5    pct10     pct25    pct50     pct75
#> 1 X2|MX3 101.11765 45.50000 15.678161 5.500000 2.1749364
#> 2 X5|MX2  42.04348 20.77778  7.407080 3.000000 1.5147929
#> 3 X8|MX3  45.14062 14.23077  5.436728 1.923077 0.9236917
```

Handle the missing data of the example cohort with three of the methods
and fit the Cox model. Five imputations here to keep the tutorial quick;
the paper used twenty.

``` r
fits <- lapply(c("CC", "SI", "MICE_PMM_notrans"), function(m) handle_missing(x, m, m = 5, seed = 1))
res <- do.call(rbind, fits)
data.frame(method = c("CC", "SI", "MICE_PMM_notrans"), n = res$n_analysed,
           X2 = signif(res$est_X2, 3), se_X2 = signif(res$se_X2, 3),
           X3 = signif(res$est_X3, 3), se_X3 = signif(res$se_X3, 3))
#>             method    n     X2   se_X2       X3    se_X3
#> 1               CC  720 0.0460 0.00729 -0.00223 0.000360
#> 2               SI 1000 0.0447 0.00616 -0.00221 0.000316
#> 3 MICE_PMM_notrans 1000 0.0499 0.00779 -0.00227 0.000331
```

## Compare with the expected output

Table 3 as printed in the paper, at printed precision (half a unit in
the last digit):

``` r
exp <- read.csv(example_path("table3_expected.csv"), colClasses = "character")
printed_ok <- function(observed, printed) {
  d <- nchar(sub("^[^.]*\\.?", "", printed))
  abs(observed - as.numeric(printed)) <= 0.5 * 10^(-d) + 1e-12
}
ok <- sapply(c("pct5", "pct10", "pct25", "pct50", "pct75"), function(k) printed_ok(t3[[k]], exp[[k]]))
cat(sum(ok), "of", length(ok), "odds ratios match Table 3\n")
#> 15 of 15 odds ratios match Table 3
stopifnot(all(ok))
```

The full Cox model on the breast cancer data (`TH.data::GBSG2`) against
the paper’s linear predictor:

``` r
lp <- read.csv(example_path("lp_expected.csv"), colClasses = "character")
b <- coef(fit_full_cox(gbsg_covariates()))
ok <- printed_ok(unname(b), lp$printed)
data.frame(term = lp$term, paper = lp$printed, ours = signif(unname(b), 4), match = ok)
#>   term   paper       ours match
#> 1   X1 -0.0088 -0.0088410  TRUE
#> 2   X2   0.051  0.0507200  TRUE
#> 3   X3 -0.0023 -0.0022750  TRUE
#> 4   X4 0.00015  0.0001498  TRUE
#> 5   X5  -0.349 -0.3492000  TRUE
#> 6   X6   0.225  0.2253000  TRUE
#> 7   X7    0.67  0.6697000  TRUE
#> 8 X8d1   0.223  0.2230000  TRUE
#> 9 X8d2   0.331  0.3311000  TRUE
cat(sum(ok), "of", length(ok), "coefficients match the paper\n")
#> 9 of 9 coefficients match the paper
stopifnot(all(ok))
```

## Your own data

`handle_missing()` takes a data frame with columns `X1` to `X7`
(numeric; X5 to X7 coded 0/1), `X8g` (tumour size group 1, 2 or 3),
`time` (days) and `status` (1 = event), with `NA` where a value of X2,
X3, X5 or X8g is missing. The method is one of `method_labels()`: `CC`,
`SI`, `NORM`, `MIX`, `MIX_notrunc`, `MICE`, `MICE_PMM`,
`MICE_PMM_notrans`, `AREG`. The result has, for each coefficient, the
pooled estimate (`est_`), its standard error (`se_`), the Wald p-value
(`p_`) and the 95% interval (`lo_`, `hi_`), then the likelihood ratio
p-value, Nagelkerke’s R2, the D statistic, the predicted 2-year survival
at the mean covariates and the number of cases analysed.

To run the study itself: `generation_parameters(gbsg_covariates())`
builds the generator, `run_replicate()` runs one replicate over
mechanisms, levels and methods, and `summarise_replicates()` gives bias,
coverage and the other figure quantities.

## The full reproduction

The pipeline that reruns the paper’s study with this package, and
compares every table, figure point and claim with the paper:
<https://github.com/jeonglab-bcm/fossil/tree/main/PMC2824146>.

# epiforest

Random forest screening for epistatic interactions in case-control studies: the two-stage epiForest method of

> Jiang R, Tang W, Wu X, Fu W. A random forest approach to the detection of epistatic interactions in case-control studies. *BMC Bioinformatics* 10(Suppl 1):S65 (2009). [doi:10.1186/1471-2105-10-S1-S65](https://doi.org/10.1186/1471-2105-10-S1-S65)

- **Stage 1.** A random forest (R package randomForest) with every SNP as a three-level factor ranks the SNPs by gini importance. The sliding window sequential forward feature selection (SWSFS) adds SNPs in that order, fits a forest on the top i, and stops at the first i whose window [i − 20, i] has its smallest out-of-bag error at i − 20; the top i − 20 SNPs are the candidates.
- **Stage 2.** Hierarchical tests of the candidates with the B statistic of Zhang and Liu (2007): every SNP, then every pair (conditional on a SNP already reported, skipped when both were), then every triple, Bonferroni-corrected for all L SNPs screened (L, L(L−1)/2, L(L−1)(L−2)/6).

The authors' program is lost; this package rebuilds the method from the paper's text. It also has the paper's simulation design (`simulate_dataset`, `disease_model`: the disease models of Marchini, Donnelly and Cardon 2005) and its comparators (`chisq_single`, `stepwise_lr`). The reproduction of the paper with it is in [`PMC2648748/`](https://github.com/jeonglab-bcm/fossil/tree/main/PMC2648748) of the fossil repository.

## Install

```r
remotes::install_github("jeonglab-bcm/fossil/PMC2648748/package")
```

R 4.1 or later with randomForest 4.7 or later. Tested with R 4.3.3 and randomForest 4.7-1.1.

**Why R.** The paper ran its forests with the R package randomForest, and the method's gini importance and out-of-bag errors are that package's. The default rule (R when the method relies on R packages) gives R.

## Use

```r
library(epiforest)
ex <- read_genotypes(example_path())          # status (1 case, 0 control) + one column per SNP (0, 1, 2)
fit <- epiforest(ex$geno, ex$status, ntree = 500, window = 20, seed = 1)
fit$candidates                                # columns kept by SWSFS
fit$tests[fit$tests$reported, ]               # reported one-, two- and three-way tests
colnames(ex$geno)[fit$identified]
```

The pieces are exported too: `gini_importance`, `swsfs`, `hierarchical_tests`, `b_test` (the B statistic and the conditional B statistic for any sets of SNPs) and `b_shift`. The [tutorial](tutorial/TUTORIAL.md) runs the bundled example and checks it against its expected output.

## What the paper does not say, and what we chose

- **B statistic.** Pseudo-counts 0.5; the paper's formula has P1/P1 where P1/P0 is meant. The paper says 2B follows a "shifted" chi-squared distribution with 3^k − 1 degrees of freedom; `b_shift` derives the shift from Stirling's expansion of each Dirichlet-multinomial term. On data with no association the shifted statistic has the chi-squared mean and 5% tail for one- and two-way tests; three-way tests are conservative (about 2.8% below 0.05), because many of the 27 cells are sparse.
- **Conditional B.** The paper names it but does not give it. Here it compares cases' joint distribution over all the SNPs with a null in which the reported SNPs keep their association and the others are unlinked; its degrees of freedom, 3^k − 3^t, are the paper's.
- **Forests.** `ntree` is not given for the paper's simulations (500, randomForest's default, here); `mtry` is randomForest's default, floor(sqrt(number of SNPs)).
- **Missing genotypes** are not handled: impute or drop them first.

## How it was checked

- The B statistic and the chi-squared test against an independent NumPy and SciPy implementation on the example data (to 1e-8), and the B statistic's null distribution on simulated null data (PMC2648748/figure-reproduction/output/checks/bstat_null.json).
- The disease models reach their prevalence and marginal effect to 1e-6 in every one of the paper's 12 model and MAF settings.
- The whole simulation study of the paper (Figs 2 and 3) was rerun with this package; see the reproduction's README for what came back.

## Licence

MIT, see [LICENSE.md](LICENSE.md). The code is written from the paper; the example data are synthetic (see [inst/extdata/README.md](inst/extdata/README.md)).

# hkselect

Selecting housekeeper genes with heteroscedastic linear models, after Szabo A, Perou CM, Karaca M,
Perreard L, Palais R, Quackenbush JF, Bernard PS. Statistical modeling for selecting housekeeper
genes. *Genome Biology* 5:R59 (2004). [doi:10.1186/gb-2004-5-8-r59](https://doi.org/10.1186/gb-2004-5-8-r59).

The paper fitted its models with R's nlme but released no code. This package rebuilds them from
the paper's text and checks them against its tables.

| Task | Functions |
| --- | --- |
| One tissue type (Model 1a: log y = sample + gene + error, one error variance per gene) | `fit_model1()`, `gene_sd()`, `gene_sd_ci()`, `set_sd()`, `best_sets()`, `variance_group_test()` |
| Several tissue types (Model 2: tissue-specific gene bias, error SD = gene factor x tissue factor) | `fit_model2()`, `model2_components()`, `gene_mse()`, `set_mse()`, `minimax_sets()` |
| geNorm (Vandesompele et al. 2002), for comparison | `m_values()`, `genorm()`, `genorm_mean_rank()` |
| Data | `read_expression()`, `example_path()`, `as_long()` |

## Install

```r
install.packages("remotes")
remotes::install_github("jeonglab-bcm/fossil/PMC507884/package")
```

It needs R 4.3 or later and the CRAN packages nlme and numDeriv.

## Quick start

```r
library(hkselect)
breast <- read_expression(example_path("szabo2004_breast.csv"))
gene_sd_ci(breast$expr)                          # Table 1: SD of each gene's log expression
best_sets(gene_sd(fit_model1(breast$expr)))      # Table 2: best gene set of each size

# Several tissue types: a matrix of expression (samples x genes) and a tissue factor
comp <- model2_components(fit_model2(expr, tissue))
gene_mse(comp)                                   # bias, variance and MSE per gene and tissue (Fig. 3)
minimax_sets(comp)                               # best universal set of each size (Table 4)
```

The tutorial, `tutorial/TUTORIAL.md` (the vignette `tutorial.Rmd`, rendered), runs both models on
the example data and compares them with the expected output.

## Language

R, because the paper's method is built on R: it was fitted with `gls` from nlme, whose REML fits,
variance functions (`varIdent`, `varComb`) and BIC the package uses directly. A Python port would
have to reimplement them, and its users would lose the comparison with the paper's own software.

## What the paper does not say, and what this package does

- **Set variance.** The paper prints Var(log geometric mean of S) = sum sigma_j^2 / |S|. Its Table 2
  is computed with |S|^2, the variance of a mean. `set_sd()` uses |S|^2; `divisor = "size"` gives
  the printed formula.
- **Set MSE.** The paper describes the mean squared error of a gene set in words only. Its Table 4
  and its ACTB plus TBP example (0.35) both come back when the bias of a set is the sum of its
  genes' biases and the variance is that of the log-average. `set_mse()` uses that rule by default;
  `bias = "mean"` gives the mean of the biases, the bias of a log-average, which does not give the
  paper's table.
- **Table 4 "maximum number of members".** `minimax_sets(nested = TRUE)` gives the best set with at
  most that many genes, which is how the table reads (rows 3-5 and 7-9 repeat).
- **Confidence intervals.** The paper does not say how it computed Table 1's intervals.
  `gene_sd_ci()` gives Wald intervals on the log scale from an accurate Hessian of the REML
  likelihood. They come within 0.002 of the printed bounds. nlme's own `intervals()` uses a
  coarser numerical Hessian; its bounds move in the third decimal with the order of the rows, and
  across those orders they cover every printed bound.
- **The test behind p = 0.0014.** Not named in the paper. `variance_group_test()` (Model 1a against
  one variance for the four microarray-selected genes and one for GAPD and ACTB, a likelihood ratio
  test on 4 degrees of freedom) gives p = 0.00139.

## How it was checked

There is no original code to check against: the authors never released theirs. The package was
checked against the paper. On the paper's breast cancer data it gives all six standard deviations of
Table 1 and every gene set of Table 2 as printed, and five of the six Table 2 values (the sixth
0.1514 against 0.1513). On Vandesompele et al.'s data (downloaded by the reproduction, not bundled)
it gives every gene set of Table 4 and the biases of Figure 3, while its Model 2 standard
deviations (Table 3) come out about 2.5% lower than printed. The full comparison is in the
reproduction: `PMC507884/README.md` and the results page,
<https://jeonglab-bcm.github.io/fossil/PMC507884/>.

## Licence

MIT. The method is implemented from the paper's text. The example data `szabo2004_breast.csv` are
the paper's Additional data file 1, redistributed under its open access notice; see
`inst/extdata/README.md`.

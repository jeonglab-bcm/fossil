# gseamod

Modular gene set enrichment analysis, after Ackermann M and Strimmer K. A general modular framework
for gene set enrichment analysis. *BMC Bioinformatics* 10:47 (2009).
[doi:10.1186/1471-2105-10-47](https://doi.org/10.1186/1471-2105-10-47).

The paper splits every gene set test into modules: a gene-level statistic, a transformation, a
gene set statistic and a significance assessment, with globaltest and Hotelling's T-squared as
global tracks. Its R code is lost. This package rebuilds each module from the paper's text, so any
combination can be run, and its simulation study can be rerun.

| Module | Choices (`gsea()` argument) |
| --- | --- |
| Gene-level statistic (`gene`) | `"modt"` (limma's moderated t), `"t"`, `"corr"` |
| Transformation (`transform`) | `"square"`, `"none"`, `"ranksq"` (rank of the squared value), `"abs"`, `"binary"`, `"lfdr"` (fdrtool) |
| Gene set statistic (`setstat`) | `"mean"`, `"median"`, `"maxmean"`, `"es"` (weighted GSEA score), `"wilcoxon"`, `"condfdr"` (Efron's conditional fdr), `"globaltest"`, `"hotelling"` (shrinkage correlation) |
| Significance (`method`) | `"permutation"` (sample labels, self-contained), `"resampling"` (gene sampling, competitive), `"restandardization"`, `"parametric"` |

## Install

```r
install.packages("remotes")
remotes::install_github("jeonglab-bcm/fossil/PMC2661051/package")
```

It needs R 4.3 or later and the Bioconductor package limma (installed by `remotes` from the
`biocViews` field), fdrtool and corpcor from CRAN, and, for the globaltest track only,
Bioconductor's globaltest.

## Quick start

```r
library(gseamod)
X <- as.matrix(read.csv(example_path("sim_expression.csv"), row.names = 1, check.names = FALSE))
y <- read.csv(example_path("sim_labels.csv"))$class
sets <- read_gmt(example_path("sim_sets.gmt"))
gsea(X, y, sets, gene = "modt", transform = "square", setstat = "mean", method = "permutation", B = 1000, seed = 1)
```

The paper recommends the mean of the squared moderated t statistics, with sample label permutation
(is anything in the set associated with the classes?) or gene sampling (is the set more associated
than random sets of genes?).

The tutorial, `tutorial/TUTORIAL.md` (the vignette `tutorial.Rmd`, rendered), runs the method on
the example data and compares 100 simulated data sets with Table 4 of the paper.

## Language

R, because the method is built on R and Bioconductor packages: limma's moderated t, fdrtool's
local false discovery rates, corpcor's shrinkage correlation and globaltest. The authors' code was
R too. A Python port would have to reimplement each of them.

## How it was checked

- The moderated t equals `limma::eBayes`, the globaltest statistic equals `globaltest::gt` up to a
  constant factor, the logistic regression inside `condfdr` (its slope, `condslope`) equals `glm`, and
  the enrichment score equals a direct running sum (`tests/testthat`).
- There is no original code to check against (the authors' R code is lost), so the package was
  checked against the paper: the simulation tables, the p53 and Hedenfalk analyses and the text's
  claims. The reproduction is in
  [PMC2661051](https://github.com/jeonglab-bcm/fossil/tree/main/PMC2661051), with its results
  page at <https://jeonglab-bcm.github.io/fossil/PMC2661051/>.
- Settings the paper does not give, chosen here: the binary transformation calls a gene at
  two-sided p <= 0.05; `lfdr` uses fdrtool with a normal null for t statistics and a correlation
  null for correlations; `condfdr` averages 1 - fdr_S over the set, with fdr_S from fdrtool and a
  logistic regression of set membership on the transformed statistic; the parametric null of the
  mean of squared statistics is chi-squared with m degrees of freedom; Hotelling's correlation is
  estimated from the data centred within each class.

## Licence

MIT. The example data are synthetic (`scripts/make_example_data.R`); the expected output is
copied from the paper (CC BY 2.0).

# pdscox

Pathway deregulation scores with a Cox-LASSO model for relapse prognosis: the method of

Huang S, Yee C, Ching T, Yu H, Garmire LX. A novel model to combine clinical and pathway-based
transcriptomic information for the prognosis prediction of breast cancer. *PLoS Comput Biol*
10(9):e1003851 (2014). [doi:10.1371/journal.pcbi.1003851](https://doi.org/10.1371/journal.pcbi.1003851)

The authors' code is lost. This package was rebuilt from the paper's text: pathway deregulation
scores from pathifier, a Cox model with an L1 penalty from penalized (the penalty chosen as the
median of repeated 10-fold likelihood cross-validations), the prognostic index and its
risk groups, the log-rank test and the ROC AUC, the clinical and combined models, the
leave-one-out evaluation and the NKI70 comparison. The fossil reproduction runs every figure and
table of the paper through it.

## Install

```r
remotes::install_github("jeonglab-bcm/fossil/PMC4168973/package")
```

It needs R 4.3 or later and the Bioconductor packages pathifier and limma; the `biocViews` field
lets `remotes` install them.

## Why R

The method is a chain of R packages (pathifier, penalized, survival, limma), and the paper's
users work in R. A Python port would need re-implementations of pathifier and penalized that do
not give the same numbers.

## Quick start

```r
library(pdscox)
expr <- as.matrix(read.csv(example_path("synthetic_expression.csv"), row.names = 1, check.names = FALSE))
surv <- read.csv(example_path("synthetic_survival.csv"))
sets <- read_gmt(example_path("synthetic_sets.gmt"))
pds <- pathway_scores(expr, sets, attempts = 20)          # pathways x samples
model <- cox_lasso(t(pds), surv$time, surv$event, runs = 20)
pi <- prognostic_index(model$coefficients, t(pds))
evaluate_model(pi, surv$time, surv$event, share_cutoff(pi, 0.25))[c("p", "auc")]
```

The tutorial, `tutorial/TUTORIAL.md` (rendered from `vignettes/tutorial.Rmd`), runs both examples
and compares them with the expected output: 9 of 9 p-values of the paper's training set as
printed, and the synthetic truth.

## Functions

| Function | Does |
| --- | --- |
| `read_series_matrix()`, `read_gpl_annot()`, `probes_to_genes()`, `read_gmt()` | Read GEO series matrices and annotation; collapse probes to genes (geometric mean of the probes' log2 values); read gene sets. |
| `pathway_scores()` | Pathway deregulation scores (pathifier, no normal samples). |
| `cv_lambdas()`, `cox_lasso()` | Repeated likelihood cross-validation and the Cox-LASSO fit. |
| `prognostic_index()`, `share_cutoff()`, `risk_groups()` | The index and the higher- and lower-risk groups. |
| `logrank_p()`, `roc_auc()`, `evaluate_model()`, `loo_evaluate()` | Log-rank test, ROC AUC, both at once, and leave-one-out. |
| `univariate_cox()`, `clinical_matrix()`, `standardize()` | Univariate Cox models; clinical features coded, filled and standardized. |
| `nki70_score()`, `two_clusters()`, `pathway_gene_weights()` | The NKI70 comparison, the heatmap clusters, the gene counts of Table 3. |

## Licence

MIT (`LICENSE`). The example data: see `inst/extdata/README.md`.

## Reproduction

Results page: <https://jeonglab-bcm.github.io/fossil/PMC4168973/>. Pipeline:
<https://github.com/jeonglab-bcm/fossil/tree/main/PMC4168973/figure-reproduction>.

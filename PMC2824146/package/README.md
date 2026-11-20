# misscox

Missing covariate data in Cox prognostic models: the simulation study of Marshall, Altman, Royston
and Holder (2010), rebuilt as an R package. It simulates cohorts like the German Breast Cancer Study
Group 2 data, imposes MCAR, MAR, MNAR or combined missingness on four covariates, handles the
missing data with complete case analysis, single imputation or seven multiple imputation methods
(NORM, MIX, MIX without truncation, MICE, MICE-PMM, MICE-PMM without transformation, aregImpute),
and pools the Cox model results with Rubin's rules.

## Install

```r
remotes::install_github("jeonglab-bcm/fossil/PMC2824146/package")
```

It needs R 4.3 or later and the CRAN packages survival, mice, Hmisc, norm and mix (TH.data for the
breast cancer data).

## Quick start

```r
library(misscox)
x <- read.csv(example_path("example_cohort_mar25.csv"))   # 1000 cases, 25% incomplete (MAR)
handle_missing(x, "MICE_PMM_notrans", m = 20, seed = 1)    # pooled Cox model
table3_odds_ratios()                                       # Table 3 of the paper
```

Tutorial: [`tutorial/TUTORIAL.md`](tutorial/TUTORIAL.md) (the vignette `tutorial`).

## Why R

The paper ran in R and its methods are R packages (norm, mix, mice, Hmisc, survival), so the
package is in R and calls them, as the reproduction's default rule asks when a method relies on R
packages. A port to Python would replace them with look-alikes that do not give the same numbers.

## Where the method comes from

The authors released no code. The package implements the simulation from the paper's text
(`source: reconstructed`), with the choices the text leaves open recorded in the reproduction's
`results.json` and README: the binary covariates cut at 0.5, back-transformed X3 and X4 floored at
0, missingness intercepts solved at the average value of each mechanism's term, a restricted
general location model for MIX, aregImpute with one burn-in iteration, and the current CRAN
versions of the imputation packages (mice 3.16, Hmisc 5.1, norm 1.0-11.1, mix 1.0-13) rather than
the 2002 to 2005 versions the paper used.

## Citation

Marshall A, Altman DG, Royston P, Holder RL. Comparison of techniques for handling missing covariate
data within prognostic modelling studies: a simulation study. *BMC Medical Research Methodology*
10:7 (2010). doi:10.1186/1471-2288-10-7

## Licence

MIT (`LICENSE.md`). The reproduction: <https://github.com/jeonglab-bcm/fossil/tree/main/PMC2824146>.

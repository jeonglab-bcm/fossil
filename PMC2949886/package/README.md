# filterfdr

Filtering, FDR bias and power in two-group testing: the methods of

> van Iterson M, Boer JM, Menezes RX. Filtering, FDR and power. *BMC Bioinformatics* 11:450 (2010).
> [doi:10.1186/1471-2105-11-450](https://doi.org/10.1186/1471-2105-11-450)

- **Filters**: signal (mean of all samples), fold change (|difference of group means|) and variance, cut at
  their empirical quantiles (`filter_statistics`, `filter_keep`).
- **Achieved FDR and power after filtering** under Benjamini-Hochberg, Benjamini-Yekutieli, adaptive BH
  (multtest's two-stage procedure) and Storey's q-value, with the t or the Wilcoxon rank-sum test
  (`filter_curve`, `fdr_reject`); filtering before or after the correction (`postfilter_compare`).
- **The test for filtering-induced FDR bias** (`fdr_bias_test`): permute each feature's samples, filter,
  test whether the p-values left in are still uniform, and test those p-values over the permutations.
- **The paper's simulation** (`simulate_two_group`, the bitriangular distribution `dbitri`, `pbitri`,
  `qbitri`, `rbitri`) and the **p-value densities of the t test after filtering**
  (`pvalue_density_filtered`, the paper's Fig. 1).

The authors' R scripts are lost (the paper's link answers 404 and the archive behind it was never captured);
this package implements the methods from the paper and its Additional File 1. The reproduction of the
paper's figures with it is in [`PMC2949886/`](https://github.com/jeonglab-bcm/fossil/tree/main/PMC2949886) of
the fossil repository.

## Install

```r
# install.packages("remotes")
remotes::install_github("jeonglab-bcm/fossil/PMC2949886/package")
```

R 4.1 or later, with the Bioconductor packages multtest and qvalue (the `biocViews` field lets remotes
install them).

**Why R.** The method rests on Bioconductor packages (multtest for the FDR procedures, qvalue, and limma in
the paper's leukemia analysis), and the authors worked in R; by the default rule the package is R.

## Use

```r
library(filterfdr)
d <- read_two_group(example_path("example_data.csv"))     # feature, null, X1..X10, Y1..Y10
filter_curve(d, fractions = c(0, 0.25, 0.5), methods = "BH")   # needs the truth (d$null)
fdr_bias_test(d$x, d$group, filter = "foldchange", fractions = c(0, 0.1, 0.5), nperm = 1000)
```

The [tutorial](tutorial/TUTORIAL.md) runs the method on the bundled example and checks it against an
expected output computed with base R alone, and the p-value densities against the values of the paper's
Fig. 1.

## How it was checked

- The example's rejections, achieved FDR and power equal those of an independent base-R computation
  (`t.test`, `quantile`, `p.adjust`): 12 of 12 rows.
- `pvalue_density_filtered` matches 95 of 95 values read from the authors' original Fig. 1 within 0.01.
- The simulation follows the first author's `SSPA::rbitri` and `SSPA::simdat` (same formulas, same order of
  random draws); this was checked by reading SSPA's code, not by running it.
- The reproduction rebuilds Figs 1 to 7 and Figures S2 to S9 with the package; see its results page.

## Limits

- The paper writes the noise as N(0, 0.01) without saying whether 0.01 is a variance or an SD; the
  default `noise_sd = 0.1` (the variance reading) is the one that reproduces the paper's Fig. 4.
- `filter_statistics` gives the variance of all samples, as the paper's text defines the variance filter.
  The paper's Fig. 1 needs the pooled within-group variance instead (under the null, the variance of all
  samples leaves the p-values uniform); `pvalue_density_filtered(filter = "variance")` uses the pooled
  variance, and `filter = "total_variance"` the variance of all samples.
- Under the alternative, the variance-filter density of the paper's Fig. 1 does not come back (it removes
  fewer small p-values than ours); the cause is open.

## Licence

MIT, see [LICENSE](LICENSE). The code is written from the paper; it contains no code of the authors. The
example data are described in [inst/extdata/README.md](inst/extdata/README.md).

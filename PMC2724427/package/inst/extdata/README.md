# Example data

| File | What it is |
| --- | --- |
| `means_example.csv` | Synthetic per-size mean coefficients: one row per sample size (100 to 1500 by 5, the grid of the paper) and coefficient (`x`, the continuous exposure; `z`, the discrete one). Columns `n`, `term`, `mean`. |
| `means_example_expected.csv` | The values the means were drawn from, with the tolerance to compare a fit at. Columns `term`, `param` (`intercept` or `inv_n`), `value`, `tolerance`. |

`scripts/make_example_data.R` writes both. Each mean is `beta + b1/n` plus normal noise with
standard deviation 0.006, seed 20090727. `beta` and `b1` are the estimates of Table 1 of Nemes et
al. (2009): 2.011 and 23.9 for `x`, -0.898 and -9.524 for `z`. The expected output is those
generating values, not a run of the package. The tolerance is four standard errors of an
ordinary least squares fit on 1/n, worked out in closed form from the noise and the sizes.

The data are synthetic and carry the package's licence (MIT). Table 1's values are cited from
the paper, which is © 2009 Nemes et al; licensee BioMed Central Ltd, under the Creative Commons
Attribution License 2.0.

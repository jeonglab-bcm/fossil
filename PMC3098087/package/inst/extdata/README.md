# Example data

| File | What it is |
| --- | --- |
| `train.csv` | Training set: 40 samples (8 in Class 1, 32 in Class 2) and 300 variables, column `class` first. |
| `test.csv` | Test set: 20 samples (10 per class), same columns. |
| `expected_selected.csv` | The 40 variables with the largest absolute two-sample t statistic (equal variances) on the sample-centred training set, from `stats::t.test(var.equal = TRUE)`. |
| `expected_predictions.csv` | The classes that `sma::stat.diag.da` predicts for the test samples with those variables: DLDA (`pool = 1`) and DQDA (`pool = 0`). |

The data are synthetic, drawn as in the alternative case of Blagus and Lusa (2010): independent
N(0, 1) variables, with mean 0.8 in Class 2 for the first 20 variables. `scripts/make_example_data.R`
writes all four files (seed 523), rounding the inputs to four decimals.

The expected output does not come from multds. The selected variables come from base R's `t.test`;
the predictions come from `stat.diag.da` of sma 0.5.15 (Dudoit and Fridlyand, GPL-2 or later),
the function the paper used for DLDA and DQDA. sma was removed from CRAN; the script reads the
function from the archived source (`https://cran.r-project.org/src/contrib/Archive/sma/sma_0.5.15.tar.gz`)
and does not copy it here. Compare exactly: the selected variables as a set, the predictions class
by class.

Licence: MIT, like the package. The data are made up.

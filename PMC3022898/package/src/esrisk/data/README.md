# Example data

| File | What it is |
| --- | --- |
| `two_samples.csv` | Counts of seven pairs of independent samples. Columns: `label`; `d1`, `n1` (cases and people in sample 1); `d2_exposed`, `n2_exposed`, `d2_unexposed`, `n2_unexposed` (cases and people among the exposed and the unexposed of sample 2). |
| `two_samples_expected.csv` | The expected estimates for each row: ESR_S and its log 95% CI, ESR_R and its log and binomial 95% CIs. |

**Where they come from.** Synthetic, made by `scripts/make_example_data.py` (in the package folder, not
installed). Six rows are one pair of samples each from six settings of the paper's simulation grid
(Reichmann et al. 2011, Table 1), drawn with Python's `random` module, seed 20110105; the label names
the scenario, the RR and N1/N2. The seventh row has no cases among the exposed of sample 2, to show the
zero-cell rule: the log intervals are (0, inf).

**The expected output is not written by esrisk.** The same script computes it with the standard
library only, straight from the paper's equations 2, 5, 6, 8, 9, 10, 11 and 12, as a second
implementation written apart from the package. Compare at a relative tolerance of 1e-9.

**Licence.** MIT, like the package. No data of the paper or of any study are included.

# Example data

| File | What it is |
| --- | --- |
| `trials.csv` | Example input: one meta-analysis of 8 trials of a continuous outcome. Columns `study`, `mean_exp`, `sd_exp`, `n_exp`, `mean_contr`, `sd_contr`, `n_contr`. |
| `trials_expected.csv` | Expected output for that input: the random-effects (DerSimonian-Laird) pooled MD, SMD and RoM. Columns `measure`, `k`, `estimate`, `ci_low`, `ci_high`, `p`, `log_estimate` (RoM only: the pooled ln RoM), `se` (on the analysis scale), `q`, `tau2`, `i2` (%). |

## Where it comes from

- Input: synthetic, written by `scripts/make_example_data.py` (seed 20080521) from the paper's own design: control
  arms with mean 100 and SD 40, experimental arms with mean 120 (a true RoM of 1.2), heterogeneity of 0.5 SD added
  to each arm's mean (SD 0.5/sqrt(2) x 40 per arm), trial sizes from 12 to 80 per arm; means and SDs rounded to 0.1.
- Expected output: from R's metafor 4.4.0, not from this package (`scripts/metafor_expected.R`): `escalc("MD")`
  and `escalc("ROM")` (no bias correction) pooled by `rma(method = "DL")`. metafor's own SMD uses another
  variance, so the paper's SMD formula (Appendix) is evaluated in R and pooled by metafor's `rma`.
  metafor's CIs use 1.959964 (`qnorm(0.975)`); call the package with `z=1.959963984540054` to compare them.
- Licence: synthetic data, released with the package under its licence (MIT).

Compare with a relative tolerance of 1e-9 (the two implementations agree to about 1e-14).

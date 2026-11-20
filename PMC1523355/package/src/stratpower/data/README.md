# Example data

| File | What it is |
| --- | --- |
| `trial.csv` | Example input: one simulated trial of the paper's base case, 8,800 people (4,400 per arm). Columns `arm` (0 control, 1 treated), `outcome` (5-year primary event, 0/1) and `rf1` to `rf6` (the six risk factors, 0/1). |
| `trial_expected.csv` | Expected output: the logistic regression of `outcome` on a subgroup variable, `arm` and their interaction, for `rf1` alone (conventional analysis) and for the RF count `rf1 + ... + rf6` (risk-stratified analysis). Columns `subgroup`, `term`, `coef`, `se`; the row `p_interaction` holds the Wald p-value of the interaction in `coef`. |

## Where it comes from

- Input: synthetic, written by `scripts/make_example_data.py` with seed 2006 from the model of Hayward et al. 2006:
  six independent RFs of prevalence 25%, each with odds ratio 2; a 5-year control event rate of 0.75% with
  no RF; on treatment, EER = CER x .5 + .003 x 5 (Fig. 1A of the paper).
- Expected output: fitted by statsmodels 0.14.4 (`sm.Logit`), an independent implementation, not by this
  package.
- Licence: synthetic data, released with the package under its licence (MIT).

Compare with a relative tolerance of 1e-6: both fits converge to the same maximum, and their standard errors
come from the same information matrix.

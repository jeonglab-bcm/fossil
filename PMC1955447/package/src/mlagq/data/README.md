# Example data

| File | What it is |
| --- | --- |
| `clustered_binary.csv` | Example input: one data set of the paper's design, 40 groups of 25 people (1,000 rows). Columns `group`, `z` (a group-level covariate), `x` (an individual-level covariate) and `y` (the 0/1 outcome). |
| `clustered_binary_expected.csv` | Expected output for that input: the maximum likelihood estimates and standard errors of the paper's model, logit P(y = 1) = γ00 + γ01 z + γ10 x + γ11 x z + u0 + u1 x, with a correlated random intercept and slope. Columns `parameter` (`1`, `z`, `x`, `x:z`, `var(1)`, `cov(1;x)`, `var(x)`), `estimate`, `se`. |

## Where it comes from

- Input: synthetic, written by `scripts/make_example_data.py` with plain NumPy (seed 20070716), from the paper's
  Methods: z and x standard normal, random-intercept variance 0.67 (ICC 0.17), random-slope variance 1, independent,
  γ = (-1.0, 0.3, 0.3, 0.3); x and z rounded to 6 decimals.
- Expected output: computed without this package (`scripts/expected_output.py`): the likelihood integrated over the
  random effects on a dense grid (241 x 241 points over ±7 SD) and maximized with SciPy's BFGS; standard errors
  from a finite-difference Hessian of that likelihood.
- Licence: synthetic data, released with the package under its licence (MIT).

Compare with an absolute tolerance of 1e-3. mlagq maximizes the adaptive Gauss-Hermite approximation with the
number of points NLMIXED's rule picks (7 per dimension here), the expected output the grid integral; the two
agree to about 3e-4 in every estimate and standard error.

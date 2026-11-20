# Example data

| File | What it is |
| --- | --- |
| `cohort.csv` | 500 simulated subjects (columns `id`, `y`, `x`, `z`): one data set of the study's scenario RR 2.0, outcome 10%, quadratic confounder, strong association (Additional file 1 of Chen et al. 2014), drawn with seed 4079617, then contaminated at 5%: `y` is reversed for the subjects whose true outcome probability is beyond the population's 2.5% and 97.5% quantiles. |
| `cohort_expected.csv` | The relative risks of `x`, `z` and `z^2` fitted to `cohort.csv` by robust Poisson and log-binomial (COPY) regression, computed without this package's fitting code. |

Both are written by `scripts/make_example_data.py`. The data are synthetic, so there is no licence beyond the
package's (MIT).

Where the expected output comes from:

- Robust Poisson: statsmodels' Poisson GLM, coefficients and HC0 (sandwich) standard errors.
- Log-binomial: the likelihood maximized by scipy (Nelder-Mead, then Powell), not by this package. For this cohort
  the plain maximum lies on the boundary (a fitted probability reaches 1), so the expected fit is the COPY fit:
  the maximum of the likelihood with weight 1,000,000 on the data and weight 1 on the data with `y` reversed. Its
  SE is the inverse expected information, sum mu/(1 - mu) x x', at that maximum.

Compare at a relative tolerance of 1e-6 for `log_rr` and `se` (the two maximizers agree to about 3e-8). The true
log RR of `x` in the generating model is log 2 = 0.693; one contaminated cohort of 500 lands where it lands.

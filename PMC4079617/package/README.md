# robustrr

Relative risks for common binary outcomes by robust Poisson regression and by log-binomial regression with the
COPY method, and the outlier simulation study of

> Chen W, Shi J, Qian L, Azen SP. Comparison of robustness to outliers between robust poisson models and
> log-binomial models when estimating relative risks for common binary outcomes: a simulation study.
> *BMC Medical Research Methodology* 14:82 (2014). [doi:10.1186/1471-2288-14-82](https://doi.org/10.1186/1471-2288-14-82)

The authors ran the study in SAS 9.2 with the COPY macro of Petersen and Deddens; neither the program nor the
macro was released. This package is implemented from the paper's text (it is not a port) and checked against the
paper's printed tables: <!--CHECKS-->863 of 864 printed cells of Tables 1-3 and A1-A3 within Monte Carlo error (the miss is a misprint of the paper), and its fits against statsmodels and an independent maximizer (60 contaminated data sets (8 COPY fits): robust Poisson coefficients equal statsmodels' to 1e-12 and the sandwich SE its HC0 SE to a relative 3e-12; log-binomial coefficients equal an independent maximizer's to 1e-06, with a likelihood at least as high (to 1e-13) and a score of at most 4e-06).<!--/CHECKS-->

## Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC4079617/package"
```

Python 3.10 or later; the only dependency is NumPy. Language: Python, by the default rule (the authors' code was
SAS, which only proprietary software runs, and the method needs no R or Bioconductor package).

## Quick start

```python
import robustrr as rr

data = rr.read_table(rr.example_path("cohort.csv"))          # columns id, y, x, z
for row in rr.fit_relative_risk(data, "y", ["x", "z", "z^2"]):
    print(row["model"], row["term"], round(row["rr"], 3), row.get("method", ""))
```

```bash
robustrr fit "$(robustrr --example-path)" --outcome y --covariates x z z^2
robustrr simulate --rr 2.0 --outcome-rate 10 --form nonlinear --level strong --reps 200
```

## What it does

- `robust_poisson(X, y)`: the Poisson log-linear fit with the sandwich (HC0) covariance, which is what SAS PROC
  GENMOD's REPEATED statement gives with one record per subject (Zou 2004).
- `log_binomial(X, y)`: the binomial fit with a log link, by Newton's method inside the parameter space. When the
  maximum lies on the boundary (a fitted probability reaches 1) the plain fit does not converge, and the COPY fit is
  returned: weight C = 1,000,000 on the data and 1 on the data with the outcome reversed (Petersen and Deddens'
  revised macro). `method` says which.
- `poisson_coef`, `log_binomial_coef`: the same fits, batched over many data sets at once.
- `scenario`, `generate`, `population_cutoffs`, `contaminate`, `run_scenario`, `summarize`: the paper's 24
  scenarios (Additional file 1), the contamination at 2% and 5%, and the relative bias, SE and MSE over replicates.

Contamination: the paper flips the outcome of "records with p_y at bottom or top 1%" (2.5% for 5%). The default,
`cutoffs="population"`, flips the records beyond the population quantiles of p_y, so the number flipped varies
between data sets; `cutoffs="sample"` flips a fixed number per data set. The reproduction found the first reading
(see its README): it gives the paper's SEs, the second makes them too small at outcome 10% and 5% contamination.

## Tutorial

[tutorial/TUTORIAL.md](tutorial/TUTORIAL.md): install, the example cohort, both fits through the API and the
command line, the comparison with the expected output, and one scenario of the simulation.

## Reproduction

The whole study, every printed cell and Fig. 1: [PMC4079617](https://github.com/jeonglab-bcm/fossil/tree/main/PMC4079617),
results page <https://jeonglab-bcm.github.io/fossil/PMC4079617/>.

## Licence

MIT (implemented from the paper's text). The paper is CC BY 4.0.

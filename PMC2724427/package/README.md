# logitbias

Small-sample bias of logistic regression coefficients, estimated by simulation as in

Nemes S, Jonasson JM, Genell A, Steineck G. Bias in odds ratios by logistic regression modelling
and sample size. *BMC Medical Research Methodology* 9:56 (2009).
[doi:10.1186/1471-2288-9-56](https://doi.org/10.1186/1471-2288-9-56)

The authors released no code. Their Additional file 1 gives the R lines that draw the population;
`simulate_population()` runs those lines unchanged (checked to give the identical population on
the same seed). The rest is written from the paper's text: repeated samples of each size,
a logistic regression on each, and an ordinary least squares fit of the mean coefficient on
`1/n` (the paper's Equation 2). The package adds the analytic first-order bias of the estimator
(Cordeiro and McCullagh 1991; Firth 1993) as an independent check, and the bias-corrected
estimate.

## Install

```r
remotes::install_github("jeonglab-bcm/fossil/PMC2724427/package")
```

## Quick start

```r
library(logitbias)
pop <- simulate_population(100000, seed = 1)          # the paper's population
sim <- bias_simulation(pop, sizes = seq(100, 1500, 5), reps = 1000, seed = 1, cores = 4)
fit_bias_curve(sim$summary)                           # Table 1: beta and b1 for x and z
analytic_bias(pop)                                    # b1 without sampling
```

The [tutorial](tutorial/TUTORIAL.md) shows each step on the bundled example data.

## Why R

The package is in R because the paper's own code (the population lines of Additional file 1) is
R, and the method is R's `glm` fit. The default rule of the reproduction is R in that case.

## How it was checked

- `simulate_population()` against the R lines of Additional file 1 on the same seed: identical
  (the `port` item of the reproduction, and a test here).
- The full study against the paper's Table 1, Figs 1 to 3 and the claims in its text: see the
  [reproduction](https://jeonglab-bcm.github.io/fossil/PMC2724427/). The authors' simulation code
  was never published, so the rest of the package is checked against the paper, not against
  their code.
- `fit_bias_curve()` against `lm()`, on the means and on every estimate; `analytic_bias()`
  against the closed form for an intercept-only model.

## Samples without an estimate

At small sizes some samples are separated: a fitted probability reaches 0 or 1 and the maximum
likelihood estimate does not exist. The paper does not say how it handled them. By default
`bias_simulation()` leaves out every fit with a fitted probability within `1e-8` of 0 or 1, or
that did not converge, and counts them (`drop = "warning"` and `drop = "none"` give the other
choices).

## Licence

MIT. See [LICENSE.md](LICENSE.md). The example data are described in
[inst/extdata/README.md](inst/extdata/README.md).

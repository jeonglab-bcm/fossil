# mlagq

Multilevel logistic regression fitted by full maximum likelihood with adaptive Gauss-Hermite quadrature, the way
SAS PROC NLMIXED fits it, and the simulation study of sample size that used it, from

> Moineddin R, Matheson FI, Glazier RH. A simulation study of sample size for multilevel logistic regression
> models. *BMC Medical Research Methodology* 7:34 (2007). [doi:10.1186/1471-2288-7-34](https://doi.org/10.1186/1471-2288-7-34)

The model (the paper's equation 2), with one or two random effects per group:

logit P(y_ij = 1) = γ00 + γ01 z_j + γ10 x_ij + γ11 x_ij z_j + u0j + u1j x_ij, (u0j, u1j) ~ N(0, D).

| Step | As the paper describes PROC NLMIXED |
| --- | --- |
| Likelihood | Full maximum likelihood; the random effects integrated out by adaptive Gauss-Hermite quadrature, centred and scaled at each group's posterior mode. |
| Quadrature points | Chosen at the starting values: 1, 3, 5, 7, 9, 11, 21, 31 points per dimension until two successive log-likelihoods differ by less than 1e-4 (relative), NLMIXED's rule. |
| Optimizer | Quasi-Newton (BFGS), started at the given values, at most 200 iterations; converged when the largest gradient is below 1e-5 or the relative gradient below 1e-8 (NLMIXED's defaults), or, with `absxconv`, when no parameter moves by more than that in an iteration (the paper set 1e-8). |
| Variance parameters | The variances and the covariance themselves, unconstrained, as in `random u0 u1 ~ normal([0,0],[s0,c01,s1])`. A trial point whose D is not positive definite has no likelihood; the line search steps back. |
| Standard errors | From the inverse of the observed information (a finite-difference Hessian of the log-likelihood). |

## Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC1955447/package"
```

Python 3.10 or later; depends on NumPy.

## Quick start

```python
import mlagq

table = mlagq.read_long_csv(mlagq.example_path())          # columns group, z, x, y
fit = mlagq.fit_table(table, outcome="y", group="group", fixed=["1", "z", "x", "x:z"], random=["1", "x"],
                      cov=True, start=[-1, 0.3, 0.3, 0.3, 0.67, 0, 1])
print(fit.converged, dict(zip(fit.names, fit.estimate)), fit.se)

# One cell of the simulation study: 30 groups of 30, random-intercept variance 0.67 (ICC 0.17)
from mlagq import simulation as sim
cell = {"id": "J30_n30", "index": 0, "groups": 30, "size": 30, "gamma": sim.GAMMA_MAIN,
        "var0": 0.67, "var1": 1.0, "dists": None}
records = [sim.run_replicate("main", cell, r, base_seed=1)[0] for r in range(100)]
sim.summarize(records, sim.GAMMA_MAIN, 0.67, 1.0, scale="variance")   # % converged, % bias, non-coverage
```

Command line:

```bash
mlagq "$(mlagq --example-path)" --outcome y --group group --fixed 1 z x x:z --random 1 x --cov -o fit.csv
mlagq --simulate --groups 30 --size 30 --var0 0.67 --reps 100 --seed 1
```

Tutorial: [tutorial/TUTORIAL.md](tutorial/TUTORIAL.md).

## Why Python

The authors ran SAS 9.1 (PROC NLMIXED), which is proprietary, and released no code. The method relies on no R or
Bioconductor package, so by the reproduction's default rule the package is in Python. It is implemented from the
paper's text, not ported: there is no code to port, and SAS cannot be run here, so it was checked against the
paper's tables and against direct numerical integration of the likelihood, not against NLMIXED.

## Choices the paper does not state

Each was tested against the paper's tables in the reproduction
([PMC1955447](https://github.com/jeonglab-bcm/fossil/tree/main/PMC1955447)). The simulation defaults are the ones
that give the paper's tables back best:

- The fitted model estimates the covariance of the random intercept and slope (`cov=True`), although the data are
  drawn with none. Without it, far fewer data sets of 30 groups of 5 fail to converge than the paper reports.
- σ0 and σ1 are reported on the variance scale, the parameters as fitted: their % bias is that of the variance
  estimates, and their Wald intervals are on the variance. On the SD scale the biases at group size 5 are a
  third to a fifth of the printed ones.
- A fit that stops because no parameter moved by more than 1e-8 counts as converged (`absxconv=1e-8`), as the
  paper's "absolute parameter convergence criterion" says. Fits that creep towards a zero variance stop this way.

## Checks

<!--CHECKS--><!--/CHECKS-->

## Licence

MIT (the repository's licence): the method is implemented from the paper's text. The example data are synthetic
(`scripts/make_example_data.py`) and released under the same licence. The paper is © 2007 Moineddin et al., licensee
BioMed Central, under [CC BY 2.0](https://creativecommons.org/licenses/by/2.0/).

# rommeta

The ratio of means (RoM) for meta-analysis of continuous outcomes, next to the mean difference (MD) and the
standardized mean difference (SMD), with DerSimonian-Laird random-effects pooling, and the simulation study
that compares the three, from

> Friedrich JO, Adhikari NKJ, Beyene J. The ratio of means method as an alternative to mean differences for
> analyzing continuous outcome variables in meta-analysis: a simulation study. *BMC Medical Research
> Methodology* 8:32 (2008). [doi:10.1186/1471-2288-8-32](https://doi.org/10.1186/1471-2288-8-32)

| Measure | Per study (paper's Methods and Appendix) |
| --- | --- |
| MD | mean_e - mean_c; Var = sd_e²/n_e + sd_c²/n_c |
| SMD | (mean_e - mean_c)/sd_pool x [1 - 3/(4N - 9)]; Var = N/(n_e n_c) + SMD²/(2(N - 3.94)) |
| RoM | ln(mean_e/mean_c); Var = sd_e²/(n_e mean_e²) + sd_c²/(n_c mean_c²) (first-order delta method); pooled on the log scale and back-transformed |

Pooling: inverse-variance weights, the DerSimonian-Laird tau², 95% CI as estimate ± 1.96 SE, I² = (Q - (k - 1))/Q.
RoM needs both means positive; a study without is left out of its meta-analysis.

## Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC2430201/package"
```

Python 3.10 or later; depends on NumPy.

## Quick start

```python
import rommeta

# A study table: one row per trial, columns mean_exp, sd_exp, n_exp, mean_contr, sd_contr, n_contr.
studies = rommeta.read_studies(rommeta.example_path())
for r in rommeta.analyze(studies):           # MD, SMD and RoM
    print(r.measure, r.estimate, (r.ci_low, r.ci_high), r.i2)

# Or straight from sequences:
rommeta.meta_analysis([120, 135], [40, 38], [20, 25], [100, 104], [41, 39], [21, 24], measure="RoM")

# One scenario of the simulation study (10,000 meta-analyses):
sc = rommeta.Scenario(sd=70, effect=0.8, n_exp=10, n_contr=10, k=30)
rommeta.run_scenario(sc, 10_000, seed=1)["RoM"]["bias"]   # about -3%, as Table 5 prints
```

Command line:

```bash
rommeta meta "$(rommeta --example-path)" -o pooled.csv
rommeta simulate --sd 70 --effect 0.8 --n-exp 10 --n-contr 10 --k 30 --seed 1
```

Tutorial: [tutorial/TUTORIAL.md](tutorial/TUTORIAL.md).

## Choices the paper does not state

Each was tested against the paper's Tables 3-8 in the reproduction
([PMC2430201](https://github.com/jeonglab-bcm/fossil/tree/main/PMC2430201)); the defaults are the ones that
give the paper's tables back.

- **% bias of RoM** is taken on the ratio scale, (mean pooled RoM - true RoM)/true RoM, like MD and SMD
  (`summarize(...)["RoM"]["bias"]`; `bias_ln` and `bias_rm1` give the other readings, which miss the tables).
- **I² over replicates** is 100 x (1 - 1/mean(Q/(k - 1))) (`i2`); `i2_mean` and `i2_median` summarize each
  replicate's I² instead and miss the tables.
- **Heterogeneity** is added as independent normal shifts of SD tau/sqrt(2) to each arm's mean
  (`heterogeneity="independent"`).
- **Skewed data** are the mixture times the control mean, shifted by effect x SD in the experimental arm
  (`skew_shift="additive"`; `"standardized"` rescales the mixture to SD 40 first and fits as well).
- **Normal arms** are drawn from their sufficient statistics (`draw="summary"`), the same in distribution as
  drawing every patient (`draw="values"`).

## Language and checks

Python: the authors' programs were SAS 8.2 and were never released, and the method needs no R package.
<!--CHECKS-->The package is implemented from the paper's text and checked against the paper's printed tables (2,266 of 2,268 cells of Tables 3-8 within Monte Carlo error) and its pooling against R's metafor 4.4.0 (the example data, and 900 simulated meta-analyses to a relative 5e-14).<!--/CHECKS-->
It was not checked against the authors' code, which is lost.

## Licence

MIT (the fossil repository's licence). Cite the paper above when you use the method.

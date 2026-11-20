# stratpower

Power of a multivariable risk-stratified subgroup analysis against a conventional one-variable-at-a-time
analysis of a clinical trial, and the interaction test behind both. The method is from

> Hayward RA, Kent DM, Vijan S, Hofer TP. Multivariable risk prediction can greatly enhance the statistical
> power of clinical trial subgroup analysis. *BMC Medical Research Methodology* 6:18 (2006).
> [doi:10.1186/1471-2288-6-18](https://doi.org/10.1186/1471-2288-6-18)

The authors' simulation code was never released and is lost. This package was written from the paper's text
and checked against its printed tables and figure in the
[PMC1523355 reproduction](https://github.com/jeonglab-bcm/fossil/tree/main/PMC1523355), not against the
original code. Python, because the method needs only a logistic regression and the authors' code (Stata, by a
referee's reading) cannot be run.

## Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC1523355/package"
```

## Quick start

```python
import stratpower as sp

# One trial: does the risk score modify the treatment effect?
d = sp.read_trial(sp.example_path())            # arm, outcome, rf1..rf6
score = sp.risk_score(d, {f"rf{i}": 1 for i in range(1, 7)})
print(sp.interaction_test(score, d["arm"], d["outcome"])["p_interaction"])

# Power by simulation, the paper's base case (Table 1)
pop = sp.population(n_rf=6, prevalence=0.25, effect=2.0, cer0=0.0075, scale="or")
k = pop.count()
print(sp.simulate_power(pop, {"one RF": pop.patterns[:, 0], "RF count": k}, iterations=2000, seed=1))
```

Command line:

```bash
stratpower test trial.csv --weights rf1=1,rf2=1,rf3=1 -o test.csv
stratpower power --n-rf 6 --effect 2 --prevalence 0.25 --iterations 2000
```

## What it computes

- `population(...)`: every pattern of K independent binary risk factors, its share and its 5-year control
  event rate (CER), on the odds or the relative-risk scale.
- `treated_risk`, `net_rrr`: EER = CER x .5 + .003 x 5 and the net relative risk reduction (Fig. 1A).
- `interaction_test(z, arm, outcome)`: logistic regression of the outcome on z, arm and z x arm, with the
  Wald p-value of the interaction (Brookes et al.).
- `simulate_power(pop, subgroups, ...)`: the share of simulated trials (4,400 per arm, drawn with replacement)
  whose interaction p-value is below .05, for each subgroup variable; the main effect too.
- `population_auroc`: the AUROC of a risk index for the outcome.

Tutorial: [tutorial/TUTORIAL.md](tutorial/TUTORIAL.md).

## Licence

MIT (the fossil repository's licence). Example data are synthetic; see `src/stratpower/data/README.md`.

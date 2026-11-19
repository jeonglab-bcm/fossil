# oisim

The risk of overestimated pooled effects in a cumulative random-effects meta-analysis, and the optimal information size (OIS), as in:

Thorlund K, Imberger G, Walsh M, Chu R, Gluud C, Wetterslev J, Guyatt G, Devereaux PJ, Thabane L. The number of patients and events required to limit the risk of overestimation of intervention effects in meta-analysis—a simulation study. *PLoS ONE* 6(10):e25491 (2011). [doi:10.1371/journal.pone.0025491](https://doi.org/10.1371/journal.pone.0025491)

The authors released no code. This package is implemented from the paper's text and its Appendices S1 and S2, and checked against the paper's tables and figures in the [reproduction](https://github.com/jeonglab-bcm/fossil/tree/main/PMC3196500).

## Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC3196500/package"
```

Python 3.10 or later; the only dependency is NumPy.

**Language.** Python, by the default rule: the paper names no software and the method uses no R or Bioconductor package.

## Quick start

```python
import oisim

# OIS for a 20% relative risk reduction, control risk 10%, I2 25%, 90% power
oisim.ois(pc=0.10, rrr=0.20, i2=0.25, beta=0.10)           # {'patients': 11474.1..., 'events': 1032.6..., ...}

# Your own trials: cumulative DerSimonian-Laird random-effects meta-analysis after each trial
rows = oisim.cumulative(oisim.read_trials(oisim.example_path("cumulative_trials.csv")))

# One of the paper's scenarios, and the patients needed for P(RRR > 30%) to drop below 10%, 5%, 1%
sim = oisim.simulate(oisim.Scenario("cochrane", "5-15", tau2=0.15, rrr=0.0, n_meta=2000), seed=1)
oisim.required_table(sim)
```

Command line:

```bash
oisim cumulative trials.csv -o cumulative.csv
oisim ois --pc 0.10 --rrr 0.20 --i2 0.25 --beta 0.10
oisim simulate --sizes cochrane --pc 5-15 --tau2 0.15 --rrr 0 --n-meta 2000
```

## What it does

- `ois(pc, rrr, i2, alpha, beta)`: OIS = 4 (z<sub>1-α/2</sub> + z<sub>1-β</sub>)² P(1 − P) / δ² × 1/(1 − I²), with P the mean of the control and treatment risks and δ their difference; events = OIS × P. `round_ois` rounds as most of the paper's Table 2 cells are rounded (the footnote's rule does not give them).
- `simulate(Scenario(...))`: Appendix S2's trials (size interval drawn with the Table S2 or 'common' probabilities, then a uniform integer; n/2 per arm; PC uniform on the range; ln RR ~ N(ln(1 − RRR), τ²); binomial events) and Appendix S1's DerSimonian-Laird pooling after every trial.
- `overestimation_curve` and `required_number`: the proportion of pooled RRR above 20% or 30% per point of cumulative patients or events, and the first point at which it drops below 10%, 5% or 1%.

Settings the paper does not state are arguments; the defaults are those that fit the paper best in the reproduction (zero cells: 0.5 added to every cell of a trial with a zero cell, trials with no events in either arm left out; binning: `nearest` for the curves, `interval` reproduces the tables best). See the reproduction's README for how each was chosen.

## Tutorial

[tutorial/TUTORIAL.md](tutorial/TUTORIAL.md) (executed notebook: `tutorial/tutorial.ipynb`).

## Licence

MIT (see LICENSE). The method is implemented from the paper's text; no authors' code exists.

<!-- Generated from tutorial.ipynb by check_package.py --write. Do not edit by hand. -->

# rommeta tutorial

`rommeta` pools continuous outcomes across trials with the ratio of means (RoM), next to the mean difference (MD) and the standardized mean difference (SMD). The RoM of a trial is the experimental mean over the control mean; its logarithm has the first-order delta-method variance sd_e²/(n_e mean_e²) + sd_c²/(n_c mean_c²), and the log ratios are pooled with inverse-variance random effects (DerSimonian-Laird) and back-transformed. Like the SMD it is unitless, so trials that measured the outcome in different units can be pooled; unlike the SMD it reads as a relative change ("20% more urine output") without knowing the pooled SD.

Friedrich JO, Adhikari NKJ, Beyene J. The ratio of means method as an alternative to mean differences for analyzing continuous outcome variables in meta-analysis: a simulation study. *BMC Medical Research Methodology* 8:32 (2008). doi:10.1186/1471-2288-8-32

## 1. Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC2430201/package"
```

```python
import rommeta

print("rommeta", rommeta.__version__)
```

```text
rommeta 0.1.0
```

## 2. The example input

One meta-analysis of eight trials: the mean, SD and number of patients of the experimental and the control arm of each. The data are synthetic, drawn from the paper's own design (control mean 100, SD 40, a true RoM of 1.2, heterogeneity between trials) by `scripts/make_example_data.py`.

```python
studies = rommeta.read_studies(rommeta.example_path("trials.csv"))
cols = ["mean_exp", "sd_exp", "n_exp", "mean_contr", "sd_contr", "n_contr"]
print(f"{'study':10s}" + "".join(f"{c:>12s}" for c in cols))
for i, name in enumerate(studies["study"]):
    print(f"{name:10s}" + "".join(f"{studies[c][i]:>12g}" for c in cols))
```

```text
study         mean_exp      sd_exp       n_exp  mean_contr    sd_contr     n_contr
Trial 1          139.7        33.9          12        83.6          36          12
Trial 2          124.6        33.6          15        42.3        42.5          14
Trial 3            143        38.6          20       105.6        34.1          21
Trial 4          124.3        33.1          24       101.5        35.2          25
Trial 5           97.5        36.3          30       129.2        36.8          30
Trial 6            129        40.8          41        92.6        27.9          39
Trial 7            137        43.9          55          95        38.2          52
Trial 8          121.5        40.1          80        95.8        37.1          78
```

## 3. Run the method

`analyze` pools the table with each measure. For RoM, `estimate` and the CI are on the ratio scale and `log_estimate` is the pooled ln RoM; `i2` is in percent.

```python
results = rommeta.analyze(studies)
print(f"{'measure':8s}{'k':>3s}{'estimate':>10s}{'95% CI':>20s}{'p':>9s}{'tau2':>10s}{'I2 (%)':>8s}")
for r in results:
    print(f"{r.measure:8s}{r.k:>3d}{r.estimate:>10.3f}{f'{r.ci_low:.3f} to {r.ci_high:.3f}':>20s}{r.p:>9.4f}{r.tau2:>10.4f}{r.i2:>8.1f}")
```

```text
measure   k  estimate              95% CI        p      tau2  I2 (%)
MD        8    32.677    13.119 to 52.236   0.0011  690.4344    89.0
SMD       8     0.836      0.332 to 1.340   0.0012    0.4321    86.0
RoM       8     1.330      1.118 to 1.581   0.0013    0.0505    87.4
```

The pooled RoM says the experimental arms average about a third more than the control arms; the MD says the same in the outcome's own units, and the SMD in SD units.

## 4. Compare with the expected output

The expected output was computed by another implementation, R's metafor 4.4.0 (`escalc` and `rma(method = "DL")`, with the paper's SMD formula evaluated in R; `scripts/metafor_expected.R`), not by this package. metafor's CIs use 1.959964 rather than the paper's 1.96, so the comparison passes that value.

```python
import math

expected = rommeta.read_results(rommeta.example_path("trials_expected.csv"))
ours = rommeta.analyze(studies, z=1.959963984540054)
fields = ["k", "estimate", "ci_low", "ci_high", "p", "log_estimate", "se", "q", "tau2", "i2"]
checked = agree = 0
for o, e in zip(ours, expected):
    d = o.as_dict()
    for f in fields:
        if e[f] is None:
            continue
        checked += 1
        agree += math.isclose(d[f], e[f], rel_tol=1e-9, abs_tol=1e-12)
print(f"{agree} of {checked} values agree with metafor (relative tolerance 1e-9)")
assert agree == checked
```

```text
28 of 28 values agree with metafor (relative tolerance 1e-9)
```

## 5. From the command line

`rommeta meta` reads the same CSV and writes the pooled results as CSV (to standard output without `-o`).

```python
path = rommeta.example_path("trials.csv")
!rommeta meta "{path}" --measure RoM
```

```text
measure,k,estimate,ci_low,ci_high,p,log_estimate,se,q,tau2,i2
RoM,8,1.3296121884765588,1.1181290205383423,1.5810953291367518,0.001267096592881416,0.28488731210211915,0.08838292910287206,55.57729972613491,0.05051377157799058,87.4049296484473
```

## 6. One scenario of the simulation study

The paper compared the three measures on 10,000 simulated meta-analyses per scenario. `run_scenario` does one: here the scenario where RoM is most biased, SD 70% of the control mean, a large effect (0.8 SD), 10 patients per arm, 30 trials, no heterogeneity (Table 5). The paper prints % bias 0/-5/-3, % coverage 94/94/90 and % power 100/100/100 for MD/SMD/RoM.

```python
sc = rommeta.Scenario(sd=70, effect=0.8, n_exp=10, n_contr=10, k=30, tau=0.0)
perf = rommeta.run_scenario(sc, 10_000, seed=20080521)
print("true values:", {m: round(v, 2) for m, v in sc.true.items()})
for q in ("bias", "coverage", "power"):
    print(f"% {q:9s}" + "".join(f"{m:>5s} {perf[m][q]:6.1f} (MC SE {perf[m][q + '_se']:.2f})" for m in ("MD", "SMD", "RoM")))
```

```text
true values: {'MD': 56.0, 'SMD': 0.8, 'RoM': 1.56}
% bias        MD   -0.0 (MC SE 0.11)  SMD   -5.3 (MC SE 0.10)  RoM   -3.0 (MC SE 0.05)
% coverage    MD   94.5 (MC SE 0.23)  SMD   94.0 (MC SE 0.24)  RoM   89.5 (MC SE 0.31)
% power       MD  100.0 (MC SE 0.00)  SMD  100.0 (MC SE 0.00)  RoM  100.0 (MC SE 0.00)
```

Each run moves these numbers by a few Monte Carlo standard errors. RoM is biased towards no effect here because a trial with a high ratio usually has a low control mean, a larger variance of ln RoM and so a smaller weight; SMD is biased the same way for a different reason (its variance grows with the SMD itself).

## 7. Your own data

- **Input.** A CSV with one row per trial and the columns `mean_exp`, `sd_exp`, `n_exp`, `mean_contr`, `sd_contr`, `n_contr` (an optional `study` column names the rows). RoM needs both means positive: a trial with a non-positive mean is left out of the RoM meta-analysis (`k` says how many were pooled).
- **Options.** `measures` picks MD, SMD and/or RoM; `z` sets the CI multiplier (1.96 by default, as in the paper). MD needs every trial in the same units; SMD and RoM do not.
- **Output.** `estimate`, `ci_low`, `ci_high`: the pooled effect and its 95% CI (RoM on the ratio scale); `p`: two-sided p of the pooled effect; `log_estimate` and `se`: the pooled ln RoM and its SE (for MD and SMD, `se` is on their own scale); `q`, `tau2`, `i2`: Cochran's Q, the DerSimonian-Laird between-trial variance and I² (%).
- **Simulation.** `Scenario(sd, effect, n_exp, n_contr, k, tau, distribution)` and `run_scenario` reproduce any cell of the paper's Tables 3-8; `summarize` also returns the other readings of RoM bias and I² that the reproduction tested.

The reproduction, with every table cell against the paper: https://github.com/jeonglab-bcm/fossil/tree/main/PMC2430201 (results page: https://jeonglab-bcm.github.io/fossil/PMC2430201/).

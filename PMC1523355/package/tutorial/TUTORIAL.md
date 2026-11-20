<!-- Generated from tutorial.ipynb by check_package.py --write. Do not edit by hand. -->

# stratpower tutorial

`stratpower` tests whether a treatment's effect differs across subgroups of a trial, and estimates by simulation how much power that test has. A conventional subgroup analysis tests one risk factor at a time; a risk-stratified analysis tests a single risk score built from many. The paper showed that, when a treatment carries a small uniform harm, the risk score has far more power.

> Hayward RA, Kent DM, Vijan S, Hofer TP. Multivariable risk prediction can greatly enhance the statistical power of clinical trial subgroup analysis. *BMC Medical Research Methodology* 6:18 (2006). doi:10.1186/1471-2288-6-18

## 1. Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC1523355/package"
```

It needs Python 3.10 or later and NumPy. This notebook was run in a fresh environment with the package installed from its wheel:

```python
import stratpower as sp
print("stratpower", sp.__version__)
```

```text
stratpower 0.1.0
```

## 2. Example input

One simulated trial of the paper's base case: 8,800 people, 4,400 per arm, six independent risk factors (prevalence 25%, odds ratio 2 each), a 5-year event rate of 0.75% with no risk factor. Treatment halves the risk but adds 3 complications per 1,000 people per year.

```python
d = sp.read_trial(sp.example_path("trial.csv"))
print("columns:", list(d))
print("people:", len(d["arm"]), " treated:", int(d["arm"].sum()), " events:", int(d["outcome"].sum()))
for i in range(5):
    print({k: int(v[i]) for k, v in d.items()})
```

```text
columns: ['arm', 'outcome', 'rf1', 'rf2', 'rf3', 'rf4', 'rf5', 'rf6']
people: 8800  treated: 4400  events: 244
{'arm': 0, 'outcome': 0, 'rf1': 0, 'rf2': 0, 'rf3': 0, 'rf4': 0, 'rf5': 0, 'rf6': 0}
{'arm': 0, 'outcome': 0, 'rf1': 1, 'rf2': 0, 'rf3': 0, 'rf4': 0, 'rf5': 0, 'rf6': 1}
{'arm': 0, 'outcome': 0, 'rf1': 0, 'rf2': 0, 'rf3': 0, 'rf4': 1, 'rf5': 0, 'rf6': 0}
{'arm': 0, 'outcome': 0, 'rf1': 0, 'rf2': 1, 'rf3': 0, 'rf4': 0, 'rf5': 0, 'rf6': 0}
{'arm': 0, 'outcome': 0, 'rf1': 0, 'rf2': 0, 'rf3': 0, 'rf4': 0, 'rf5': 1, 'rf6': 0}
```

## 3. Run the method

The conventional analysis tests `rf1` alone; the risk-stratified analysis tests the count of risk factors. Both fit a logistic regression of the outcome on the subgroup variable, the arm and their interaction.

```python
conventional = sp.interaction_test(d["rf1"], d["arm"], d["outcome"])
score = sp.risk_score(d, {f"rf{i}": 1 for i in range(1, 7)})
stratified = sp.interaction_test(score, d["arm"], d["outcome"])
for name, r in (("rf1 alone", conventional), ("risk score", stratified)):
    print(f"{name:11s} interaction {r['coef']['z_x_arm']:+.4f} (SE {r['se']['z_x_arm']:.4f}), p = {r['p_interaction']:.2g}")
```

```text
rf1 alone   interaction -0.1729 (SE 0.2697), p = 0.52
risk score  interaction -0.4597 (SE 0.1126), p = 4.5e-05
```

## 4. Compare with the expected output

`trial_expected.csv` holds the same two regressions fitted by statsmodels, an independent implementation.

```python
import csv, math
with open(sp.example_path("trial_expected.csv"), newline="") as f:
    exp = {(r["subgroup"], r["term"]): r for r in csv.DictReader(f)}
ok = n = 0
for label, r in (("rf1", conventional), ("score", stratified)):
    for term in ("intercept", "z", "arm", "z_x_arm"):
        for kind in ("coef", "se"):
            n += 1
            ok += math.isclose(r[kind][term], float(exp[(label, term)][kind]), rel_tol=1e-6)
    n += 1
    ok += math.isclose(r["p_interaction"], float(exp[(label, "p_interaction")]["coef"]), rel_tol=1e-6)
print(f"{ok} of {n} values match the expected output")
assert ok == n
```

```text
18 of 18 values match the expected output
```

## 5. Power by simulation

Power is the share of simulated trials in which the interaction test reaches p < .05. Here 2,000 trials of the base case (the paper's Table 1 reports .23 for one risk factor, .72 for the dichotomized score and .83 for the score).

```python
pop = sp.population(n_rf=6, prevalence=0.25, effect=2.0, cer0=0.0075, scale="or")
k = pop.count()
power = sp.simulate_power(pop, {"one RF": pop.patterns[:, 0], "score 0-1 vs 2+": (k >= 2) * 1.0, "score": k},
                          iterations=2000, seed=1)
for name, v in power.items():
    print(f"{name:16s} {v['power']:.3f}")
```

```text
one RF           0.237
score 0-1 vs 2+  0.731
score            0.853
main_effect      0.064
```

Net relative risk reduction against pre-treatment risk (the paper's Fig. 1A): treatment harms people whose 5-year risk is below 3%.

```python
for cer in (0.01, 0.02, 0.03, 0.05, 0.075):
    print(f"CER {cer:.3f}: net RRR {float(sp.net_rrr(cer)):+.3f}")
```

```text
CER 0.010: net RRR -1.000
CER 0.020: net RRR -0.250
CER 0.030: net RRR +0.000
CER 0.050: net RRR +0.200
CER 0.075: net RRR +0.300
```

## 6. Command line

The same test from the shell:

```python
path = sp.example_path("trial.csv")
!stratpower test "{path}" --weights rf1=1,rf2=1,rf3=1,rf4=1,rf5=1,rf6=1
```

```text
subgroup,term,coef,se
score,intercept,-5.069334390764444,0.21282945957214064
score,z,0.7591793272824244,0.07938948791590085
score,arm,1.0496975123721517,0.2744567663808805
score,z_x_arm,-0.4596543394774172,0.11259802047444639
score,p_interaction,4.459995505694415e-05,
```

## 7. Your own data

- Input: a CSV with `arm` (0 control, 1 treated), `outcome` (0/1) and any numeric covariates.
- `--subgroup COLUMN` tests one 0/1 covariate; `--weights COL=W,...` tests a risk score, the weighted sum of covariates (use the weights of an externally developed prediction tool).
- Output: the coefficients and standard errors of the intercept, the subgroup variable (`z`), `arm` and the interaction (`z_x_arm`), and the Wald p-value of the interaction.
- For power, describe the population with `sp.population` (or `sp.Population` for unequal prevalences and effects) and pass each subgroup variable to `sp.simulate_power`; `harm_per_year`, `n_per_arm`, `test="lr"` and `scale="rr"` change the design.

## 8. The reproduction

Every table and figure of the paper rerun with this package: <https://github.com/jeonglab-bcm/fossil/tree/main/PMC1523355> (results page: <https://jeonglab-bcm.github.io/fossil/PMC1523355/>).

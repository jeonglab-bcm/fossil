<!-- Generated from tutorial.ipynb by check_package.py --write. Do not edit by hand. -->

# mlagq tutorial

`mlagq` fits multilevel logistic regression by full maximum likelihood, integrating the random effects with adaptive Gauss-Hermite quadrature, as SAS PROC NLMIXED does. It also runs the simulation study of the paper it was rebuilt from, which asked how many groups, and how many people per group, such a model needs for unbiased estimates and honest confidence intervals.

> Moineddin R, Matheson FI, Glazier RH. A simulation study of sample size for multilevel logistic regression models. *BMC Medical Research Methodology* 7:34 (2007). [doi:10.1186/1471-2288-7-34](https://doi.org/10.1186/1471-2288-7-34)

The authors used SAS PROC NLMIXED and released no code. This package is implemented from the paper's text.

## 1. Install

Install the package from its folder in the repository:

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC1955447/package"
```

Or with uv:

```bash
uv pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC1955447/package"
```

It needs Python 3.10 or later and NumPy.

```python
import mlagq

print("mlagq", mlagq.__version__)
```

```text
mlagq 0.1.0
```

## 2. The example input

The package ships one data set of the paper's design: 40 groups of 25 people, a group-level covariate `z`, an individual-level covariate `x` and a 0/1 outcome `y`. It was drawn with a random-intercept variance of 0.67 (ICC 0.17), a random-slope variance of 1 and γ = (-1.0, 0.3, 0.3, 0.3). `mlagq.example_path()` returns its location.

```python
path = mlagq.example_path()
table = mlagq.read_long_csv(path)
n = len(table["y"])
print(n, "rows,", len(set(table["group"])), "groups; columns:", ", ".join(table))
print("prevalence of y:", sum(int(v) for v in table["y"]) / n)
for i in range(4):
    print({k: table[k][i] for k in table})
```

```text
1000 rows, 40 groups; columns: group, z, x, y
prevalence of y: 0.302
{'group': 'g01', 'z': '0.857641', 'x': '1.550793', 'y': '1'}
{'group': 'g01', 'z': '0.857641', 'x': '-0.151215', 'y': '0'}
{'group': 'g01', 'z': '0.857641', 'x': '0.793853', 'y': '0'}
{'group': 'g01', 'z': '0.857641', 'x': '-0.830712', 'y': '0'}
```

## 3. Run the method

The paper's model (its equation 2) has four fixed effects, the intercept, `z`, `x` and their product `x:z`, and a random intercept and a random slope on `x` for each group. `fit_table` names the columns. `cov=True` also estimates the covariance of the two random effects. The variance parameters are fitted as variances, as in an NLMIXED `random` statement. The fit starts from the given values, which the paper set to the true ones. The number of quadrature points is chosen at those values, as NLMIXED does.

```python
start = [-1.0, 0.3, 0.3, 0.3, 0.67, 0.0, 1.0]
fit = mlagq.fit_table(table, outcome="y", group="group", fixed=["1", "z", "x", "x:z"], random=["1", "x"],
                      cov=True, start=start)
print(f"status {fit.status}, converged {fit.converged}, {fit.iterations} iterations, "
      f"{fit.qpoints} points per dimension, log-likelihood {fit.loglik:.4f}")
print(f"{'parameter':<10}{'estimate':>10}{'se':>10}")
for name, est, se in zip(fit.names, fit.estimate, fit.se):
    print(f"{name:<10}{est:>10.4f}{se:>10.4f}")
```

```text
status gconv, converged True, 7 iterations, 7 points per dimension, log-likelihood -535.2605
parameter   estimate        se
1            -1.1303    0.1694
z             0.3390    0.1791
x             0.2807    0.1810
x:z           0.4759    0.2028
var(1)        0.7910    0.2578
cov(1;x)      0.2978    0.2163
var(x)        0.9194    0.3329
```

## 4. Compare with the expected output

The expected output ships with the package. It was computed without `mlagq`: the likelihood was integrated over the random effects on a dense grid and maximized with SciPy (`scripts/expected_output.py`). The two methods integrate differently, so they agree to about 3e-4. They are compared at 1e-3.

```python
import csv

with open(mlagq.example_path("clustered_binary_expected.csv")) as f:
    expected = {r["parameter"]: (float(r["estimate"]), float(r["se"])) for r in csv.DictReader(f)}
matches = 0
for name, est, se in zip(fit.names, fit.estimate, fit.se):
    e, s = expected[name]
    ok = abs(est - e) < 1e-3 and abs(se - s) < 1e-3
    matches += ok
    print(f"{name:<10} ours {est:8.4f} ({se:.4f})  expected {e:8.4f} ({s:.4f})  {'match' if ok else 'DIFFERENT'}")
print(f"{matches} of {len(expected)} parameters match the expected output")
assert matches == len(expected)
```

```text
1          ours  -1.1303 (0.1694)  expected  -1.1303 (0.1695)  match
z          ours   0.3390 (0.1791)  expected   0.3391 (0.1791)  match
x          ours   0.2807 (0.1810)  expected   0.2806 (0.1809)  match
x:z        ours   0.4759 (0.2028)  expected   0.4761 (0.2027)  match
var(1)     ours   0.7910 (0.2578)  expected   0.7913 (0.2581)  match
cov(1;x)   ours   0.2978 (0.2163)  expected   0.2979 (0.2164)  match
var(x)     ours   0.9194 (0.3329)  expected   0.9197 (0.3333)  match
7 of 7 parameters match the expected output
```

## 5. One cell of the simulation study

`mlagq.simulation` holds the paper's design. Each replicate draws a data set from its own random stream, fits it from the true values and keeps the fit only if it converged. The summary gives the % converged, the % relative bias (variance scale for the random effects, as fitted) and the non-coverage of the 95% Wald interval. The cell below is 50 groups of 30 at ICC 0.17 with 40 replicates. The paper ran 1,000 per cell; its Table 1 prints 100% converged and biases of -0.32, 0.28, 2.06, 3.69, -2.90 and -2.55% for this cell. Forty replicates show the method, not those numbers: their Monte Carlo error is several percent.

```python
from mlagq import simulation as sim

cell = {"id": "J50_n30_icc0.17", "index": 0, "groups": 50, "size": 30, "gamma": sim.GAMMA_MAIN,
        "var0": 0.67, "var1": 1.0, "dists": None}
records = [sim.run_replicate("main", cell, rep, base_seed=1)[0] for rep in range(40)]
s = sim.summarize(records, sim.GAMMA_MAIN, 0.67, 1.0, scale="variance", ci="variance")
print(f"converged: {s['converged_pct']:.0f}% of {s['n']}")
print(f"{'parameter':<8}{'% bias':>9}{'non-coverage':>14}")
for p in sim.PARAMS:
    print(f"{p:<8}{s[p]['bias_pct']:>9.2f}{s[p]['noncoverage']:>14.3f}")
```

```text
converged: 100% of 40
parameter   % bias  non-coverage
g00         -0.71         0.025
g01         -1.38         0.100
g10          7.46         0.100
g11         -0.31         0.075
sigma0       2.97         0.075
sigma1      -8.39         0.100
```

## 6. From the command line

The same fit runs as `mlagq`, with the model given by column names. Without `-o` it writes the CSV to standard output, and the fit's status goes to standard error.

```python
!mlagq "{path}" --outcome y --group group --fixed 1 z x x:z --random 1 x --cov --start -1 0.3 0.3 0.3 0.67 0 1
```

```text
parameter,estimate,se
1,-1.130264,0.169431
z,0.339026,0.179075
x,0.280682,0.180987
x:z,0.475906,0.202845
var(1),0.791010,0.257778
cov(1;x),0.297796,0.216292
var(x),0.919357,0.332887
status gconv, converged True, 7 iterations, 7 quadrature points per dimension, log-likelihood -535.260526
```

`mlagq --simulate` runs replicates of one cell of the design: `--groups`, `--size`, `--var0` (0.13, 0.67 or 2.0 in the paper), `--reps` and `--seed`.

```python
!mlagq --simulate --groups 30 --size 30 --var0 0.67 --reps 5 --seed 2
```

```text
parameter,converged_pct,bias_pct,noncoverage
g00,100.0,1.0648,0.0000
g01,100.0,-29.1197,0.0000
g10,100.0,-24.1864,0.0000
g11,100.0,21.6452,0.0000
sigma0,100.0,12.0429,0.0000
sigma1,100.0,-3.9566,0.0000
```

## 7. Your own data

- **Input:** a CSV with one row per person: a group column, a 0/1 outcome and the covariates. Read it with `mlagq.read_long_csv` and fit it with `mlagq.fit_table`, or build arrays and call `mlagq.group_data` and `mlagq.fit`.
- **Model:** `fixed` lists the fixed effects: `1` for the intercept, a column name, or `a:b` for a product. `random` lists one or two random effects in the same notation, for example `["1"]` for a random intercept or `["1", "x"]` for a random intercept and slope. `cov=True` estimates their covariance.
- **Starting values:** `start` holds the fixed effects, then the variance parameters (`var`, or `var0, var1`, or `var0, cov01, var1`). The default is 0 for each fixed effect and 1 for each variance.
- **Output:** a `Fit` with `names`, `estimate`, `se` (from the observed information), `converged`, `status`, `iterations`, `qpoints` and `loglik`.
- **Convergence:** the fit stops when the largest gradient is below 1e-5 or the relative gradient below 1e-8 (NLMIXED's defaults), within 200 iterations. The variances are not constrained. When the maximum lies on the boundary (a variance of zero), the fit does not converge, and `status` says why. The paper also stopped a fit whose parameters changed by less than 1e-8 in an iteration (`absxconv=1e-8`). Such a fit counts as converged even on the boundary. `mlagq.fit` uses that rule only when you pass `absxconv`.

## 8. The reproduction

The whole simulation study (27 cells x 1,000 data sets for Tables 1-3, the prevalence study of Table 4 and the eight non-normal models of Table 5) is rerun and compared with the paper in the [PMC1955447 reproduction](https://github.com/jeonglab-bcm/fossil/tree/main/PMC1955447). Its results page is <https://jeonglab-bcm.github.io/fossil/PMC1955447/>.

<!-- Generated from tutorial.ipynb by check_package.py --write. Do not edit by hand. -->

# robustrr tutorial

`robustrr` estimates relative risks (RR) for a common binary outcome two ways: robust Poisson regression (the Poisson log-linear model with a sandwich variance) and log-binomial regression (maximum likelihood with a log link). When the log-binomial maximum lies on the boundary of the parameter space, where a fitted probability reaches 1, the plain fit does not converge and the COPY method takes over: the data get weight C = 1,000,000 and a copy with the outcome reversed gets weight 1. Chen et al. (2014) showed by simulation that when a few outcomes are flipped at extreme risks, the robust Poisson model is biased less than the log-binomial model, clearly so when the confounder acts on the outcome through a quadratic term.

Chen W, Shi J, Qian L, Azen SP. Comparison of robustness to outliers between robust poisson models and log-binomial models when estimating relative risks for common binary outcomes: a simulation study. *BMC Medical Research Methodology* 14:82 (2014). doi:10.1186/1471-2288-14-82

## 1. Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC4079617/package"
```

```python
import robustrr as rr

print("robustrr", rr.__version__)
```

```text
robustrr 0.1.0
```

## 2. The example input

One simulated cohort of 500 subjects from the paper's design (RR 2.0, outcome 10%, quadratic confounder, strong association), contaminated at 5%: the outcome `y` is reversed for the subjects whose true outcome probability is in the bottom or top 2.5% of the population. `x` is the exposure and `z` the confounder. The cohort is written by `scripts/make_example_data.py`.

```python
data = rr.read_table(rr.example_path("cohort.csv"))
n = len(data["y"])
print(f"{n} subjects; columns {list(data)}")
print(f"exposed {sum(data['x']) / n:.1%}, outcome {sum(data['y']) / n:.1%}")
print("first rows:")
for i in range(5):
    print({k: data[k][i] for k in data})
```

```text
500 subjects; columns ['id', 'y', 'x', 'z']
exposed 47.6%, outcome 15.2%
first rows:
{'id': 1.0, 'y': 0.0, 'x': 0.0, 'z': 0.963114}
{'id': 2.0, 'y': 0.0, 'x': 0.0, 'z': 0.747816}
{'id': 3.0, 'y': 0.0, 'x': 1.0, 'z': 0.862362}
{'id': 4.0, 'y': 0.0, 'x': 0.0, 'z': 0.909881}
{'id': 5.0, 'y': 1.0, 'x': 1.0, 'z': 0.357306}
```

## 3. Fit both models

`fit_relative_risk` fits the outcome on the covariates (exposure first; `z^2` adds the square of `z`) by both methods and reports each covariate's log RR, SE, RR and 95% CI. For the log-binomial model, `method` says whether the plain maximum (`mle`) or the COPY fit (`copy`) is reported.

```python
rows = rr.fit_relative_risk(data, "y", ["x", "z", "z^2"])
print(f"{'model':16s}{'log RR':>9s}{'SE':>8s}{'RR':>8s}   95% CI           method")
for r in rows:
    if r["term"] == "x":
        ci = f"{r['ci_low']:.3f} to {r['ci_high']:.3f}"
        print(f"{r['model']:16s}{r['log_rr']:9.4f}{r['se']:8.4f}{r['rr']:8.3f}   {ci:17s}{r.get('method', '')}")
lb = next(r for r in rows if r["model"] == "log_binomial")
print(f"largest fitted probability of the log-binomial fit: {lb['max_fitted']:.7f}")
```

```text
model              log RR      SE      RR   95% CI           method
robust_poisson     1.0010  0.2304   2.721   1.732 to 4.274
log_binomial       1.1232  0.2542   3.075   1.868 to 5.060   copy
largest fitted probability of the log-binomial fit: 0.9999998
```

The plain log-binomial maximum of this cohort is on the boundary, so the COPY fit is reported; its largest fitted probability sits just below 1. The true RR of `x` in the generating model is 2.0.

## 4. Compare with the expected output

`cohort_expected.csv` was computed without this package's fitting code: statsmodels for the robust Poisson fit, and scipy maximizing the COPY likelihood for the log-binomial fit (see `data/README.md`).

```python
import csv
import math

with open(rr.example_path("cohort_expected.csv")) as f:
    expected = list(csv.DictReader(f))
match = 0
for o, e in zip(rows, expected):
    same = (o["model"], o["term"]) == (e["model"], e["term"]) and all(
        math.isclose(o[k], float(e[k]), rel_tol=1e-6) for k in ("log_rr", "se", "rr", "ci_low", "ci_high"))
    match += same
print(f"{match} of {len(expected)} rows match the expected output (relative tolerance 1e-6)")
assert match == len(expected)
```

```text
6 of 6 rows match the expected output (relative tolerance 1e-6)
```

## 5. The command line

The same fit from the shell. `robustrr --example-path` prints where the bundled cohort is.

```python
path = rr.example_path("cohort.csv")
!robustrr fit "{path}" --outcome y --covariates x z z^2
```

```text
model,term,log_rr,se,rr,ci_low,ci_high,method,max_fitted
robust_poisson,x,1.00098397,0.2304157893,2.720957853,1.732174095,4.274172936,,
robust_poisson,z,-23.33198558,2.970478998,7.362874694e-11,2.180575369e-13,2.486129328e-08,,
robust_poisson,z^2,17.30179787,2.274955342,32664449.24,378120.1681,2821764967,,
log_binomial,x,1.123152797,0.2542136105,3.074532316,1.868065263,5.060181329,copy,0.9999998452
log_binomial,z,-19.122823,1.692001641,4.955226276e-09,1.798163106e-10,1.365519478e-07,copy,0.9999998452
log_binomial,z^2,15.0213628,1.505347826,3339604.033,174719.1805,63833604.67,copy,0.9999998452
```

## 6. One scenario of the simulation study

`run_scenario` draws data sets from one of the paper's 24 scenarios, contaminates each at 0%, 2% and 5%, and fits both models; `summarize` gives the relative bias (%) of the log RR, its empirical SE and the MSE. Here 200 data sets of 1,500 subjects (the paper used 1,000), next to the paper's Table 1 row for the same scenario.

```python
s = rr.scenario(1.5, 10, "nonlinear", "moderate")
res = rr.run_scenario(s, n=1500, reps=200, seed=2014)
paper = {"0%": ("0.0", "0.0"), "2%": ("-30.0", "-19.5"), "5%": ("-51.7", "-41.3")}
print(f"{'contamination':>14s}{'LB ours':>10s}{'paper':>8s}{'RP ours':>10s}{'paper':>8s}{'MC SE':>8s}{'COPY fits':>11s}")
for rate, d in res.items():
    lb, rp = rr.summarize(d["lb"], s["beta1"]), rr.summarize(d["rp"], s["beta1"])
    key = f"{round(100 * rate)}%"
    print(f"{key:>14s}{lb['relbias']:10.1f}{paper[key][0]:>8s}{rp['relbias']:10.1f}{paper[key][1]:>8s}"
          f"{lb['relbias_mcse']:8.1f}{int(d['copy'].sum()):11d}")
```

```text
 contamination   LB ours   paper   RP ours   paper   MC SE  COPY fits
            0%      -3.5     0.0      -3.5     0.0     2.7          0
            2%     -31.9   -30.0     -22.1   -19.5     2.4         69
            5%     -50.5   -51.7     -41.9   -41.3     2.6        106
```

With 200 data sets each relative bias carries the Monte Carlo SE in the `MC SE` column; the reproduction's 1,000 data sets of every scenario put all 144 cells of Table 1 within Monte Carlo error.

## 7. Your own data

- **Input**: a CSV with a header and one row per subject. The outcome column holds 0 or 1; covariates are numbers (code categories as 0/1 columns). List the exposure first; `name^2` adds a square.
- **Options**: `copy=False` (`--no-copy`) reports the plain log-binomial fit even when it does not converge; `copies` (`--copies`) sets C. A larger C is closer to the maximum likelihood estimate.
- **Output columns**: `model`, `term`, `log_rr`, `se`, `rr`, `ci_low`, `ci_high` (Wald 95%); for the log-binomial model `method` (`mle` or `copy`) and `max_fitted`, the largest fitted probability. The robust Poisson SE is the sandwich (HC0) SE; the log-binomial SE is the model-based one.

## 8. The full reproduction

Every scenario at n = 1,500 and 500, every printed cell of Tables 1-3 and A1-A3, and Fig. 1: <https://github.com/jeonglab-bcm/fossil/tree/main/PMC4079617>; results page <https://jeonglab-bcm.github.io/fossil/PMC4079617/>.

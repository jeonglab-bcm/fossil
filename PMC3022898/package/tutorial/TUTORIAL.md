<!-- Generated from tutorial.ipynb by check_package.py --write. Do not edit by hand. -->

# esrisk tutorial

`esrisk` estimates an exposure-specific risk (ESR), the risk of a disease given an exposure, from two independent samples: the overall risk P1(D) from one, the relative risk RR2 and the exposure probability P2(E) from another. The simple product-based estimator ESR_S = P1(D) x RR2 is biased upward when the exposure is common or the RR large; the revised estimator ESR_R divides out the exposed share of P1(D) first. Each comes with 95% confidence intervals: log-based for both, binomial for ESR_R.

Reichmann WM, Gagnon D, Horsburgh CR, Losina E. Evaluation of exposure-specific risks from two independent samples: a simulation study. *BMC Medical Research Methodology* 11:1 (2011). doi:10.1186/1471-2288-11-1

## 1. Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC3022898/package"
```

```python
import esrisk

print("esrisk", esrisk.__version__)
```

```text
esrisk 0.1.0
```

## 2. The example input

Seven pairs of samples as counts: `d1` cases among `n1` people in sample 1; in sample 2, `d2_exposed` cases among `n2_exposed` exposed people and `d2_unexposed` among `n2_unexposed` unexposed people. Six are drawn from settings of the paper's simulation grid; the last has no cases among the exposed of sample 2.

```python
rows = esrisk.read_counts(esrisk.example_path("two_samples.csv"))
cols = ["d1", "n1", "d2_exposed", "n2_exposed", "d2_unexposed", "n2_unexposed"]
print(f"{'label':26s}" + "".join(f"{c:>14s}" for c in cols))
for r in rows:
    print(f"{r['label']:26s}" + "".join(f"{r[c]:>14d}" for c in cols))
```

```text
label                                 d1            n1    d2_exposed    n2_exposed  d2_unexposed  n2_unexposed
scenario1_rr2_1000_1000               24          1000             4            59            18           941
scenario2_rr5_5000_5000              555          5000           110           256           410          4744
scenario3_rr3_1000_5000               32          1000            62          1012            84          3988
scenario3_rr5_1000_1000               39          1000            19           184            14           816
scenario4_rr1_5000_1000              425          5000            24           208            72           792
scenario4_rr4_250_250                 37           250            22            46            16           204
no_exposed_cases                      31          1000             0            48            19           933
```

## 3. Run the method

`estimate` takes the six counts (numbers or NumPy arrays) and returns both estimators and the three intervals. `estimate_table` does it for every row of the file.

```python
e = esrisk.estimate(39, 1000, 19, 184, 14, 816)
print(f"ESR_S {float(e.esr_s):.4f}, log CI {float(e.ci_s_log[0]):.4f} to {float(e.ci_s_log[1]):.4f}")
print(f"ESR_R {float(e.esr_r):.4f}, log CI {float(e.ci_r_log[0]):.4f} to {float(e.ci_r_log[1]):.4f}, "
      f"binomial CI {float(e.ci_r_binomial[0]):.4f} to {float(e.ci_r_binomial[1]):.4f}")

table = esrisk.estimate_table(rows, digits=4)
for r in table:
    print(f"{r['label']:26s} ESR_S {r['esr_s']} ({r['esr_s_log_lower']}-{r['esr_s_log_upper']})  "
          f"ESR_R {r['esr_r']} ({r['esr_r_log_lower']}-{r['esr_r_log_upper']}; binomial {r['esr_r_binomial_lower']}-{r['esr_r_binomial_upper']})")
```

```text
ESR_S 0.2347, log CI 0.1121 to 0.4913
ESR_R 0.1220, log CI 0.0550 to 0.2710, binomial CI 0.0747 to 0.1693
scenario1_rr2_1000_1000    ESR_S 0.0851 (0.0277-0.2614)  ESR_R 0.0740 (0.0238-0.2298; binomial 0.0072-0.1407)
scenario2_rr5_5000_5000    ESR_S 0.5519 (0.4582-0.6647)  ESR_R 0.4586 (0.3793-0.5545; binomial 0.3976-0.5196)
scenario3_rr3_1000_5000    ESR_S 0.0931 (0.0583-0.1486)  ESR_R 0.0671 (0.0401-0.1124; binomial 0.0327-0.1016)
scenario3_rr5_1000_1000    ESR_S 0.2347 (0.1121-0.4913)  ESR_R 0.1220 (0.0550-0.2710; binomial 0.0747-0.1693)
scenario4_rr1_5000_1000    ESR_S 0.1079 (0.0691-0.1684)  ESR_R 0.1022 (0.0654-0.1596; binomial 0.0838-0.1206)
scenario4_rr4_250_250      ESR_S 0.9025 (0.4792-1.6998)  ESR_R 0.4657 (0.2299-0.9432; binomial 0.3215-0.6098)
no_exposed_cases           ESR_S 0.0000 (0.0000-inf)  ESR_R 0.0000 (0.0000-inf; binomial 0.0000-0.0000)
```

With no cases among the exposed, ESR_S and ESR_R are 0 and the log intervals are (0, inf): the data bound the risk ratio from above only. That is the default, `zero_cells="unbounded"`.

## 4. Compare with the expected output

The expected output was computed by a separate implementation of the paper's equations (standard library only, `scripts/make_example_data.py`), not by esrisk.

```python
import csv
import math

cols = ["esr_s", "esr_s_log_lower", "esr_s_log_upper", "esr_r", "esr_r_log_lower", "esr_r_log_upper",
        "esr_r_binomial_lower", "esr_r_binomial_upper"]
with open(esrisk.example_path("two_samples_expected.csv"), newline="") as f:
    expected = {r["label"]: r for r in csv.DictReader(f)}

ours = esrisk.estimate_table(rows, digits=15)
same = 0
for r in ours:
    x = expected[r["label"]]
    ok = all((float(r[c]) == float(x[c])) or math.isclose(float(r[c]), float(x[c]), rel_tol=1e-9) for c in cols)
    same += ok
print(f"{same} of {len(ours)} rows match the expected output (8 values each, relative tolerance 1e-9)")
assert same == len(ours)
```

```text
7 of 7 rows match the expected output (8 values each, relative tolerance 1e-9)
```

## 5. From the command line

`esrisk estimate` reads the same CSV and writes the estimates as CSV (to standard output without `-o`).

```python
path = esrisk.example_path("two_samples.csv")
!esrisk estimate "{path}" --digits 4
```

```text
label,esr_s,esr_s_log_lower,esr_s_log_upper,esr_r,esr_r_log_lower,esr_r_log_upper,esr_r_binomial_lower,esr_r_binomial_upper
scenario1_rr2_1000_1000,0.0851,0.0277,0.2614,0.0740,0.0238,0.2298,0.0072,0.1407
scenario2_rr5_5000_5000,0.5519,0.4582,0.6647,0.4586,0.3793,0.5545,0.3976,0.5196
scenario3_rr3_1000_5000,0.0931,0.0583,0.1486,0.0671,0.0401,0.1124,0.0327,0.1016
scenario3_rr5_1000_1000,0.2347,0.1121,0.4913,0.1220,0.0550,0.2710,0.0747,0.1693
scenario4_rr1_5000_1000,0.1079,0.0691,0.1684,0.1022,0.0654,0.1596,0.0838,0.1206
scenario4_rr4_250_250,0.9025,0.4792,1.6998,0.4657,0.2299,0.9432,0.3215,0.6098
no_exposed_cases,0.0000,0.0000,inf,0.0000,0.0000,inf,0.0000,0.0000
```

## 6. One setting of the simulation study

`simulate` builds a population of 10 million with the given exposure probability, risk in the unexposed and RR, draws pairs of independent samples without replacement, and returns the estimates of every pair; `evaluate` gives the paper's measures. Scenario 3 of the paper (P(E) .20, P(D|not E) .02) at RR 5.0 and N1/N2 1000/1000 is where ESR_S is worst: the paper reports a relative bias of 93.9% for ESR_S and 0.3% for ESR_R.

```python
est, population, sample1, sample2 = esrisk.simulate(0.20, 0.02, 5.0, n1=1000, n2=1000, reps=1000, rng=20110105)
m = esrisk.evaluate(est, true_esr=5.0 * 0.02)
print(f"relative bias: ESR_S {100 * m['esr_s']['relative_bias']:.1f}%, ESR_R {100 * m['esr_r']['relative_bias']:.1f}%")
for name, label in [("ci_s_log", "log CI of ESR_S"), ("ci_r_log", "log CI of ESR_R"), ("ci_r_binomial", "binomial CI of ESR_R")]:
    print(f"coverage of the {label}: {100 * m[name]['coverage']:.1f}%")
```

```text
relative bias: ESR_S 91.5%, ESR_R 0.0%
coverage of the log CI of ESR_S: 64.8%
coverage of the log CI of ESR_R: 99.9%
coverage of the binomial CI of ESR_R: 92.8%
```

The paper prints coverages of 65.4% (ESR_S), 99.6% (log, ESR_R) and 93.8% (binomial, ESR_R) for this setting. Each run of 1,000 pairs moves these numbers by a point or two (Monte Carlo error).

## 7. Your own data

- **Counts.** A CSV with the columns of section 2, one row per pair of studies; `esrisk estimate FILE -o OUT.csv`. Output columns: `esr_s`, its log CI (`esr_s_log_lower`, `esr_s_log_upper`), `esr_r`, its log CI and its binomial CI (`esr_r_binomial_lower`, `esr_r_binomial_upper`).
- **Published summaries.** Most often only P1(D) with its sample size, an RR with its 95% CI and P(E) are published. `esr_from_summaries` takes those; the variance of ln RR2 comes from the CI. The paper's case study (Table 5: knee osteoarthritis in obese people) gives P1(D) by age, RR 1.91 and P(obese) 0.371:

```python
for age, p1 in [("50-59", 0.0040), ("60-69", 0.0087), ("70-79", 0.0147)]:
    s = float(esrisk.esr_simple(p1, 1.91))
    r = float(esrisk.esr_revised(p1, 1.91, 0.371))
    print(f"{age}: ESR_S {s:.4f}, ESR_R {r:.4f}")
```

```text
50-59: ESR_S 0.0076, ESR_R 0.0057
60-69: ESR_S 0.0166, ESR_R 0.0124
70-79: ESR_S 0.0281, ESR_R 0.0210
```

The paper prints 0.0076, 0.0167, 0.0282 (ESR_S) and 0.0057, 0.0125, 0.0211 (ESR_R): its overall risks were rounded to four decimals before printing, so two ages come out one unit lower here. Its CIs also need the sample sizes of the two studies, which the paper does not print; the reproduction recovers them.

- **Options.** `zero_cells` (`"unbounded"`, `"missing"`, `"not_covered"`, `"half"`) for samples with no cases in a group; `z` for another confidence level.

## 8. The reproduction

The paper's whole simulation (Tables 2-4, S1-S7, Figs 1-4) and its case study are rerun with this package in [PMC3022898](https://github.com/jeonglab-bcm/fossil/tree/main/PMC3022898): results page <https://jeonglab-bcm.github.io/fossil/PMC3022898/>, pipeline `PMC3022898/figure-reproduction/main.nf`.

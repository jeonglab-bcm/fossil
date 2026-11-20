<!-- Generated from tutorial.ipynb by check_package.py --write. Do not edit by hand. -->

# mutbench tutorial

`mutbench` scores mutation effect predictors against mutations whose effect is known: accuracy, sensitivity, specificity, PPV, NPV and a composite score with bootstrap intervals, Cohen's kappa between predictors, and 'at least p of n' combinations of predictors over random splits.

It is the method of:

> Martelotto LG, Ng CKY, De Filippo MR, Zhang Y, Piscuoglio S, Lim RS, Shen R, Norton L, Reis-Filho JS, Weigelt B. Benchmarking mutation effect prediction algorithms using functionally validated cancer-related missense mutations. *Genome Biology* 15:484 (2014). doi:10.1186/s13059-014-0484-1

The authors' code was never released; the package is implemented from the paper's text.

## 1. Install

Install the package from its folder in the repository:

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC4232638/package"
```

It needs Python 3.10 or later and NumPy. This notebook was run in a fresh environment with the package installed from its wheel. Check the version:

```python
import mutbench as mb

print("mutbench", mb.__version__)
```

```text
mutbench 0.1.0
```

## 2. The example input

The bundled example is the paper's own data for the six oncogenes: the 176 SNVs in BRAF, EGFR, ERBB2, KIT, KRAS and PIK3CA whose effect was tested, with the category each of the 15 predictors gave (from Additional file 2 of the paper, CC0).

```python
import csv

path = mb.example_path()
with open(path, newline="") as f:
    rows = list(csv.DictReader(f))
print(len(rows), "SNVs;", sum(r["label"] == "neutral" for r in rows), "neutral,", sum(r["label"] == "non-neutral" for r in rows), "non-neutral")
print("columns:", ", ".join(rows[0]))
for r in rows[:3]:
    print(r["gene"], r["mutation"], r["label"], r["CHASM (breast)"], r["MutationTaster"], r["CanDrA (lung)"])
```

```text
176 SNVs; 7 neutral, 169 non-neutral
columns: gene, mutation, label, CHASM (breast), CHASM (lung), CHASM (melanoma), FATHMM (cancer), FATHMM (missense), Mutation Assessor, MutationTaster, PolyPhen-2, PROVEAN, SIFT, VEST, CanDrA (breast), CanDrA (lung), CanDrA (melanoma), Condel
BRAF F595L non-neutral Driver disease_causing Driver
BRAF L597Q non-neutral Driver disease_causing Driver
BRAF L597R non-neutral Driver disease_causing Driver
```

## 3. Run the method

`read_calls_csv` merges each predictor's categories into non-neutral (1), neutral (0) or no call (NaN), as the paper does. `evaluate` scores every predictor, with percentile bootstrap intervals from 1,000 resamples (seeded, so the run repeats).

```python
labels, calls = mb.read_calls_csv(path)
results = mb.evaluate(labels, calls, n_boot=1000, seed=0)
print(f"{'predictor':18s} {'n':>4s} {'acc %':>7s} {'95% interval':>15s} {'NPV %':>7s} {'composite':>9s}")
for r in results:
    print(f"{r['predictor']:18s} {r['n']:4d} {100 * r['accuracy']:7.2f} {100 * r['accuracy_low']:7.2f}-{100 * r['accuracy_high']:6.2f} {100 * r['npv']:7.2f} {r['composite']:9.4f}")
```

```text
predictor             n   acc %    95% interval   NPV % composite
CHASM (breast)      176   82.39   76.70- 88.07   14.71    2.6757
CHASM (lung)        176   89.77   84.66- 94.32   26.09    3.0109
CHASM (melanoma)    176   84.09   78.41- 89.20   13.79    2.5410
FATHMM (cancer)     176   96.59   93.75- 99.43  100.00    3.1086
FATHMM (missense)   176   47.73   40.91- 54.55    4.30    2.0517
Mutation Assessor   175   62.29   55.43- 69.71    8.45    2.5451
MutationTaster      176   95.45   92.05- 98.31    0.00    1.9541
PolyPhen-2          176   87.50   82.95- 92.05   17.39    2.6133
PROVEAN             176   82.39   76.70- 87.50   16.67    2.8392
SIFT                176   84.09   78.98- 89.20   13.79    2.5410
VEST                176   92.05   88.07- 96.02   29.41    2.9248
CanDrA (breast)     176   76.70   70.45- 82.95    0.00    1.7495
CanDrA (lung)       160   95.00   91.25- 98.12   40.00    3.0144
CanDrA (melanoma)   147   68.03   60.54- 74.83    6.25    2.3254
Condel              176   65.91   58.52- 73.30    6.56    2.2736
```

## 4. Compare with the expected output

The paper prints these point values in Additional file 16 (oncogenes, n = 176). The expected output file holds them as printed; we compare at the printed precision.

```python
with open(mb.example_path("oncogene_expected.csv"), newline="") as f:
    expected = {r["predictor"]: r for r in csv.DictReader(f)}

def same(value, printed):
    dec = len(printed.split(".")[1]) if "." in printed else 0
    return abs(value - float(printed)) <= 0.5 * 10 ** -dec + 1e-12

hit = total = 0
for r in results:
    e = expected[r["predictor"]]
    for k in mb.STATS:
        v = r[k] * (1 if k == "composite" else 100)
        hit += same(v, e[k])
        total += 1
print(f"{hit} of {total} values match the paper's Additional file 16")
assert hit == total
```

```text
90 of 90 values match the paper's Additional file 16
```

Kappa between two predictors keeps a missing call as a third category, and its interval uses the standard error under no agreement, as the paper's Additional file 3 does:

```python
k, low, high = mb.cohen_kappa(calls["CHASM (breast)"], calls["CHASM (lung)"])
print(f"CHASM (breast) / CHASM (lung): kappa {k:.4f} ({low:.4f} to {high:.4f}), {mb.landis_koch(k)} agreement")
```

```text
CHASM (breast) / CHASM (lung): kappa 0.6882 (0.5444 to 0.8321), substantial agreement
```

Combinations: a mutation is called non-neutral when at least p of the n predictors in the rule call it so. Here every rule over three predictors, scored over 200 random two-thirds / one-third splits of the 176 SNVs:

```python
import numpy as np

keep = ~np.isnan(labels)
chosen = ["CHASM (breast)", "MutationTaster", "SIFT"]
sel = {p: calls[p][keep] for p in chosen}
combos = mb.combinations(chosen)
split = mb.split_sample(labels[keep], mb.combination_calls(sel, combos), mb.random_splits(int(keep.sum()), 200, seed=1))
for i in mb.rank(split["subset1"]["composite"]["mean"]):
    m, p = combos[i]
    s1 = split["subset1"]
    print(f"{mb.combination_name(m, p):55s} accuracy {100 * s1['accuracy']['mean'][i]:6.2f}%  composite {s1['composite']['mean'][i]:.4f}")
```

```text
At least 1 of CHASM (breast), SIFT                      accuracy  94.78%  composite 2.7033
At least 2 of CHASM (breast), MutationTaster, SIFT      accuracy  94.78%  composite 2.7033
At least 2 of CHASM (breast), SIFT                      accuracy  71.48%  composite 2.6661
At least 3 of CHASM (breast), MutationTaster, SIFT      accuracy  70.89%  composite 2.6578
At least 2 of CHASM (breast), MutationTaster            accuracy  81.69%  composite 2.6481
At least 2 of MutationTaster, SIFT                      accuracy  83.39%  composite 2.5131
At least 1 of CHASM (breast), MutationTaster            accuracy  96.04%  composite nan
At least 1 of CHASM (breast), MutationTaster, SIFT      accuracy  96.04%  composite nan
At least 1 of MutationTaster, SIFT                      accuracy  96.04%  composite nan
```

## 5. The command line

The same evaluation from the command line (`python -m mutbench` works too):

```python
!mutbench evaluate "{path}" --boot 0 -o performance.csv
with open("performance.csv", newline="") as f:
    cli = {r["predictor"]: r for r in csv.DictReader(f)}
print("CHASM (lung) accuracy from the command line:", round(100 * float(cli["CHASM (lung)"]["accuracy"]), 2))
assert all(abs(float(cli[r["predictor"]]["accuracy"]) - r["accuracy"]) < 1e-6 for r in results)
```

```text
CHASM (lung) accuracy from the command line: 89.77
```

## 6. Your own data

- **Input**: a CSV with a column `label` (`non-neutral` or `neutral`; other values, such as `uncertain`, are left out of the performance) and one column per predictor with its categories as the tool reports them (Driver/Passenger, CANCER/PASSENGER/OTHER, DAMAGING/TOLERATED, high/medium/low/neutral, disease_causing/polymorphism, probably/possibly damaging/benign, Deleterious/Neutral, Damaging/Tolerated, functional/neutral, D/N). An empty cell or 'No-call' is no call. Columns `id`, `gene` and `mutation` are carried along.
- **Options**: `n_boot` (resamples, 0 for none) and `seed`; for combinations, the predictors to combine and the number of splits.
- **Output of `evaluate`**: per predictor `n` (mutations with a call), `tp`, `tn`, `fp`, `fn`, and accuracy, sensitivity, specificity, PPV, NPV as fractions and the composite score (0 to 4), each with `_low` and `_high` interval ends. A statistic with no denominator (no predicted neutrals, for NPV) is empty.
- **Significance**: the paper calls two predictors different when their intervals touch or do not overlap: `mb.ci_better((low_a, high_a), (low_b, high_b))`.

## 7. The paper's full data

The reproduction runs this package on all 3,706 mutations of the paper and compares every table, figure and supplement with the published one: results page <https://jeonglab-bcm.github.io/fossil/PMC4232638/>, pipeline <https://github.com/jeonglab-bcm/fossil/tree/main/PMC4232638/figure-reproduction>.

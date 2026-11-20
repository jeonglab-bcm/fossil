# mutbench

Benchmark mutation effect predictors against mutations whose effect is known. For each predictor:
accuracy, sensitivity, specificity, PPV, NPV and the composite score (sensitivity + specificity + PPV +
NPV, 0 to 4), with bootstrap 95% intervals; Cohen's kappa between predictors with its interval;
complete-linkage clustering of the calls; three-category calls with a low-confidence class; and every
"at least p of n" combination of predictors, scored over random two-thirds / one-third splits.

The method is that of:

> Martelotto LG, Ng CKY, De Filippo MR, Zhang Y, Piscuoglio S, Lim RS, Shen R, Norton L, Reis-Filho JS, Weigelt B. Benchmarking mutation effect prediction algorithms using functionally validated cancer-related missense mutations. *Genome Biology* 15:484 (2014). doi:10.1186/s13059-014-0484-1

The authors' code was never released. This package is implemented from the paper's text, and checked
against everything the paper prints: on the paper's own spreadsheet it gives every count and point value
of Tables 1 to 4, every kappa of Additional files 3, 5, 11 and 13 to the last digit, and every mean of the
11,253 combinations of Additional files 17 and 18 within the resampling spread. The reproduction (pipeline,
results and comparison with the published figures) is in [`PMC4232638/`](../) of
[jeonglab-bcm/fossil](https://github.com/jeonglab-bcm/fossil); its page is
<https://jeonglab-bcm.github.io/fossil/PMC4232638/>.

Why Python: the paper's statistics need no R or Bioconductor package (counts, percentile bootstrap,
Cohen's kappa, complete linkage, random splits), so the default rule of the reproduction gives Python.
NumPy is the only dependency.

## Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC4232638/package"
```

Python 3.10 or later.

## Use

```python
import mutbench as mb

labels, calls = mb.read_calls_csv(mb.example_path())       # 176 oncogene SNVs, 15 predictors
for row in mb.evaluate(labels, calls, n_boot=1000, seed=0):
    print(row["predictor"], round(100 * row["accuracy"], 2), row["accuracy_low"], row["accuracy_high"])

k, low, high = mb.cohen_kappa(calls["CHASM (breast)"], calls["CHASM (lung)"])

combos = mb.combinations(["CHASM (breast)", "MutationTaster", "SIFT"])   # 'at least p of n' rules
```

From the command line:

```bash
mutbench evaluate "$(mutbench --example-path)" -o performance.csv
mutbench kappa "$(mutbench --example-path)" -o kappa.csv
mutbench combine "$(mutbench --example-path)" --predictors "CHASM (breast)" MutationTaster SIFT -o combinations.csv
```

The [tutorial](tutorial/TUTORIAL.md) installs the package, runs it on the bundled example, compares the
result with the paper's printed values and explains the input format.

## How the paper's unstated choices are made

The paper does not say how some steps are done. These choices reproduce its printed numbers:

- A call a predictor did not make (CanDrA 'No-call', FATHMM 'No weights', Mutation Assessor N/A) is left
  out of that predictor's performance, and kept as a third category ('equivocal') in kappa and clustering.
- Kappa's interval is kappa +/- 1.96 SE0, the standard error under kappa = 0, capped at 1.
- Bootstrap intervals are percentile intervals of resamples of all labelled mutations (not stratified).
- Low-confidence score intervals include their end points; a missing call is of low confidence.
- In a combination, a missing call does not count as non-neutral.

## Input and output

- Input CSV: a column `label` (`non-neutral` or `neutral`; any other value, such as `uncertain`, is left
  out of the performance) and one column per predictor with its categories as the predictor reports them
  (Driver/Passenger, CANCER/PASSENGER/OTHER, DAMAGING/TOLERATED, high/medium/low/neutral,
  disease_causing/polymorphism, probably damaging/possibly damaging/benign, Deleterious/Neutral,
  Damaging/Tolerated, functional/neutral, D/N). Columns `id`, `gene` and `mutation` are carried along.
- `evaluate` output: one row per predictor with `n` (mutations with a call), `tp`, `tn`, `fp`, `fn`, and
  each statistic as a fraction (composite 0 to 4) with `_low` and `_high` interval ends.
- `kappa` output: one row per pair, kappa and its interval.
- `combine` output: one row per combination with the mean and interval of each statistic in subsets 1 and 2.

## Licence

MIT. See [LICENSE](LICENSE). The example data come from the paper's Additional file 2 (CC0); see
[data/README.md](src/mutbench/data/README.md).

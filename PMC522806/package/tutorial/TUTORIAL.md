<!-- Generated from tutorial.ipynb by check_package.py --write. Do not edit by hand. -->

# cfsenn tutorial

`cfsenn` classifies expression samples. On each of 100 bootstrap resamples of the training samples it picks three feature sets (the top 30 genes by the Wilcoxon rank-sum test, the top 15 principal components, and 30 genes taken one per cluster after clustering the genes), trains a small neural network on each, and averages their confidences. The 100 answers are combined by soft voting.

The method is from:

> Liu B, Cui Q, Jiang T, Ma S. A combinational feature selection and ensemble neural network method for classification of gene expression data. *BMC Bioinformatics* 5:136 (2004). doi:10.1186/1471-2105-5-136

The authors' Matlab code was never released; this package implements the method from the paper's text. The settings the paper does not give (how the networks are trained, how the genes are clustered) are listed in the README.

## 1. Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC522806/package"
```

It needs Python 3.10 or later, NumPy and SciPy. This notebook was run in a fresh environment with the package installed from its wheel.

```python
import csv
import os

os.environ.setdefault("OMP_NUM_THREADS", "1")  # one BLAS thread: the same numbers on every machine

import numpy as np

import cfsenn

print("cfsenn", cfsenn.__version__)
```

```text
cfsenn 0.1.0
```

## 2. The example input

Two CSV tables with the same genes: a training table (40 samples) and a test table (20 samples). The first column is the class, the others are genes. The data are synthetic: 500 genes, of which 30 differ between "normal" and "tumor" in three co-expressed blocks (`scripts/make_example_data.py`, described in `data/README.md`).

```python
train = cfsenn.read_table(cfsenn.example_path("example_train.csv"))
test = cfsenn.read_table(cfsenn.example_path("example_test.csv"))
X, y, genes, classes = train
print(f"training: {X.shape[0]} samples x {X.shape[1]} genes; classes {classes}, {np.bincount(y).tolist()} per class")
print(f"test: {test[0].shape[0]} samples")
print("first sample, first 5 genes:", X[0, :5].tolist())
```

```text
training: 40 samples x 500 genes; classes ['normal', 'tumor'], [20, 20] per class
test: 20 samples
first sample, first 5 genes: [80.43, 123.04, 121.72, 137.91, 136.77]
```

## 3. Run the method

`cfsenn.run` fits the ensemble on the training table with the paper's settings (100 resamples, 30 + 15 + 30 features, 10 hidden units) and classifies the test samples. Each prediction carries its confidence: the averaged vote for the predicted class.

```python
res = cfsenn.run(train, test, seed=0)
print(f"{'sample':>6}  {'true':<7}{'predicted':<10}confidence")
for p in res["predictions"]:
    print(f"{p['sample']:>6}  {p['true']:<7}{p['predicted']:<10}{p['confidence']:.3f}")
```

```text
sample  true   predicted confidence
     1  normal normal    0.955
     2  normal normal    0.921
     3  normal normal    0.807
     4  normal normal    0.615
     5  normal normal    0.910
     6  normal normal    0.956
     7  normal normal    0.973
     8  normal normal    0.763
     9  normal normal    0.975
    10  normal normal    0.826
    11  tumor  tumor     0.971
    12  tumor  tumor     0.992
    13  tumor  tumor     0.612
    14  tumor  tumor     0.947
    15  tumor  tumor     0.895
    16  tumor  tumor     0.973
    17  tumor  tumor     0.870
    18  tumor  tumor     0.843
    19  tumor  tumor     0.763
    20  tumor  tumor     0.945
```

## 4. Compare with the expected output

`example_test_expected.csv` holds the class each test sample was drawn from by the generator, not output of this package.

```python
with open(cfsenn.example_path("example_test_expected.csv"), newline="") as f:
    expected = [row["class"] for row in csv.DictReader(f)]
match = sum(p["predicted"] == e for p, e in zip(res["predictions"], expected))
print(f"{match} of {len(expected)} test samples match the expected class")
assert match == len(expected)
```

```text
20 of 20 test samples match the expected class
```

## 5. From the command line

The same run as `cfsenn TRAIN TEST -o predictions.csv`. With only a training table it reports leave-one-out cross-validation.

```python
train_path = cfsenn.example_path("example_train.csv")
test_path = cfsenn.example_path("example_test.csv")
!cfsenn "{train_path}" "{test_path}" -o predictions.csv
!cut -d, -f1-3 predictions.csv | head -4
```

```text
20 of 20 correct (100.00%)
sample,true,predicted
1,normal,normal
2,normal,normal
3,normal,normal
```

## 6. Your own data

- **Input:** a CSV or TSV table per set, one row per sample. The first column is named `class` and holds the class names; every other column is a gene (or any feature). Blank, `NA` or `?` cells are missing and are filled with the gene's training mean. Use the values as they are (the paper used the Kent Ridge "transformed" files without further preprocessing); each feature is scaled to z-scores on the training resample.
- **Two or more classes:** for more than two, the rank-sum and t tests become Kruskal-Wallis and one-way F tests and each network has one output per class.
- **Options:** `cfsenn.Ensemble(**settings)` takes `n_bags`, `n_rank`, `n_pc`, `n_cluster_genes`, `n_clusters`, `n_prefilter`, `hidden`, `alpha` (weight decay), `maxiter`, `vote` (`"soft"` or `"hard"`), `resample` (`"bagging"`, `"adaboost"` or `"none"`), `select_per_bag` and `seed`. `cfsenn.cross_validate(X, y, folds)` gives held-out predictions for any fold assignment (`np.arange(n)` for leave-one-out, `cfsenn.stratified_folds(y, 10)` for 10-fold).
- **Output:** for each test sample its number, true class, predicted class and confidence (between 1/K and 1 for K classes).

## 7. The paper's data

The reproduction of the paper with this package, on the seven Kent Ridge datasets, is in the fossil repository: [PMC522806](https://github.com/jeonglab-bcm/fossil/tree/main/PMC522806), with its [results page](https://jeonglab-bcm.github.io/fossil/PMC522806/).

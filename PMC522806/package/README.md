# cfsenn

Classification of expression samples by combinational feature selection and an ensemble of neural networks. On each of 100 bootstrap resamples of the training samples, three feature sets are chosen (the top 30 genes by the Wilcoxon rank-sum test, the top 15 principal components of all genes, and 30 genes taken one per cluster after clustering the genes into 50 clusters, ranked by t-test), one small network is trained on each, and their confidences are averaged. The 100 answers are combined by soft voting.

The method comes from:

> Liu B, Cui Q, Jiang T, Ma S. A combinational feature selection and ensemble neural network method for classification of gene expression data. *BMC Bioinformatics* 5:136 (2004). [doi:10.1186/1471-2105-5-136](https://doi.org/10.1186/1471-2105-5-136)

The authors wrote it in Matlab and never released the code. This package implements the method from the paper's text (Python, by the default rule: the method needs no R or Bioconductor package, and there is no original code to port). It was checked against the paper's printed accuracies only, not against the original code. Its reproduction of the paper (pipeline, results and comparison with the published tables and figures) is at [PMC522806](https://github.com/jeonglab-bcm/fossil/tree/main/PMC522806).

## Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC522806/package"
```

Python 3.10 or later, with NumPy and SciPy.

## Use

```python
import cfsenn

train = cfsenn.read_table(cfsenn.example_path("example_train.csv"))  # bundled example data
test = cfsenn.read_table(cfsenn.example_path("example_test.csv"))
res = cfsenn.run(train, test)  # the paper's settings: 100 resamples, 30 + 15 + 30 features
print(res["accuracy"])
```

Or with arrays: `cfsenn.Ensemble().fit(X, y).predict(X_new)`, with X samples x genes and y class indices. `cfsenn.cross_validate(X, y, folds)` gives held-out predictions (`numpy.arange(n)` for leave-one-out).

From the command line:

```bash
cfsenn train.csv test.csv -o predictions.csv
```

The [tutorial](tutorial/TUTORIAL.md) installs the package, runs it on the bundled example data, compares the result with the expected classes, and explains the input and output formats.

## Input and output

- Input: CSV or TSV, one row per sample; first column `class`, then one column per gene. Missing cells (blank, `NA`, `?`) are filled with the gene's mean over the training samples.
- Output: for each test sample, its true class, the predicted class and the confidence (the averaged vote for that class).

## What the paper states, and what we chose

| Setting | Value | Source |
| --- | --- | --- |
| Resamples | 100 bootstrap resamples (bagging); features chosen on each resample | paper |
| Feature sets | top 30 genes by rank-sum test; top 15 principal components; 50 gene clusters, then the top 30 genes by t-test | paper |
| Networks | one per feature set; one hidden layer of 10 units; one output (two classes) or one per class | paper |
| Combination | the three networks' confidences averaged; the 100 answers combined by soft voting | paper |
| Hidden and output units | tanh; logistic (two classes) or softmax | our choice |
| Training | cross-entropy with weight decay 0.01, L-BFGS, at most 200 iterations, weights drawn uniformly in ±1/√(fan-in), seeded | our choice |
| Input scaling | each feature to z-scores on the resample | our choice |
| PCA | genes centred, not scaled | our choice |
| "Masked out clustering" | the 500 genes with the largest Welch t; k-means (k-means++ start) on their standardized profiles, that is correlation distance; genes taken in order of t, each one masking the rest of its cluster | our choice, after Jaeger, Sengupta and Ruzzo (2003) |
| Tests | Mann-Whitney z and Welch t; Kruskal-Wallis H and one-way F for more than two classes | our choice |
| Missing values | the gene's training mean | our choice |
| Resamples without two samples of every class | drawn again | our choice |

Every setting is a keyword argument of `cfsenn.Ensemble`, with these defaults in `cfsenn.DEFAULTS`. `resample="adaboost"` (AdaBoost.M1 by weighted resampling), `resample="none"`, `vote="hard"`, `select_per_bag=False` and the feature sets `"random"` and `"combined"` give the variants the paper's Discussion compares.

## Licence

MIT. See [LICENSE](LICENSE). The example data are described in [data/README.md](src/cfsenn/data/README.md).

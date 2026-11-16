# pacorg

Pathway activity inference with condition-responsive genes (CORGs). For each pathway, `pacorg`
finds the subset of its genes whose combined expression best separates two classes of samples, and
summarizes the pathway in each sample as the combined z-score of those genes. The method is from:

> Lee E, Chuang HY, Kim JW, Ideker T, Lee D. Inferring pathway activity toward precise disease
> classification. *PLoS Computational Biology* 4(11):e1000217 (2008).
> [doi:10.1371/journal.pcbi.1000217](https://doi.org/10.1371/journal.pcbi.1000217)

The authors' software is lost. `pacorg` was written from the paper's Methods and checked against
the paper, not against their code: on the paper's lung datasets it returns every CORG list of
Table 1 (18 of 18). Its reproduction (pipeline, results and comparison with the published figures)
is in [PMC2563693](../) of the fossil repository.

**Language:** Python. The authors' code is gone and the method needs only NumPy and SciPy, so by the
Paper2Repro default rule (R only when the method relies on R or Bioconductor packages) it is Python.

## Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC2563693/package"
```

Python 3.10 or later; NumPy and SciPy.

## Use

```python
import pacorg as pc

genes, samples, X = pc.read_gct(pc.example_path("example.gct"))  # genes x samples
labels = pc.read_cls(pc.example_path("example.cls"))
sets = pc.read_gmt(pc.example_path("example.gmt"))
for r in pc.infer_pathways(X, genes, labels, sets):
    print(r.name, r.corgs, round(r.score, 2))
```

From the command line:

```bash
pacorg EXPRESSION.gct LABELS.cls GENESETS.gmt [--top 52] -o corgs.csv
pacorg --example
```

The [tutorial](tutorial/TUTORIAL.md) installs the package, runs it on the bundled example,
compares the result with the expected output, and shows how to get the paper's Table 1 from the
GSEA lung data.

## What it computes

| Function | |
| --- | --- |
| `zscore(X)` | Each gene (row) to mean 0 and standard deviation 1 over all samples. |
| `t_scores(X, y)` | Student's two-sample t (pooled variance) per row. |
| `activity(Z, rows)` | Sum of the member z-scores over sqrt(number of members). |
| `find_corgs(Z, y, rows)` | The greedy CORG search: members ranked by t (descending when their mean t is positive), added while the |t| of the activity increases. |
| `tian_scores(t, sets)` | Tian et al.'s pathway score, sum of member t over sqrt(members). The paper's text calls it the average t; the standardized sum is what its Table 1 and Fig. 2 follow. |
| `infer_pathways(X, genes, labels, sets)` | All of the above for every gene set. |
| `mean_activity`, `median_activity`, `pca_activity` | The summaries the paper compares against (Guo et al. 2005, Bild et al. 2006). |
| `fit_logistic`, `sequential_selection`, `auc` | Logistic regression with markers added in order of p-value and the count chosen by validation AUC. |

## Licence

MIT. See [LICENSE](LICENSE). The example data are synthetic; see
[data/README.md](src/pacorg/data/README.md).

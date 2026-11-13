<!-- Generated from tutorial.ipynb by check_package.py --write. Do not edit by hand. -->

# fgnssl tutorial

`fgnssl` predicts synthetic genetic interactions (SGI) between gene pairs. It builds a weighted functional gene network from protein interactions and expression profiles, describes each gene pair by 18 network features, and spreads the known labels to the unknown pairs with graph-based semi-supervised learning.

It rebuilds, from the paper's text, the method of You ZH, Yin Z, Han K, Huang DS, Zhou X. A semi-supervised learning approach to predict synthetic genetic interactions by combining functional and topological properties of functional gene network. *BMC Bioinformatics* 11:343 (2010). [doi:10.1186/1471-2105-11-343](https://doi.org/10.1186/1471-2105-11-343). The authors' code is lost.

## 1. Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC2909217/package"
```

It needs Python 3.10 or later and installs numpy, scipy, scikit-learn, python-igraph and numba.

```python
import fgnssl

print("fgnssl", fgnssl.__version__)
```

```text
fgnssl 0.1.0
```

## 2. The example input

Three small synthetic files ship with the package (`data/README.md` says how they were made): expression profiles of 40 genes in 12 conditions, 84 interactions between them, and 60 gene pairs, half of them labelled (1 = SGI, 0 = not, blank = unknown).

```python
genes, X = fgnssl.read_expression(fgnssl.example_path("expression.csv"))
interactions = fgnssl.read_edges(fgnssl.example_path("interactions.csv"))
pairs, labels = fgnssl.read_pairs(fgnssl.example_path("pairs.csv"))
print(len(genes), "genes x", X.shape[1], "conditions;", len(interactions), "interactions;", len(pairs), "pairs")
print("labelled:", int((labels == 1).sum()), "SGI,", int((labels == 0).sum()), "non-SGI,", int((labels == -1).sum()), "unknown")
print("first pairs:", pairs[:3], labels[:3])
```

```text
40 genes x 12 conditions; 84 interactions; 60 pairs
labelled: 15 SGI, 15 non-SGI, 30 unknown
first pairs: [('G11', 'G13'), ('G17', 'G19'), ('G10', 'G19')] [ 1 -1  1]
```

## 3. Run the method

`build_fgn` clusters the profiles by divisive correlation clustering and weights each interaction by eq. 2 of the paper. `pair_features` computes the 18 features of each pair. `predict` scales the features and runs label spreading; it returns a soft SGI label in [0, 1] for every pair.

```python
net = fgnssl.build_fgn(genes, X, interactions)
print(net.clusters.max() + 1, "expression clusters;", len(net.edges), "weighted edges; median weight", round(float(sorted(net.weights)[len(net.weights) // 2]), 3))

features = fgnssl.pair_features(net, pairs)
scores = fgnssl.predict(features, labels)
print(f"{'pair':<10}{'label':>6}{'degree avg':>12}{'shortest path':>15}{'SGI score':>11}")
for (a, b), lab, F, s in list(zip(pairs, labels, features, scores))[:8]:
    print(f"{a + '-' + b:<10}{lab:>6}{F[0]:>12.2f}{F[16]:>15.4f}{s:>11.3f}")
```

```text
8 expression clusters; 84 weighted edges; median weight 0.719
pair       label  degree avg  shortest path  SGI score
G11-G13        1       10.83         0.9215      0.508
G17-G19       -1        9.74         2.4443      0.498
G10-G19        1       16.52         0.2947      0.508
G03-G07       -1        5.46         3.4064      0.498
G03-G09        1       11.48         2.0676      0.507
G23-G25       -1       14.00         0.7839      0.499
G14-G17        1        4.02         4.0148      0.511
G21-G25       -1       20.92         0.2577      0.499
```

## 4. Compare with the expected output

The expected scores ship with the package. They were computed without it, by scikit-learn's `LabelSpreading` on features computed with networkx and the definitions (`data/README.md`), so a match is a real check.

```python
import numpy as np

expected = np.array([float(r["sgi_score"]) for r in fgnssl.read_table(fgnssl.example_path("expected_scores.csv"))])
matches = int(np.sum(np.abs(scores - expected) <= 1e-6))
print(matches, "of", len(expected), "pair scores match the expected output (within 1e-6)")
assert matches == len(expected)

ef = np.array([[float(r[k]) for k in fgnssl.FEATURE_NAMES] for r in fgnssl.read_table(fgnssl.example_path("expected_features.csv"))])
print(int(np.sum(np.all(np.isclose(features, ef, rtol=1e-6, atol=1e-9), axis=1))), "of", len(ef), "pairs have all 18 features as expected")
```

```text
60 of 60 pair scores match the expected output (within 1e-6)
60 of 60 pairs have all 18 features as expected
```

How well the scores rank the hidden pairs (their true labels are in `pairs.csv`):

```python
truth = np.array([int(r["true_label"]) for r in fgnssl.read_table(fgnssl.example_path("pairs.csv"))])
hidden = labels == -1
fpr, tpr = fgnssl.roc_curve(scores[hidden], truth[hidden])
print("area under the ROC curve on the hidden pairs:", round(fgnssl.auc(fpr, tpr), 3))
```

```text
area under the ROC curve on the hidden pairs: 0.409
```

## 5. From the command line

The same run as `fgnssl`. Without `-o` it writes the CSV to standard output: the pair, its 18 features and, when the pairs file has a `label` column, the SGI score.

```python
import subprocess

paths = [str(fgnssl.example_path(n)) for n in ("expression.csv", "interactions.csv", "pairs.csv")]
out = subprocess.run(["fgnssl", *paths], capture_output=True, text=True, check=True).stdout.splitlines()
print(out[0][:80], "...")
print(len(out) - 1, "rows; first score:", out[1].split(",")[-1])
```

```text
gene_a,gene_b,avg_degree,avg_clustering,avg_betweenness,avg_closeness,avg_eigenv ...
60 rows; first score: 0.507785506
```

## 6. Your own data

- **Expression:** a CSV with a `gene` column and one column per condition (log ratios); blank cells are replaced by the condition's mean, as in the paper.
- **Interactions:** a CSV with `gene_a`, `gene_b`: protein interactions, plus every pair of proteins that share a complex. Genes without an expression row are dropped.
- **Pairs:** a CSV with `gene_a`, `gene_b` and `label` (1, 0 or blank). Both genes must be in the network.
- **Options:** `l1` (eq. 2 trade-off, 0.3), `sigma` (the SSL length scale; by default the median distance, or `select=True` to choose it on the labels), `alpha` (0.99), and `weighted=False` for the binary network.
- **Output:** `fgnssl.FEATURE_NAMES` names the 18 feature columns: the average and the absolute difference of 8 node properties, the weighted shortest path and the number of mutual neighbours. The score is F*[SGI] / (F*[SGI] + F*[non-SGI]).

## 7. The reproduction

The paper's full data (Tong et al. 2004 screen, BioGRID interactions, Gavin and Ho complexes, four expression time courses) are run through this package by the Nextflow pipeline in [`PMC2909217/figure-reproduction`](https://github.com/jeonglab-bcm/fossil/tree/main/PMC2909217/figure-reproduction). The results page compares each figure with the published one: <https://jeonglab-bcm.github.io/fossil/PMC2909217/>.

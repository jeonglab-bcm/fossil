# fgnssl

Synthetic genetic interaction (SGI) prediction from a weighted functional gene network (FGN) with
graph-based semi-supervised learning, rebuilt from the paper:

> You ZH, Yin Z, Han K, Huang DS, Zhou X. A semi-supervised learning approach to predict synthetic genetic
> interactions by combining functional and topological properties of functional gene network.
> *BMC Bioinformatics* 11:343 (2010). [doi:10.1186/1471-2105-11-343](https://doi.org/10.1186/1471-2105-11-343)

The authors' program (GeneticInterPred) is lost: its page has answered 404 since at least 2022. This package
implements the method from the paper's text:

- divisive correlation clustering of expression profiles (Bhattacharya and De 2008, as the paper describes it);
- eq. 2 edge weights from each gene's distance to its cluster centroid and the distance between centroids (L1 = 0.3);
- the 10 network properties of Table 2: weighted degree, Barrat clustering, betweenness, closeness and eigenvector
  centrality, weighted shortest paths (on 1 / w), and the binary stress, information and current-flow betweenness
  centralities and mutual neighbours, built into 18 pair features;
- label spreading (Zhou et al. 2004), the paper's semi-supervised classifier, with an RBF SVM baseline.

**Language.** Python: the paper names no R dependency, its tools were igraph (also in Python) and LIBSVM
(scikit-learn wraps it), and there is no authors' code to follow.

**Checked against.** The paper only, because the original code is lost. The reproduction
([`../figure-reproduction/`](../figure-reproduction/)) runs this package on the paper's data sources: the method
runs as written, but its curves stay far below the published ones (see the results page).

## Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC2909217/package"
```

Python 3.10 or later; numpy, scipy, scikit-learn, python-igraph and numba are installed with it.

## Quick start

```python
import fgnssl

genes, X = fgnssl.read_expression(fgnssl.example_path("expression.csv"))
net = fgnssl.build_fgn(genes, X, fgnssl.read_edges(fgnssl.example_path("interactions.csv")))
pairs, labels = fgnssl.read_pairs(fgnssl.example_path("pairs.csv"))
features = fgnssl.pair_features(net, pairs)      # 18 features per pair
scores = fgnssl.predict(features, labels)        # soft SGI labels in [0, 1]
```

The same from the command line:

```bash
fgnssl expression.csv interactions.csv pairs.csv -o scores.csv
```

The [tutorial](tutorial/TUTORIAL.md) runs it on the bundled example and checks the result against outputs computed
without this package.

## Licence

MIT (the method is implemented from the paper's text). The example data are synthetic.

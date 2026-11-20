# geodenoise

Geometric de-noising of protein-protein interaction networks. The package embeds a network in low-dimensional Euclidean space by multidimensional scaling of shortest-path lengths. Non-adjacent pairs that lie close together are predicted interactions (Algorithm 1). Every pair within a distance cut-off gets a confidence score from Gaussian-mixture densities of edge and non-edge distances (Algorithm 2). Edges whose ends lie far apart are candidate false positives.

The method comes from:

> Kuchaiev O, Rašajski M, Higham DJ, Pržulj N. Geometric de-noising of protein-protein interaction networks. *PLoS Comput Biol* 5(8):e1000454 (2009). doi:10.1371/journal.pcbi.1000454

Its reproduction (pipeline, results and comparison with the published figures) is at [`PMC2711306`](https://github.com/jeonglab-bcm/fossil/tree/main/PMC2711306) in the fossil repository.

## Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC2711306/package"
```

Python 3.10 or later, with NumPy and SciPy.

## Use

```python
import geodenoise as gd

net = gd.read_network(gd.example_path())           # the bundled example network
D = gd.pairwise_distances(gd.embed(net, 2))        # embedding distances
pred = gd.predict(net, D, epsilon=0.05)            # Algorithm 1
f_edge, f_non = gd.learn_densities(net, D, rng=0)  # p(dist|edge), p(dist|nonedge)
scores = gd.confidence_scores(net, D, f_edge, f_non, prior_edge=0.001, delta=0.4)  # Algorithm 2
```

From the command line:

```bash
geodenoise scores network.tsv --dim 5 --delta 0.4 --prior 0.001 -o scores.csv --false-positives far_edges.tsv
geodenoise predict network.tsv --dim 5 --epsilon 0.1 -o predicted.csv
geodenoise distances "$(geodenoise --example-path)" --dim 2 -o distances.csv
```

The [tutorial](tutorial/TUTORIAL.md) installs the package, runs it on the bundled example, compares the result with the expected output from the authors' code, and explains the input and output formats.

## Why Python, and what it was checked against

The authors' code is Matlab (three short functions, free for non-commercial use, archived by the Wayback Machine from kuchaev.com/Denoising). By the default rule a Matlab method becomes a Python package. This package is an independent implementation from the paper; it contains none of the authors' code. It takes the settings the paper leaves out from the authors' code: path lengths up to 29, an unreachable value of 200, the diagonal at 2, each axis rescaled to [0, 1], P(edge) = 0.001, 18,000 training distances, and EM stopping at a log-likelihood change below 0.01. The embedding was checked against the authors' `embed_novi.m` run under GNU Octave. On the paper's yeast network, distances differ by at most 0.018 (dimension 4; at most 0.0033 in dimensions 2, 3, 5, 6 and 7), and ROC counts differ by under 1%. The authors' iteration stops at a change of 0.001; this package solves the eigenproblem exactly (`solver="subspace"` runs the same iteration from a seeded start). On the bundled example the largest difference is 0.002.

## Input and output

- Input: an edge list, two columns of protein names (tab- or comma-separated, optional header).
- `scores` output: CSV with `protein_a`, `protein_b`, `distance`, `posterior`, `score` (posterior divided by its maximum) and `is_edge`.
- `predict` and `distances` output: CSV with `protein_a`, `protein_b`, `distance`.

## Licence

MIT. See [LICENSE](LICENSE). The example data are described in [data/README.md](src/geodenoise/data/README.md).

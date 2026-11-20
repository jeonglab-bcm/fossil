<!-- Generated from tutorial.ipynb by check_package.py --write. Do not edit by hand. -->

# geodenoise tutorial

`geodenoise` places the proteins of an interaction network in a low-dimensional Euclidean space so that interacting proteins lie close together. It then uses the distances in two ways. Non-interacting pairs that lie very close are candidate missing interactions. Interacting pairs that lie far apart are candidate false positives. Every pair within a cut-off gets a confidence score from Gaussian-mixture densities of edge and non-edge distances.

> Kuchaiev O, Rašajski M, Higham DJ, Pržulj N. Geometric de-noising of protein-protein interaction networks. *PLoS Comput Biol* 5(8):e1000454 (2009). doi:10.1371/journal.pcbi.1000454

## 1. Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC2711306/package"
```

It needs Python 3.10 or later, NumPy and SciPy. This notebook ran in a fresh environment with the package installed from its wheel. Check the version:

```python
import numpy as np
import geodenoise as gd

print("geodenoise", gd.__version__)
```

```text
geodenoise 0.1.0
```

## 2. The example input

The package ships a small synthetic network: 150 points scattered in the unit square and joined when closer than 0.15 (a geometric random graph, the paper's model of a PPI network). 10% of the true edges were then deleted and as many spurious edges added. `data/README.md` says how it was made. The input is a two-column edge list:

```python
path = gd.example_path("geometric_network.tsv")
print(path.read_text().splitlines()[:4])
net = gd.read_network(path)
print(net.n, "proteins,", net.m, "interactions")
```

```text
['protein_a\tprotein_b', 'P001\tP010', 'P001\tP036', 'P001\tP044']
150 proteins, 665 interactions
```

## 3. Run the method

Embed the network in 2 dimensions and compute the distance between every pair. Then apply Algorithm 1: every non-adjacent pair closer than epsilon is a predicted interaction. The deleted edges are known here, so we can count how many predictions recover one.

```python
X = gd.embed(net, 2)
D = gd.pairwise_distances(X)
missing = gd.read_network(gd.example_path("geometric_missing.tsv"))
truth = {frozenset((missing.nodes[i], missing.nodes[j])) for i, j in missing.edges}
for eps in (0.02, 0.05, 0.1):
    pred = gd.predict(net, D, eps)
    hits = sum(frozenset((net.nodes[i], net.nodes[j])) in truth for i, j in pred)
    print(f"epsilon {eps}: {len(pred)} predicted pairs, {hits} of them deleted edges (of {len(truth)})")
```

```text
epsilon 0.02: 13 predicted pairs, 2 of them deleted edges (of 66)
epsilon 0.05: 101 predicted pairs, 7 of them deleted edges (of 66)
epsilon 0.1: 318 predicted pairs, 11 of them deleted edges (of 66)
```

Algorithm 2 scores every pair within distance delta. Here the edge and non-edge densities are learned from all edges and an equal number of non-edges. The best-scoring pairs that are not edges come first:

```python
f_edge, f_non = gd.learn_densities(net, D, size=net.m, rng=0)
scores = gd.confidence_scores(net, D, f_edge, f_non, delta=0.1)
new = scores[~scores["is_edge"]][:5]
for r in new:
    pair = frozenset((net.nodes[r["i"]], net.nodes[r["j"]]))
    print(net.nodes[r["i"]], net.nodes[r["j"]], f"distance {r['distance']:.4f}", f"score {r['score']:.3f}",
          "(a deleted edge)" if pair in truth else "")
far = gd.candidate_false_positives(net, D, delta=0.3)
spurious = gd.read_network(gd.example_path("geometric_spurious.tsv"))
sp = {frozenset((spurious.nodes[i], spurious.nodes[j])) for i, j in spurious.edges}
print(len(far), "edges further apart than 0.3;",
      sum(frozenset((net.nodes[i], net.nodes[j])) in sp for i, j in far), "of them spurious")
```

```text
P090 P123 distance 0.0906 score 1.000
P067 P032 distance 0.0910 score 1.000
P067 P070 distance 0.0904 score 1.000
P050 P089 distance 0.0911 score 1.000
P007 P123 distance 0.0903 score 1.000
46 edges further apart than 0.3; 25 of them spurious
```

## 4. Compare with the expected output

The expected output is the pairwise distances of the same embedding computed by the authors' own Matlab code (`embed_novi.m`, run under GNU Octave). The package did not write it. The authors' subspace iteration stops when no vector changes by more than 0.001, so the two agree to about that precision. We compare at a tolerance of 0.005:

```python
import csv

idx = {v: i for i, v in enumerate(net.nodes)}
with open(gd.example_path("geometric_expected_distances.csv"), newline="") as f:
    expected = list(csv.DictReader(f))
diff = np.array([abs(D[idx[r["protein_a"]], idx[r["protein_b"]]] - float(r["distance"])) for r in expected])
match = int((diff <= 0.005).sum())
print(f"{match} of {len(expected)} pair distances match the authors' code within 0.005 "
      f"(largest difference {diff.max():.4f})")
assert match == len(expected)
```

```text
11175 of 11175 pair distances match the authors' code within 0.005 (largest difference 0.0020)
```

## 5. The same run from the command line

`geodenoise distances` writes every pair's distance; `geodenoise predict --epsilon E` writes Algorithm 1's predictions; `geodenoise scores` writes Algorithm 2's confidence scores (and, with `--false-positives FILE`, the far-apart edges).

```python
!geodenoise distances "{path}" --dim 2 -o distances.csv
with open("distances.csv", newline="") as f:
    cli = list(csv.DictReader(f))
same = sum(abs(float(r["distance"]) - D[idx[r["protein_a"]], idx[r["protein_b"]]]) < 1e-5 for r in cli)
print(f"{same} of {len(cli)} distances equal the API's")
assert same == len(cli)
```

```text
11175 of 11175 distances equal the API's
```

```python
!geodenoise scores "{path}" --dim 2 --delta 0.1 --min-score 0.9 -o scores.csv
print(open("scores.csv").read().splitlines()[:4])
```

```text
['protein_a,protein_b,distance,posterior,score,is_edge', 'P090,P123,0.090621,0.00742067,1.000000,0', 'P067,P032,0.090959,0.00742064,0.999996,0', 'P067,P070,0.090424,0.00742061,0.999992,0']
```

## 6. Your own data

- **Input**: an edge list with two columns of protein names, tab- or comma-separated; a header line such as `protein_a protein_b` is skipped. Self-interactions and repeated pairs are dropped, and only the largest connected component is used (pass `--all-components` to keep the others).
- **Options**: `--dim` (the paper uses 5 for the human network and 2 to 7 on yeast), `--delta` (0.4 in the paper), `--prior` P(edge) (0.001), `--learn-set-size` (18,000 in the paper), `--seed`. Distances are on the authors' scale: every axis is rescaled to [0, 1].
- **Output** of `scores`: `protein_a`, `protein_b`, `distance`, `posterior` (P(edge | distance)), `score` (the posterior divided by the largest posterior, so the best pair scores 1) and `is_edge` (1 if the pair is already an interaction). The paper calls pairs with score at least 0.975 high-confidence.

## 7. The full reproduction

The paper's figures and tables are reproduced with this package on the yeast and human networks in [`PMC2711306/figure-reproduction`](https://github.com/jeonglab-bcm/fossil/tree/main/PMC2711306/figure-reproduction). The results page is at https://jeonglab-bcm.github.io/fossil/PMC2711306/.

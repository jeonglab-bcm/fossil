<!-- Generated from tutorial.ipynb by check_package.py --write. Do not edit by hand. -->

# condloc tutorial

`condloc` maps where a protein is likely to be under a condition. It scores 13 subcellular locations from the protein's own features, its interaction neighbours and how coherently those neighbours are expressed in the condition (CoLP). Proteins whose most possible location changes between conditions are candidate mislocations.

Lee K, Byun K, Hong W, et al. Proteome-wide discovery of mislocated proteins in cancer. *Genome Research* 23(8):1283–1294 (2013). doi:10.1101/gr.155499.113

## 1. Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC3730102/package"
```

```python
import condloc as cl

print("condloc", cl.__version__)
```

```text
condloc 0.1.0
```

## 2. The example input

Eight proteins, nine interactions, three known locations and the expression of the eight genes over eight samples. The data are synthetic (see `data/README.md`).

```python
genes, x = cl.read_expression(cl.example_path("example_expression.tsv"))
links = cl.read_links(cl.example_path("example_network.tsv"))
print(len(genes), "proteins,", x.shape[1], "samples,", len(links), "links")
print(cl.example_path("example_locations.tsv").read_text())
```

```text
8 proteins, 8 samples, 9 links
protein	locations
P1	NU
P2	NU
P3	CY
P4
P5	CY,PM
P6	PM
P7
P8	NU
```

## 3. Run the method

The coherence of a link is high when both genes are well expressed and strongly correlated:

Φ(a, b) = −log2 Ψ[min(med a, med b) / MEDIAN × r(a, b)],

with Ψ the share of links scoring at least as high. CoLP multiplies each neighbour's weight w_ki = 1 / (Ψ_ki + ρ) by these scores, so the neighbours that are coherently expressed in a condition count most.

```python
rows = cl.link_coherence(cl.example_path("example_expression.tsv"), cl.example_path("example_network.tsv"))
for a, b, phi in rows:
    print(f"{a}-{b}  {phi:.3f}")
```

```text
P1-P2  1.170
P1-P4  2.170
P2-P3  0.848
P3-P5  0.170
P4-P5  0.585
P4-P8  0.363
P5-P6  -0.000
P6-P7  1.585
P2-P8  3.170
```

```python
import numpy as np

names = genes
idx = {p: i for i, p in enumerate(names)}
locs = dict(l.split("\t") for l in cl.example_path("example_locations.tsv").read_text().splitlines()[1:])
loc_names = ["CY", "NU", "PM"]
masks = cl.location_masks([[loc_names.index(v) for v in locs[p].split(",") if v] for p in names], 3)
adj = cl.adjacency(len(names), np.array([(idx[a], idx[b]) for a, b in links]))
w2 = cl.neighbourhood_weights(adj, masks, 2, rho=2.0).toarray()
print("weights of P1's distance-2 neighbourhood:", {names[k]: round(float(w2[0, k]), 3) for k in np.flatnonzero(w2[0])})
```

```text
weights of P1's distance-2 neighbourhood: {'P1': 0.5, 'P2': 0.333, 'P3': 0.25, 'P4': 0.5, 'P5': 0.25, 'P8': 0.333}
```

## 4. Compare with the expected output

The expected values were computed from the published formulas in plain Python, without this package.

```python
import math

exp = [l.split("\t") for l in cl.example_path("expected_coherence.tsv").read_text().splitlines()[1:]]
ok = sum(math.isclose(phi, float(e[2]), rel_tol=1e-9, abs_tol=1e-12) for (_, _, phi), e in zip(rows, exp))
print(f"{ok} of {len(exp)} coherence scores match the expected output")
assert ok == len(exp)

expw = [l.split("\t") for l in cl.example_path("expected_weights.tsv").read_text().splitlines()[1:]]
wmat = {d: cl.neighbourhood_weights(adj, masks, d, rho=2.0).toarray() for d in (1, 2)}
okw = sum(math.isclose(wmat[int(d)][idx[i], idx[k]], float(v), rel_tol=1e-9) for d, i, k, v in expw)
print(f"{okw} of {len(expw)} neighbour weights match the expected output")
assert okw == len(expw)
```

```text
9 of 9 coherence scores match the expected output
74 of 74 neighbour weights match the expected output
```

## 5. From the command line

```python
ex, net = cl.example_path("example_expression.tsv"), cl.example_path("example_network.tsv")
!condloc "{ex}" "{net}"
```

```text
protein_a	protein_b	coherence
P1	P2	1.16992500144
P1	P4	2.16992500144
P2	P3	0.847996906555
P3	P5	0.169925001442
P4	P5	0.584962500721
P4	P8	0.362570079385
P5	P6	0
P6	P7	1.58496250072
P2	P8	3.16992500144
```

## 6. Your own data

- **Expression:** one TSV per study, first column the protein (the same identifiers as the network), then one column per sample, on a log scale. Quantile-normalise each study (`cl.quantile_normalize`) and impute genes with under 30% missing values (`cl.knn_impute`).
- **Network:** a TSV of interacting pairs with a header line.
- **Whole maps:** build a `cl.Proteome` from accessions, sequences, InterPro motifs, GO function and process terms, known locations (GO cellular component) and links; choose the feature sets of each location with `cl.train` on the gold standard; then, for each condition, weight the links with `cl.condition_link_weights`, rebuild the network feature sets with `cl.network_sets(..., link_weight=...)`, and turn the DC-kNN confidences into degrees of possibility with `cl.possibility_map`.
- **Outputs:** `coherence` is −log2 of an upper-tail share, so 0 is the least coherent link and log2(number of links) the most. A degree of possibility runs from 0 to 1 for each protein, location and condition.

## 7. The reproduction

The pipeline that rebuilds the paper's figures with this package, on the paper's data, is at [PMC3730102](https://github.com/jeonglab-bcm/fossil/tree/main/PMC3730102) and its results page at <https://jeonglab-bcm.github.io/fossil/PMC3730102/>.

# gecon

GeCON builds a signed gene co-expression network from local expression patterns: each step between two
neighbouring conditions becomes an angle and a direction, and two genes are connected when enough of their
steps match (same direction, similar angle) or mirror each other (opposite direction). Edges carry a sign:
+1 for genes that move together, −1 for genes that move in opposite directions.

The method comes from:

> Roy S, Bhattacharyya DK, Kalita JK. Reconstruction of gene co-expression network from microarray data
> using local expression patterns. *BMC Bioinformatics* 15(Suppl 7):S10 (2014).
> doi:[10.1186/1471-2105-15-S7-S10](https://doi.org/10.1186/1471-2105-15-S7-S10)

The authors' Java executable is lost. This package reimplements the method from the paper's Eqs. (4) to
(11), so it was checked against the paper (its Figure 7 example and its Figure 2 pair), not against the
original program. Python was chosen by the default rule: the method needs no R or Bioconductor package.

Its reproduction (pipeline, results and comparison with the published figures) is in
[`PMC4110735/`](https://github.com/jeonglab-bcm/fossil/tree/main/PMC4110735).

## Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC4110735/package"
```

Python 3.10 or later, with NumPy.

## Use

```python
import gecon

genes, conditions, X = gecon.read_matrix(gecon.example_path("gds3702_mrps26_pfn2.tsv"))
A, sup = gecon.gecon(X, theta=0.5, tau=20)   # signed adjacency matrix and the supports
print(gecon.edge_list(A, sup, genes))
```

From the command line:

```bash
gecon "$(gecon --example-path)" -o edges.csv
```

The [tutorial](tutorial/TUTORIAL.md) installs the package, runs it on the bundled examples, compares the
result with the paper's own values, and explains the input and output formats.

## Settings the paper does not state

| Setting | Default here | Paper |
| --- | --- | --- |
| θ | 0.5 | "above 50% of the total number of edges" |
| τ | 20 degrees | "15 to 25" |
| Inverted-pattern test, Eq. (7) | \|a_i + a_j − 180\| < τ, as the text describes it | printed as \|180 − a_i + a_j\| < τ (`neg_rule="printed"`) |
| Equal neighbours, Eq. (4) | regulation +1 | not covered |
| Sign when neither support exceeds θ | the larger support | not stated |
| Standardising genes | off (`--standardize` to switch it on) | "insensitive to normalization" |

On positive data with small relative changes, every angle of Eq. (5) sits near 45 or 135 degrees and
almost every pair is connected; standardise first. The reproduction measured this.

## Licence

MIT. See [LICENSE](LICENSE). The example data are described in [data/README.md](src/gecon/data/README.md).

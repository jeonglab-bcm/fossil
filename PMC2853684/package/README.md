# diseasenet

Network-based scores for associating genes with diseases, and their leave-one-out evaluation, as
compared by:

> Navlakha S, Kingsford C. The power of protein interaction networks for associating genes with
> diseases. *Bioinformatics* 26(8):1057-1063 (2010). [doi:10.1093/bioinformatics/btq076](https://doi.org/10.1093/bioinformatics/btq076)

The authors released their predictions but not their code. This package implements the methods
from the paper and its supplement: Neighborhood, Oti, random walk with restart (RW, Köhler et al.
2008), network propagation (Prop, Vanunu and Sharan 2008) and cluster-based scores (for example
from MCL), each leave-one-out, with the paper's precision and recall over linkage-interval
candidates and its two measures of disease homophily. On the paper's HPRD and OPHID networks it
gives the authors' published scores on every one of 1,935,350 candidate pairs (Neighborhood, Oti,
RW, Prop; MCL with the `mcl` program). The reproduction is in
[`PMC2853684/`](https://github.com/jeonglab-bcm/fossil/tree/main/PMC2853684) of the fossil repository.

Graph summarization (GS1-3, GS-All) and VI-Cut are not included: the graph summarization code is
lost, and VI-Cut needs its merge tree.

**Language:** Python. The paper names no language and its code is lost; the default rule (R only
when the method relies on R packages) gives Python.

## Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC2853684/package"
```

Python 3.10 or later, with numpy and scipy.

## Use

```python
import diseasenet as dn

net = dn.read_network(dn.example_path("network.tsv"))
cands = dn.read_candidates(dn.example_path("candidates.csv"))
ann = cands.annotations()                       # disease -> known genes
rw = dn.rw_scores(net, ann, cands)              # leave-one-out RW score of each pair
print(dn.precision_recall(rw > 0.01, cands.known))   # precision %, recall %, predictions
```

From the command line:

```bash
diseasenet $(diseasenet --example-path) -o scores.csv
```

The [tutorial](tutorial/TUTORIAL.md) runs the methods on the bundled example and compares them
with the expected output.

## Input and output

- Network: one interaction per line, two protein names separated by white space. Unweighted;
  `self_loops=True` (`--self-loops`) adds a self-interaction to every protein (the paper's OPHID
  scores were computed that way).
- Candidates: CSV with `gene`, `disease`, `known` (1 when the gene is known to cause the disease),
  one row per gene in a linkage interval of the disease. The DiseaseNet prediction-file layout of
  the paper's web site is read too.
- Scores: one per candidate pair, leave-one-out (a gene's own disease associations are ignored when
  it is scored). A pair is predicted when its score is greater than the threshold θ.

## Licence

MIT. See [LICENSE](LICENSE). The example data are described in [data/README.md](src/diseasenet/data/README.md).

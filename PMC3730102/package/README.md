# condloc

Conditional protein location maps (CoLP). For every protein, `condloc` scores how possible each of 13
subcellular locations is under a condition, from the protein's sequence, motifs and GO terms, its interaction
neighbours, and how coherently the neighbours are expressed in that condition. Proteins whose most possible
location changes between conditions are candidate mislocations.

The method comes from:

> Lee K, Byun K, Hong W, Chuang HY, Pack CG, Bayarsaikhan E, et al. Proteome-wide discovery of mislocated
> proteins in cancer. *Genome Research* 23(8):1283–1294 (2013). doi:10.1101/gr.155499.113

and the DC-kNN classifier it reuses:

> Lee K, Chuang HY, Beyer A, Sung MK, Huh WK, Lee B, Ideker T. Protein networks markedly improve prediction
> of subcellular localization in multiple eukaryotic species. *Nucleic Acids Research* 36:e136 (2008).
> doi:10.1093/nar/gkn619

The authors' CoLP web server is gone and its code was never released. This package implements the method from
the text and equations of the two papers. Its reproduction of the 2013 paper (pipeline, results and comparison
with the published figures) is at
[`PMC3730102`](https://github.com/jeonglab-bcm/fossil/tree/main/PMC3730102).

**Why Python:** there is no authors' code, and the method relies on no R or Bioconductor package, so the
default rule picks Python.

## Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC3730102/package"
```

Python 3.10 or later, with NumPy and SciPy.

## Use

```python
import condloc as cl

# expression coherence of interacting pairs in one study
rows = cl.link_coherence(cl.example_path("example_expression.tsv"), cl.example_path("example_network.tsv"))

# the whole method on your own proteome
p = cl.Proteome.build(accessions, sequences, motifs, go_terms, known_locations, links)
sets = {**p.s, **cl.network_sets(p)}                          # S, N1, N2, L1 and L2 feature sets
counts = cl.knn_counts(sets, p, query=gold, train=gold)       # k = 5 nearest gold-standard proteins
model, _ = cl.train(counts, p.labels[gold], range(len(gold)), list(sets))   # forward selection per location
w = cl.condition_link_weights(p, [(genes, expression)])       # one condition's coherence on each link
cond_sets = cl.network_sets(p, link_weight=cl.weighted_adjacency(p, w))
```

From the command line, the coherence of each link in one study:

```bash
condloc expression.tsv links.tsv -o coherence.tsv
```

The [tutorial](tutorial/TUTORIAL.md) runs the example step by step and checks it against the expected output.

## What is from the papers and what is ours

From the papers: the 29 feature sets, w_ki = 1 / (Psi_ki + rho) with rho = 2, the pair-location conditional
probabilities, the DC-kNN confidence with k = 5 and forward selection on the AUC, the coherence score and the
degree of possibility. Ours, because the papers do not say: Psi in the coherence is the upper-tail share of
links; condition weights multiply the path weights and are scaled to a median of 1; studies of one condition
are averaged with weights equal to their sample counts; Euclidean distance; leave-two-out as two random halves
of the gold standard.

## Licence

MIT. The example data are synthetic.

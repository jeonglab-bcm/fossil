# prospectr-adtree

PROSPECTR ranks candidate disease genes by sequence features with an alternating decision tree.
This package holds the paper's published 15-rule tree (Figure 2) as a gene scorer, and a port of
Weka 3.4's ADTree learner, the one PROSPECTR was built with, that builds the same trees as Weka
3.4.3 (checked to the last bit on PROSPECTR's archived data).

> Adie EA, Adams RR, Evans KL, Porteous DJ, Pickard BS. Speeding disease gene discovery by sequence
> based candidate prioritization. *BMC Bioinformatics* 6:55 (2005). doi:10.1186/1471-2105-6-55

## Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC1274252/package"
```

Python 3.10 or later; no other dependencies.

## Quick start

```python
import prospectr_adtree as pa

raw = pa.score({"gene_length": 50000, "exons": 40, "signal_peptide": 1, "mouse_identity": 90})
print(raw, pa.normalise(raw))          # negative raw score: looks like a disease gene

data = pa.read_arff(pa.example_path("example_train.arff"))
tree = pa.ADTree(15, "zpure").fit(data)   # Weka: ADTree -B 15 -E -1
print(tree.to_weka_string())
```

```bash
prospectr-adtree score genes.csv -o scores.csv
prospectr-adtree train data.arff --tree tree.txt -o scores.csv
prospectr-adtree train data.arff --cv 10 -o cv_scores.csv
```

Tutorial: [tutorial/TUTORIAL.md](tutorial/TUTORIAL.md).

## What is in it

| Function | Does |
| --- | --- |
| `published_tree()`, `score()`, `normalise()` | the Figure 2 tree; a gene's raw score; 1/(1 + e^raw) |
| `contributions()`, `average_contributions()` | each feature's share of a score (Table 4's measure) |
| `features_from_prospectr_arff()` | maps a row of PROSPECTR's archived ARFF files onto the tree's features |
| `ADTree` | Weka 3.4's alternating decision tree (all four search modes, merging, Weka's printout) |
| `cross_validate()` | Weka's stratified k-fold cross-validation with the same shuffles (java.util.Random) |
| `evaluate()`, `roc_curve()`, `roc_area()` | accuracy, precision, recall, kappa, threshold curve and AUC as Weka 3.4.3 reports them |
| `read_arff()` | a reader for dense ARFF files |

## Language and licence

Python: the authors used Weka (Java) and a Perl scorer that is lost; no R or Bioconductor package
is involved, so the default rule gives Python. The ADTree learner is a port of Weka 3.4.3's
`weka.classifiers.trees.ADTree` (GPL-2.0-or-later), so this package is GPL-2.0-or-later. It ships
no Weka code. The published tree's values are facts from the paper (CC BY 2.0).

## Checked against

- Weka 3.4.3 (the original runtime, free Java): identical tree text, scores and cross-validation on
  PROSPECTR's archived training and test sets (64 features, and Table 1's features), and on the
  bundled example.
- The paper: the published tree's scores add up by hand (bundled example), and on the archived sets
  it gives Table 3's accuracy within a few points.

Reproduction: [PMC1274252](https://github.com/jeonglab-bcm/fossil/tree/main/PMC1274252), results
page <https://jeonglab-bcm.github.io/fossil/PMC1274252/>.

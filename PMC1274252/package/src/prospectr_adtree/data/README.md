# Bundled data

| File | What it is | Where it comes from |
| --- | --- | --- |
| `prospectr_fig2.json` | PROSPECTR's 15-rule alternating decision tree | Read node by node from Figure 2 of Adie et al. (2005), BMC Bioinformatics 6:55 (CC BY 2.0). Rule 15 is printed "Gene length >- 896bp"; it is read as >=. |
| `example_train.arff` | 200 synthetic genes, five features (gene length, exons, mouse identity, signal peptide, 3' UTR length; some missing), two classes | `scripts/make_example_data.py` (fixed seed). Not real genes. Licence: this package's (GPL-2.0-or-later). |
| `example_train_weka_tree.txt` | The tree Weka 3.4.3 builds on it (`ADTree -B 15 -E -1`) | Weka 3.4.3 itself, through `PMC1274252/figure-reproduction/pipeline/WekaRun.java`: `java -cp weka.jar:. WekaRun out 15 -1 all example_train.arff` |
| `example_train_weka_scores.tsv` | Weka's score of each row with that tree (`index`, `fold` = -1, `class`, `score`) | Same run |
| `example_train_weka_cv.tsv` | Weka's 10-fold cross-validated score of each row (seed 1) and its fold | Same run |
| `example_genes.csv` | Three made-up genes with Figure 2's features (empty = unknown) | Written by hand to reach different branches |
| `example_genes_expected.csv` | Their scores and the rules each one fires | Added up by hand from Figure 2 (the `rules_fired` column), not computed by this package; normalised with 1/(1 + e^raw) |

The expected outputs come from Weka 3.4.3 and from hand arithmetic on the published figure, so the
tests check the package against something it did not produce. Scores agree with Weka to 1e-12
(they agree to the last bit on PROSPECTR's own data) and with the hand sums to 1e-9.

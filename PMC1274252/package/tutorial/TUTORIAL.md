<!-- Generated from tutorial.ipynb by check_package.py --write. Do not edit by hand. -->

# prospectr-adtree tutorial

PROSPECTR ranks candidate disease genes by sequence features: gene and protein length, exon number,
3' UTR length, GC content, signal peptides and conservation in mouse, rat and worm. It adds up the
values of an alternating decision tree, built with Weka's ADTree; a negative score means the gene
looks more like a known disease gene. This package holds the paper's published tree (Figure 2) as a
scorer, and a port of Weka 3.4's ADTree learner that builds the same trees as Weka 3.4.3.

> Adie EA, Adams RR, Evans KL, Porteous DJ, Pickard BS. Speeding disease gene discovery by sequence
> based candidate prioritization. *BMC Bioinformatics* 6:55 (2005). doi:10.1186/1471-2105-6-55

## 1. Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC1274252/package"
```

It needs Python 3.10 or later and nothing else. This notebook was run in a fresh environment with
the package installed from its wheel.

```python
import csv
import prospectr_adtree as pa

print("prospectr-adtree", pa.__version__)
```

```text
prospectr-adtree 0.1.0
```

## 2. The example input

Two bundled examples. `example_genes.csv` has three made-up genes with the features of the
published tree (an empty cell is unknown). `example_train.arff` has 200 synthetic genes in Weka's
ARFF format, with five features and a disease or normal label, for training a tree.

```python
genes_path = pa.example_path("example_genes.csv")
print(genes_path.read_text())

train = pa.read_arff(pa.example_path("example_train.arff"))
print(len(train.rows), "genes;", [a.name for a in train.attributes])
print(train.labels().count("disease"), "disease,", train.labels().count("normal"), "normal")
```

```text
gene,gene_length,cds_length,utr3_length,exons,gc,signal_peptide,paralog_identity,mouse_identity,rat_identity,worm_identity,mouse_ka
long_conserved_secreted,50000,2000,1000,40,45,1,,90,85,0,0.05
short_no_homolog,700,,,3,,0,,0,,,
partly_unknown,20000,500,300,10,,,80,50,,,

200 genes; ['gene_length', 'exons', 'mouse_identity', 'sigpep', 'len_3utr', 'phenotype']
120 disease, 80 normal
```

## 3. Run the method

**Score genes with the published tree.** `pa.score` follows every rule whose feature is known and
adds up the values; `pa.normalise` maps the raw score to 1/(1 + e^raw), so higher means more likely
a disease gene. `pa.contributions` gives each feature's share of the score (Table 4's measure).

```python
with open(genes_path, newline="") as f:
    genes = list(csv.DictReader(f))

ours = {}
for g in genes:
    feats = {k: float(v) for k, v in g.items() if k != "gene" and v != ""}
    raw = pa.score(feats)
    ours[g["gene"]] = raw
    top = sorted(pa.contributions(feats).items(), key=lambda kv: -kv[1])[:3]
    print(f"{g['gene']:<26} raw {raw:+.3f}  normalised {pa.normalise(raw):.4f}  top features",
          ", ".join(f"{k} {v:.0%}" for k, v in top))
```

```text
long_conserved_secreted    raw -1.126  normalised 0.7551  top features exons 41%, signal_peptide 22%, mouse_identity 15%
short_no_homolog           raw +1.168  normalised 0.2372  top features gene_length 58%, mouse_identity 36%, signal_peptide 5%
partly_unknown             raw -0.511  normalised 0.6250  top features paralog_identity 43%, cds_length 20%, mouse_identity 20%
```

**Train a tree.** `pa.ADTree(15, "zpure")` is Weka's `ADTree -B 15 -E -1`, the command on
PROSPECTR's download page. `to_weka_string()` prints the tree as Weka does; `pa.evaluate` gives the
statistics Weka reports, and `pa.cross_validate` reruns Weka's 10-fold cross-validation.

```python
model = pa.ADTree(15, "zpure").fit(train)
print(model.to_weka_string())
classes = [int(r[train.class_index]) for r in train.rows]
fit = pa.evaluate(classes, model.scores(train))
cv = sorted(pa.cross_validate(train, 15, "zpure", folds=10, seed=1), key=lambda r: r["index"])
cv_stats = pa.evaluate(classes, [r["score"] for r in cv])
for name, ev in (("training set", fit), ("10-fold CV", cv_stats)):
    print(f"{name:<13} accuracy {ev['pct_correct']:.1f}%  recall {ev['recall_disease']:.2f}  "
          f"precision {ev['precision_disease']:.2f}  AUC {ev['auc_disease']:.3f}  kappa {ev['kappa']:.3f}")
```

```text
Alternating decision tree:

: -0.201
|  (1)gene_length < 13494: 0.607
|  |  (4)len_3utr < 205.5: 0.849
|  |  (4)len_3utr >= 205.5: -0.15
|  |  |  (5)mouse_identity < 79.8: 0.2
|  |  |  (5)mouse_identity >= 79.8: -1.154
|  (1)gene_length >= 13494: -0.482
|  |  (2)mouse_identity < 40.15: 0.887
|  |  (2)mouse_identity >= 40.15: -0.491
|  |  (3)len_3utr < 838.5: 0.278
|  |  (3)len_3utr >= 838.5: -1.295
|  (6)gene_length < 4499.5: 1.03
|  (6)gene_length >= 4499.5: -0.153
|  |  (10)exons < 6.5: 0.211
|  |  (10)exons >= 6.5: -0.309
|  |  (12)len_3utr < 838.5: 0.116
|  |  |  (13)gene_length < 15782.5: 0.317
|  |  |  (13)gene_length >= 15782.5: -0.266
|  |  |  (14)len_3utr < 387: -0.194
|  |  |  (14)len_3utr >= 387: 0.311
|  |  (12)len_3utr >= 838.5: -0.503
|  (7)len_3utr < 74: 0.766
|  (7)len_3utr >= 74: -0.033
|  (8)mouse_identity < 84: 0.105
|  (8)mouse_identity >= 84: -0.669
|  (9)sigpep = 0: 0.141
|  (9)sigpep = 1: -0.456
|  (11)gene_length < 103948: 0.097
|  (11)gene_length >= 103948: -0.869
|  (15)len_3utr < 114: 0.496
|  (15)len_3utr >= 114: -0.065
Legend: -ve = disease, +ve = normal
Tree size (total number of nodes): 46
Leaves (number of predictor nodes): 31
training set  accuracy 89.0%  recall 0.90  precision 0.92  AUC 0.962  kappa 0.772
10-fold CV    accuracy 74.5%  recall 0.78  precision 0.79  AUC 0.848  kappa 0.470
```

## 4. Compare with the expected output

The expected scores of the three genes were added up by hand from Figure 2 (the `rules_fired`
column). The expected tree and scores of the training example come from Weka 3.4.3 itself. Neither
comes from this package.

```python
import math

with open(pa.example_path("example_genes_expected.csv"), newline="") as f:
    expected = {r["gene"]: float(r["raw_score"]) for r in csv.DictReader(f)}
hits = sum(math.isclose(ours[g], expected[g], abs_tol=1e-9) for g in expected)
print(f"{hits} of {len(expected)} genes match the hand-computed scores")
assert hits == len(expected)

weka_tree = pa.example_path("example_train_weka_tree.txt").read_text()
same_tree = model.to_weka_string().strip() == weka_tree[weka_tree.index("Alternating"):].strip()
with open(pa.example_path("example_train_weka_scores.tsv"), newline="") as f:
    weka = [float(r["score"]) for r in csv.DictReader(f, delimiter="\t")]
score_hits = sum(math.isclose(a, b, abs_tol=1e-12) for a, b in zip(model.scores(train), weka))
with open(pa.example_path("example_train_weka_cv.tsv"), newline="") as f:
    weka_cv = {int(r["index"]): float(r["score"]) for r in csv.DictReader(f, delimiter="\t")}
cv_hits = sum(math.isclose(r["score"], weka_cv[r["index"]], abs_tol=1e-12) for r in cv)
print("tree identical to Weka 3.4.3's:", same_tree)
print(f"{score_hits} of {len(weka)} training scores and {cv_hits} of {len(weka_cv)} cross-validated scores match Weka")
assert same_tree and score_hits == len(weka) and cv_hits == len(weka_cv)
```

```text
3 of 3 genes match the hand-computed scores
tree identical to Weka 3.4.3's: True
200 of 200 training scores and 200 of 200 cross-validated scores match Weka
```

## 5. From the command line

`prospectr-adtree score` scores a CSV of genes with the published tree; `prospectr-adtree train`
builds a tree on an ARFF file and writes each row's score (`--cv 10` for cross-validated scores,
`--tree FILE` for the tree).

```python
!prospectr-adtree score "{genes_path}"
```

```text
gene,raw_score,normalised_score
long_conserved_secreted,-1.126,0.755100
short_no_homolog,1.168,0.237217
partly_unknown,-0.511,0.625041
```

## 6. Your own data

- **Scoring with PROSPECTR:** a CSV with a `gene` column and any of `gene_length`, `cds_length`,
  `utr3_length` (bp), `exons`, `gc` (%), `signal_peptide` (1 or 0), `paralog_identity`,
  `mouse_identity`, `rat_identity`, `worm_identity` (% protein identity; 0 when there is no homolog,
  empty when there is no paralog) and `mouse_ka`. An empty cell is unknown: its rules are skipped.
  Output: `raw_score` (negative = more like a disease gene) and `normalised_score` (0 to 1). To rank
  a locus, sort its genes by raw score, lowest first.
- **Training a tree:** an ARFF file whose last attribute is the two-valued class; the first class
  value gets negative scores. `--iterations` (Weka -B) sets the number of rules; `--search` sets
  Weka's -E.
- The published tree was trained on features from Ensembl 22 (2004) and HomoloGene; features from
  later builds give somewhat different scores (the reproduction measures how much).

## 7. The reproduction

The paper's tables and figures, rerun on PROSPECTR's archived training and test sets:
[results page](https://jeonglab-bcm.github.io/fossil/PMC1274252/) and
[pipeline](https://github.com/jeonglab-bcm/fossil/tree/main/PMC1274252/figure-reproduction).

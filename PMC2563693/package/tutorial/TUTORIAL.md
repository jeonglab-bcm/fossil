<!-- Generated from tutorial.ipynb by check_package.py --write. Do not edit by hand. -->

# pacorg tutorial

`pacorg` infers the activity of a pathway in each sample from its **condition-responsive genes (CORGs)**: the subset of the pathway's genes whose combined expression best separates two classes of samples. Each gene is z-scored over all samples; a gene set's activity is the sum of its members' z-scores over the square root of their number; the CORGs are found by a greedy search that adds genes in order of their own t statistic while the t statistic of the combined activity keeps rising. Pathway activities can then be used as features of a classifier.

The method is from:

> Lee E, Chuang HY, Kim JW, Ideker T, Lee D. Inferring pathway activity toward precise disease classification. *PLoS Computational Biology* 4(11):e1000217 (2008). doi:10.1371/journal.pcbi.1000217

The authors' software is lost; `pacorg` was written from the paper's Methods. On the paper's lung data it gives every CORG list of the paper's Table 1 (section 7).

## 1. Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC2563693/package"
```

It needs Python 3.10 or later, NumPy and SciPy. This notebook was run in a fresh environment with the package installed from its wheel. Check the version:

```python
import pacorg as pc

print("pacorg", pc.__version__)
```

```text
pacorg 0.1.0
```

## 2. The example input

The package ships a small synthetic example (see `data/README.md`): 120 genes in 40 samples of two classes, `case` and `control`, and four gene sets. Shifts were planted in a few genes of three sets; the fourth set has none. The inputs are in the GSEA formats: GCT (expression), CLS (labels) and GMT (gene sets).

```python
genes, samples, X = pc.read_gct(pc.example_path("example.gct"))
labels = pc.read_cls(pc.example_path("example.cls"))
sets = pc.read_gmt(pc.example_path("example.gmt"))
print(X.shape[0], "genes x", X.shape[1], "samples; classes:", sorted(set(labels)))
print("first gene:", genes[0], X[0, :5])
for name, members in sets.items():
    print(f"{name:<10} {len(members):>3} genes: {' '.join(members[:6])} ...")
```

```text
120 genes x 40 samples; classes: ['case', 'control']
first gene: G001 [8.643 8.346 9.462 8.706 8.749]
SET_UP      12 genes: G001 G002 G003 G004 G005 G006 ...
SET_DOWN    10 genes: G021 G022 G023 G024 G025 G026 ...
SET_MIXED   15 genes: G041 G042 G043 G044 G045 G046 ...
SET_NULL     8 genes: G101 G102 G103 G104 G105 G106 ...
```

## 3. Run the method

`infer_pathways` z-scores the genes, finds the CORGs of every gene set and returns, for each set, its CORGs, Tian et al.'s score (sum of member t over the square root of the set size, used to pre-select pathways) and S(G), the t statistic of the CORG activity. The two classes sort as `case`, `control`, so every t statistic is `control` minus `case`.

```python
results = pc.infer_pathways(X, genes, labels, sets)
print(f"{'set':<10}{'CORGs':<30}{'Tian':>8}{'S(G)':>9}")
for r in results:
    print(f"{r.name:<10}{' '.join(r.corgs):<30}{r.tian:>8.3f}{r.score:>9.3f}")
```

```text
set       CORGs                             Tian     S(G)
SET_UP    G001 G002                       -3.187   -9.099
SET_DOWN  G021 G022 G028                   2.017    4.725
SET_MIXED G042 G051 G045 G050 G047         1.778    4.307
SET_NULL  G106 G105 G102                  -0.560   -2.359
```

The planted genes come back first in each set (G001 and G002 in SET_UP; G021 and G022 in SET_DOWN). In SET_MIXED the search follows the direction of the members' mean t, so it takes the down-shifted G042 and then genes that lean the same way. Even SET_NULL gets CORGs: the search always returns at least one gene, which is why the paper pre-selects pathways and validates the classifier on held-out samples.

Each result also carries the activity vector:

```python
up = results[0]
print(up.name, "activity, first five samples:", up.activity[:5].round(3))
```

```text
SET_UP activity, first five samples: [1.289 0.006 2.166 0.965 0.549]
```

## 4. Compare with the expected output

The expected output was computed by `scripts/make_example_data.py` with `scipy.stats.ttest_ind` and loops written for it, not with this package.

```python
import math

expected = pc.read_results(pc.example_path("example_expected.csv"))
matches = sum(
    r.name == e["pathway"] and r.corgs == e["corgs"]
    and math.isclose(r.tian, e["tian"], rel_tol=1e-9) and math.isclose(r.score, e["score"], rel_tol=1e-9)
    for r, e in zip(results, expected)
)
print(f"{matches} of {len(expected)} gene sets match the expected output")
assert matches == len(expected)
```

```text
4 of 4 gene sets match the expected output
```

## 5. From the command line

`pacorg EXPRESSION.gct LABELS.cls GENESETS.gmt` writes the same table as CSV (`-o` for a file, `--top N` to keep the N sets with the largest |Tian score|). `--example` runs it on the bundled files.

```python
!pacorg --example
```

```text
pathway,members,measured,n_corgs,corgs,tian,score
SET_UP,12,12,2,G001 G002,-3.187181405987856,-9.098798785141295
SET_DOWN,10,10,3,G021 G022 G028,2.016884844801034,4.724707835448399
SET_MIXED,15,15,5,G042 G051 G045 G050 G047,1.7779511980331943,4.307039373055357
SET_NULL,8,8,3,G106 G105 G102,-0.5602036658223204,-2.3591632044056574
```

## 6. Your own data

- **Expression:** GCT 1.2, genes in rows, samples in columns, no missing values and no constant genes (impute or drop them first). Gene names must match the gene sets'.
- **Labels:** CLS with exactly two classes. The second class in sorted order is the case class of the t statistics; only signs depend on it.
- **Gene sets:** GMT. Members not measured in the data are skipped; `members` counts the set as listed and `measured` the members found.
- **Output columns:** `pathway`, `members`, `measured`, `n_corgs`, `corgs` (in the order the search added them), `tian`, `score`.

For classification, `pc.sequential_selection` adds pathway activities to a logistic regression in order of p-value and keeps the count with the best validation AUC, as in the paper.

```bash
pacorg my_expression.gct my_labels.cls c2.symbols.gmt --top 52 -o corgs.csv
```

## 7. The paper's Table 1

The Broad Institute's GSEA site still serves the paper's lung datasets and MSigDB v1.0 C2. Run on the whole Michigan dataset, `pacorg` returns all eight Michigan CORG lists of Table 1 (and on Boston, all ten Boston lists):

```python
import urllib.request
base = "https://data.broadinstitute.org/gsea-msigdb/gsea/dataset_files/"
for f in ("Lung_Michigan_collapsed_symbols.gct", "Lung_Michigan.cls", "c2.symbols.gmt"):
    urllib.request.urlretrieve(base + f, f)
genes, _, X = pc.read_gct("Lung_Michigan_collapsed_symbols.gct")
res = {r.name: r for r in pc.infer_pathways(X, genes, pc.read_cls("Lung_Michigan.cls"), pc.read_gmt("c2.symbols.gmt"))}
print(res["GLYCOL"].corgs)  # ['ENO2', 'PGK1', 'ALDOA'], as in Table 1
```

The full reproduction (all seven datasets, Figs 2 to 4 and S1 to S5, and why some results differ) is in the [fossil repository](https://github.com/jeonglab-bcm/fossil/tree/main/PMC2563693) and on its [results page](https://jeonglab-bcm.github.io/fossil/PMC2563693/).

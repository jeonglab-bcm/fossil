<!-- Generated from tutorial.ipynb by check_package.py --write. Do not edit by hand. -->

# adrfusion tutorial

`adrfusion` predicts adverse drug reactions (ADRs) from binary drug properties. It trains one classifier per ADR (by default an SVM with an RBF kernel, g = 0.008, C = 2) on chemical substructures, biological properties (targets, transporters, enzymes, pathways) and phenotypic properties (indications and the drug's other known ADRs), scores every drug by cross-validation, and summarizes all (drug, ADR) pairs with one global, micro-averaged ROC curve.

It is a rebuild, from the paper's text, of the method of

> Liu M, Wu Y, Chen Y, Sun J, Zhao Z, Chen XW, Matheny ME, Xu H. Large-scale prediction of adverse drug reactions using chemical, biological, and phenotypic properties of drugs. *J Am Med Inform Assoc* 19(e1):e28-e35 (2012). doi:10.1136/amiajnl-2011-000699

The authors' code was never released.

## 1. Install

Install the package from its folder in the fossil repository:

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC3392844/package"
```

It needs Python 3.10 or later, NumPy, SciPy and scikit-learn. This notebook was run in a fresh environment with the package installed from its wheel. Check the version:

```python
import adrfusion as A
import numpy as np

print("adrfusion", A.__version__)
```

```text
adrfusion 0.1.0
```

## 2. Example input

The bundled example is 120 synthetic drugs and 30 ADRs in the file format of the paper's training data: one drug per line, `|`-separated: id, name, compound id, then 0/1 strings for the ADRs, the chemical substructures, targets, transporters, enzymes, pathways and indications, and last the cross-validation fold of the drug for each ADR. `data/README.md` says how it was made.

```python
path = A.example_path()
data = A.read_dataset(path)
print(f"{data.n_drugs} drugs, {data.n_adrs} ADRs, {int(data.Y.sum())} (drug, ADR) pairs with the ADR")
print("features per block:", data.dimensions())
print("first three drugs:")
for line in path.read_text().splitlines()[:3]:
    print(" ", line[:90] + " ...")
```

```text
120 drugs, 30 ADRs, 747 (drug, ADR) pairs with the ADR
features per block: {'chem': 40, 'target': 20, 'transporter': 5, 'enzyme': 6, 'pathway': 10, 'indication': 25, 'ade': 29}
first three drugs:
  D001|drug1||010001001110001000010001011100|1011000010100100000101111010100000000000|100000 ...
  D002|drug2||010000000010001000000000011000|1011000001010000000100001001000000000100|100001 ...
  D003|drug3||000000010000010010000000000000|0100100000100001000010000000000100000000|100001 ...
```

## 3. Run the method

`cross_validated_scores` trains one SVM per ADR and fold, on the folds of the file, and returns the score of every drug for every ADR (drugs x ADRs): the SVM's probability estimate, as LIBSVM gives with `-b 1`. `micro_metrics` merges all pairs into one ROC curve and reads the paper's four numbers off it: AUC; accuracy at the point with the highest accuracy; precision and recall at the point with the highest F1.

Here the feature sets of the paper's Table 2, on the example drugs:

```python
print(f"{'feature set':16s} {'AUC':>7s} {'ACC':>7s} {'Prec.':>7s} {'Recall':>7s}")
for fs in A.FEATURE_SETS:
    S = A.cross_validated_scores(data, fs, "svm", seed=0)
    m = A.micro_metrics(data.Y, S)
    print(f"{fs:16s} {m.auc:7.4f} {m.acc:7.4f} {m.precision:7.4f} {m.recall:7.4f}")
```

```text
feature set          AUC     ACC   Prec.  Recall
chem              0.8180  0.8353  0.5610  0.6707
bio               0.8144  0.8314  0.5094  0.7617
pheno             0.8190  0.8311  0.5633  0.6854
chem+bio          0.8230  0.8367  0.5516  0.7443
chem+pheno        0.8280  0.8339  0.5679  0.7108
chem+bio+pheno    0.8317  0.8408  0.5822  0.7256
```

The paper's clinical validation leaves one drug out, trains on the rest, and asks whether the left-out drug gets each of its known ADRs. `predict_held_out` does that for single ADRs and for a group of ADRs (any of them):

```python
for r in A.predict_held_out(data, drug=0, adrs=[0, 1, 2, [0, 1, 2]], feature_set="chem+bio+pheno"):
    print(f"ADRs {r['adrs']}: known {r['known']}, probability {r['probability']:.3f}, call {r['call']}")
```

```text
ADRs [0]: known 0, probability 0.187, call No
ADRs [1]: known 1, probability 0.601, call Yes
ADRs [2]: known 0, probability 0.182, call No
ADRs [0, 1, 2]: known 1, probability 0.834, call Yes
```

## 4. Compare with the expected output

`example_expected.csv` holds the decision value of every (drug, ADR) pair from the official LIBSVM C library, trained on the raw 0/1 features with the paper's settings (`-t 2 -g 0.008 -c 2`), not from adrfusion. adrfusion builds the same kernel from Hamming distances; the two solvers stop at slightly different points, so compare at 1e-3:

```python
import csv

expected = np.zeros(data.Y.shape)
with open(A.example_path("example_expected.csv"), newline="") as f:
    for r in csv.DictReader(f):
        expected[data.drugs.index(r["drug"]), int(r["adr"][3:])] = float(r["decision"])

S = A.cross_validated_scores(data, "chem+bio+pheno", "svm", scores="decision")
close = np.abs(S - expected) < 1e-3
print(f"{int(close.sum())} of {close.size} pairs match the expected output within 1e-3")
print(f"AUC {A.auc(data.Y, S):.4f} here, {A.auc(data.Y, expected):.4f} from LIBSVM")
assert close.all()
```

```text
3600 of 3600 pairs match the expected output within 1e-3
AUC 0.8342 here, 0.8342 from LIBSVM
```

## 5. Command line

The same run from the shell. `adrfusion` writes every score to a CSV (`drug, adr, label, score`) and the micro-averaged metrics as JSON:

```python
import json, tempfile, pathlib

tmp = pathlib.Path(tempfile.mkdtemp())
!adrfusion "{path}" --feature-set chem+bio+pheno --scores decision -o "{tmp}/scores.csv" --metrics "{tmp}/metrics.json"
m = json.loads((tmp / "metrics.json").read_text())
print({k: round(m[k], 4) for k in ("auc", "acc", "precision", "recall")})
print((tmp / "scores.csv").read_text().splitlines()[:3])
```

```text
{'auc': 0.8342, 'acc': 0.8386, 'precision': 0.5738, 'recall': 0.7443}
['drug,adr,label,score', 'D001,ADR0,0,-0.9577270407329447', 'D002,ADR0,0,-1.220476769737414']
```

## 6. Your own data

- **Input.** A text file in the format above, or build an `ADRData` in Python: `ADRData(drugs=[...], Y=labels, blocks={"chem": ..., "target": ..., ...}, folds=...)`, every matrix 0/1 with one row per drug. Blocks are yours to name; `bio` means target + transporter + enzyme + pathway and `pheno` means indication + the other ADRs. Without folds, make them with `stratified_folds(Y, k=5, seed=0)`.
- **Options.** `feature_set` (blocks joined by `+`), `algorithm` (`svm`, `lr`, `nb`, `knn`, `rf`), `scores` (`probability` or `decision`, SVM only), `class_weight="paper"` (each class weighted by 1 - its share), `n_jobs`.
- **Output.** A drugs x ADRs matrix of scores: higher means more likely to cause the ADR. `micro_metrics` gives AUC, ACC, precision, recall and the two thresholds they were read at; `per_adr_auc` the AUC of each ADR; `ks_larger` the paper's one-sided KS test between two feature sets' per-ADR AUCs; `informative_features` the chi-square counts of Table S1.

## 7. The paper's data

The reproduction runs this package on the paper's own training data (832 drugs, 1,385 ADRs, the authors' folds) and compares every table and figure: results page <https://jeonglab-bcm.github.io/fossil/PMC3392844/>, pipeline `PMC3392844/figure-reproduction/` in <https://github.com/jeonglab-bcm/fossil>.

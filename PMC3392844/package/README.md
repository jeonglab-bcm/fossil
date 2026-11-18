# adrfusion

Adverse drug reaction (ADR) prediction from chemical, biological and phenotypic drug properties: one
classifier per ADR, cross-validated scores for every (drug, ADR) pair, and the micro-averaged AUC,
accuracy, precision and recall of one global ROC curve. A rebuild, from the paper's text, of the
method of

> Liu M, Wu Y, Chen Y, Sun J, Zhao Z, Chen XW, Matheny ME, Xu H. Large-scale prediction of adverse drug
> reactions using chemical, biological, and phenotypic properties of drugs. *J Am Med Inform Assoc*
> 19(e1):e28-e35 (2012). [doi:10.1136/amiajnl-2011-000699](https://doi.org/10.1136/amiajnl-2011-000699)

The authors' code was never released. This package was written from the paper's Methods and checked
against its tables and figures on its own training data (see the reproduction below), not against the
original code.

## Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC3392844/package"
```

Python 3.10 or later; NumPy, SciPy and scikit-learn.

## Quick start

```python
import adrfusion as A

data = A.read_dataset(A.example_path())             # 120 synthetic drugs, 30 ADRs, with folds
S = A.cross_validated_scores(data, "chem+bio+pheno", "svm")
print(A.micro_metrics(data.Y, S))                    # AUC, ACC, precision, recall
```

```bash
adrfusion "$(adrfusion --example-path)" --feature-set chem+bio+pheno -o scores.csv
```

Tutorial: [`tutorial/TUTORIAL.md`](tutorial/TUTORIAL.md).

## What it does

| Step | The paper | adrfusion |
| --- | --- | --- |
| Features | 881 PubChem substructures; 786 targets, 72 transporters, 111 enzymes, 173 KEGG pathways; 869 indications and the 1,384 other ADRs | any 0/1 blocks; `bio` and `pheno` name the paper's groups; the other ADRs of ADR j are the label columns except j |
| Classifier | LIBSVM, RBF kernel, g = 0.008, C = 2 | scikit-learn's libsvm on a precomputed RBF kernel built from per-block Hamming distances (the same kernel) |
| Scores | not stated | Platt probabilities (LIBSVM `-b 1`), the scores that give the paper's AUCs; decision values on request |
| Other algorithms | LIBLINEAR LR (C = 10, epsilon = 1), CLOP naive Bayes, WEKA KNN (k = 55) and random forest (100 trees) | `lr` (LIBLINEAR through scikit-learn), `nb` (Bernoulli; CLOP is lost), `knn` (share of positive neighbours, ties included), `rf` (scikit-learn, log2(M) + 1 features per split) |
| Evaluation | 5-fold CV per ADR; micro-averaged AUC; ACC, precision, recall at the "best cut-off points" | the folds you give; ACC at the maximum-accuracy point, precision and recall at the maximum-F1 point (the two rules that give the paper's Table 2) |
| Clinical validation | train on the other drugs, predict the left-out drug | `predict_held_out` (call Yes when the probability is above 0.5, LIBSVM's label with `-b 1`) |

## Language

Python, by the default rule: the paper's tools (LIBSVM, LIBLINEAR, WEKA) are not R packages, and the
authors' code is lost.

## Reproduction

The paper's tables and figures, rerun with this package on the authors' training data:
<https://github.com/jeonglab-bcm/fossil/tree/main/PMC3392844> (results page:
<https://jeonglab-bcm.github.io/fossil/PMC3392844/>).

## Licence

MIT. The method is from the paper; no code of the authors is included.

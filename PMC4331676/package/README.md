# pssmdt

PSSM distance transformation (PSSM-DT) and SVM-PSSM-DT for telling DNA-binding proteins from other
proteins by their PSI-BLAST profile. PSSM-DT turns a profile of any length into 400 x LG numbers:
for each lag lg = 1..LG and each ordered pair of amino acids (a1, a2), the mean product of the
score of a1 at one position and of a2 lg positions later. An RBF support vector machine on those
numbers is SVM-PSSM-DT.

The method comes from:

> Xu R, Zhou J, Wang H, He Y, Wang X, Liu B. Identifying DNA-binding proteins by combining support
> vector machine and PSSM distance transformation. *BMC Systems Biology* 9(Suppl 1):S10 (2015).
> [doi:10.1186/1752-0509-9-S1-S10](https://doi.org/10.1186/1752-0509-9-S1-S10)

No code was released and the paper's web server is gone, so this package is implemented from the
paper's text (Eqs. 2 to 12). The feature order and the use of raw integer PSSM scores follow the
authors' later toolkit, BioSeq-Analysis2.0 (mode PSSM-DT); the bundled expected output is computed
by a transliteration of that toolkit's loops (`scripts/make_expected.py`), not by this package.

Its reproduction (pipeline, results and comparison with the published tables and figures) is in
[`PMC4331676/`](https://github.com/jeonglab-bcm/fossil/tree/main/PMC4331676).

## Why Python

The paper used LIBSVM and PSI-BLAST, and no R or Bioconductor package. By the default rule of the
fossil reproductions, a method with no R dependencies gets a Python package. scikit-learn's `SVC`
wraps LIBSVM.

## Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC4331676/package"
```

Python 3.10 or later; numpy and scikit-learn. Making the profiles needs NCBI BLAST+ (`psiblast`)
and a protein database, which this package does not install.

## Use

```python
import pssmdt

seq, scores = pssmdt.read_pssm("1AKHA.pssm")      # psiblast -out_ascii_pssm output
x = pssmdt.pssm_dt(scores, lg_max=5)              # 2,000 numbers
names = pssmdt.feature_names(5)                   # "A-R_lg1" is DT(A, R, 1)
```

Training and testing as in the paper: scale every feature to [-1, 1] on the training set, choose
C and gamma by 5-fold cross validation over LIBSVM's grid, then run the jackknife.

```python
X = pssmdt.scale(features)                        # features: n x 2000, labels y in {0, 1}
g = pssmdt.grid_search(X, y)                      # C, gamma, cross-validated accuracy
dec = pssmdt.jackknife(X, y, g.C, g.gamma)        # leave-one-out decision values
print(pssmdt.metrics(y, dec))                     # SN, SP, ACC, MCC, AUC

clf = pssmdt.PSSMDTClassifier(g.C, g.gamma).fit(features, y)
clf.decision_function(new_features)               # > 0: DNA-binding
W = clf.discriminant_weights()                    # Eq. 12, one weight per feature
pssmdt.pair_weights(W, 5)                         # Fig. 2A, 20 x 20
```

From the command line, one CSV row of features per PSSM:

```bash
pssmdt "$(pssmdt --example-path)"/*.pssm -o features.csv
pssmdt my.pssm --encoding AvePscore-400
```

The [tutorial](tutorial/TUTORIAL.md) installs the package, encodes the bundled example profiles,
compares them with the expected output, and explains how to make profiles for your own proteins.

## Input and output

- Input: ASCII PSSMs written by `psiblast -num_iterations 3 -evalue 0.001 -out_ascii_pssm FILE`
  (the paper's settings). Only the 20 log-odds columns are read.
- `pssm_dt` returns 400 x LG values, lag-major; within a lag, the 20 x 20 matrix row by row (first
  amino acid, then second, in the order ARNDCQEGHILKMFPSTWYV). `pssm_sdt` and `pssm_ddt` return
  the 20 x LG same-pair and 380 x LG different-pair parts.
- `encode` also gives the encodings the paper compared with: AvePscore-20, AvePscore-400,
  Pscore-100 and ACC (definitions in `pssmdt/core.py`).

## Licence

MIT. See [LICENSE](LICENSE). The example data are described in
[data/README.md](src/pssmdt/data/README.md).

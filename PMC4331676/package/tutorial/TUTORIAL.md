<!-- Generated from tutorial.ipynb by check_package.py --write. Do not edit by hand. -->

# pssmdt tutorial: PSSM distance transformation

SVM-PSSM-DT tells DNA-binding proteins from other proteins by their PSI-BLAST profile. The profile
(a position-specific scoring matrix, PSSM: one row per residue, one column per amino acid) is
turned into a fixed-length vector by **PSSM distance transformation**: for each lag lg = 1..LG and
each ordered pair of amino acids (a1, a2), the mean of S[j, a1] x S[j + lg, a2] along the sequence.
With LG = 5 that is 2,000 numbers, which go to an RBF support vector machine.

> Xu R, Zhou J, Wang H, He Y, Wang X, Liu B. Identifying DNA-binding proteins by combining support
> vector machine and PSSM distance transformation. *BMC Systems Biology* 9(Suppl 1):S10 (2015).
> doi:10.1186/1752-0509-9-S1-S10

The authors released no code and their web server is gone; this package rebuilds the method from
the paper.

## Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC4331676/package"
```

```python
import csv
import numpy as np
import pssmdt

print(pssmdt.__version__)
```

```text
0.1.0
```

## Example input

The package bundles the PSSMs of eight chains of the paper's benchmark: four DNA-binding (label 1)
and four not (label 0). They were made with `psiblast -num_iterations 3 -evalue 0.001
-out_ascii_pssm` against UniRef100 release 2014_01.

```python
folder = pssmdt.example_path("pssm")
with open(pssmdt.example_path("labels.csv"), newline="") as f:
    labels = {r["id"]: int(r["label"]) for r in csv.DictReader(f)}
files = sorted(folder.glob("*.pssm"))
profiles = {f.stem: pssmdt.read_pssm(f) for f in files}
for name, (seq, scores) in profiles.items():
    print(f"{name}  label {labels[name]}  length {len(seq):3d}  {seq[:30]}...")
```

```text
1AKHA  label 1  length  61  KKEKSPKGKSSISPQARAFLEEVFRRKQSL...
1OAIA  label 0  length  59  PTLSPEQQEMLQAFSTQSGMNLEWSQKCLQ...
1TEJB  label 0  length  64  NSVNPCCDPQTCKPIEGKHCISGPCCENCY...
1UJ0A  label 0  length  62  AGHMARRVRALYDFEAVEDNELTFKHGELI...
1ZRJA  label 1  length  50  GSSGSSGMDVRRLKVNELREELQRRGLDTR...
2BA3B  label 1  length  51  SDSAVRKKSEVRQKTVVRTLRFSPVEDETI...
2L92A  label 1  length  50  MSTVPKYRDPATGKTWSGRGRQPAWLGNDP...
2LRDA  label 0  length  61  AMGKCSVLKKVACAAAIAGAVAACGGIDLP...
```

```python
seq, scores = profiles["1AKHA"]
print("1AKH chain A, first five positions (columns", " ".join(pssmdt.AMINO_ACIDS) + "):")
for j in range(5):
    print(seq[j], " ".join(f"{v:3d}" for v in scores[j]))
```

```text
1AKH chain A, first five positions (columns A R N D C Q E G H I L K M F P S T W Y V):
K  -3   3  -1   4  -5   0   3  -3  -2  -5  -4   4  -3  -5  -3  -2  -2  -5  -4  -4
K  -2   0  -1   4  -5   2   3  -3   2  -4  -4   3  -3  -5  -2  -1  -2  -5  -3  -3
E  -1   2   2   2  -2   1   2   1  -1  -4  -3   1  -3  -3   1   0  -1  -3   1  -3
K   0   3   0  -2  -4   2  -1   2   2  -4  -4   4  -3  -4  -1   0  -2  -4  -3  -3
S   0   3   2  -2  -1   1  -1   0  -1  -4  -2   2  -2  -4   2   2   1  -4  -3  -3
```

## Run the method

`pssm_dt` gives the 2,000 features of one profile. Their names say which pair and lag each one is:
`R-R_lg1` is the mean of S[j, R] x S[j + 1, R].

```python
names = pssmdt.feature_names(5)
X = np.array([pssmdt.pssm_dt(s, 5) for _, s in profiles.values()])
print(X.shape)
x = X[list(profiles).index("1AKHA")]
for k in np.argsort(-x)[:5]:
    print(f"{names[k]:10s} {x[k]:8.3f}")
```

```text
(8, 2000)
W-F_lg1      16.617
W-W_lg2      16.288
W-W_lg5      15.732
C-W_lg4      15.719
W-W_lg1      15.667
```

## Compare with the expected output

`expected_pssm_dt.csv` was not made by this package: a separate script computed it with plain loops
transliterated from the authors' later toolkit (BioSeq-Analysis2.0, mode PSSM-DT). Every value must
agree to a relative tolerance of 1e-12.

```python
with open(pssmdt.example_path("expected_pssm_dt.csv"), newline="") as f:
    rows = list(csv.reader(f))
assert rows[0][1:] == names
expected = {r[0]: np.array([float(v) for v in r[1:]]) for r in rows[1:]}
same = [np.allclose(X[k], expected[name], rtol=1e-12, atol=0) for k, name in enumerate(profiles)]
print(f"{sum(same)} of {len(same)} profiles match the expected output")
assert all(same)
```

```text
8 of 8 profiles match the expected output
```

## Command line

The same features, one CSV row per PSSM:

```python
paths = " ".join(f'"{f}"' for f in files)
!pssmdt {paths} -o features.csv
with open("features.csv", newline="") as f:
    cli = {r[0]: np.array([float(v) for v in r[1:]]) for r in list(csv.reader(f))[1:]}
print(all(np.allclose(cli[n], expected[n], rtol=1e-12) for n in profiles))
```

```text
True
```

## Train and score

`PSSMDTClassifier` scales the features to [-1, 1] on its training set and fits an RBF SVM.
Eight profiles are far too few to judge a classifier; this only shows the calls. With your own
labelled profiles, choose C and gamma with `pssmdt.grid_search` and test with `pssmdt.jackknife`,
as the paper did (C = 2^5 and gamma = 2^-9 below are only an example).

```python
y = np.array([labels[n] for n in profiles])
test = list(profiles).index("1AKHA")
train = [k for k in range(len(y)) if k != test]
clf = pssmdt.PSSMDTClassifier(C=2.0**5, gamma=2.0**-9).fit(X[train], y[train])
print("decision value for 1AKHA:", round(float(clf.decision_function(X[[test]])[0]), 4))
print(pssmdt.metrics(y[train], clf.decision_function(X[train])))
```

```text
decision value for 1AKHA: -0.0886
{'TP': 3, 'TN': 4, 'FP': 0, 'FN': 0, 'SN': 100.0, 'SP': 100.0, 'ACC': 100.0, 'MCC': 1.0, 'AUC': 100.0}
```

## Your own data

1. Make one profile per protein with NCBI BLAST+:
   `psiblast -query protein.fa -db nr -num_iterations 3 -evalue 0.001 -out_ascii_pssm protein.pssm`.
   PSI-BLAST writes no PSSM when it finds no hits; give such a protein the BLOSUM62 row of each
   residue (what PSI-BLAST starts from) or leave it out.
2. Read each with `pssmdt.read_pssm` (it returns the sequence and the L x 20 scores) and encode
   with `pssmdt.pssm_dt(scores, lg_max)`. Sequences must be longer than LG.
3. `pssmdt.encode(scores, sequence, encoding)` also gives the encodings the paper compared with:
   AvePscore-20, AvePscore-400, Pscore-100 and ACC.
4. `pssmdt.scale`, `grid_search`, `jackknife`, `cross_validation` and `metrics` (SN, SP, ACC and
   AUC in %, MCC) repeat the paper's evaluation; `PSSMDTClassifier(...).discriminant_weights()` and
   `pair_weights` give Eq. 12 and Fig. 2A.

The full reproduction (1,075 benchmark chains, PDB186, every table and figure) is in
[PMC4331676](https://github.com/jeonglab-bcm/fossil/tree/main/PMC4331676), and its results page at
<https://jeonglab-bcm.github.io/fossil/PMC4331676/>.

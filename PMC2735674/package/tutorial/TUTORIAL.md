<!-- Generated from tutorial.ipynb by check_package.py --write. Do not edit by hand. -->

# blmdti tutorial

`blmdti` predicts drug-target interactions with bipartite local models. A drug-target network
is a bipartite graph: drugs on one side, target proteins on the other, an edge where the drug
binds the target. For every candidate pair the method trains two local support vector
machines, one over the other drugs of that target and one over the other targets of that drug,
and combines their scores.

The method comes from:

> Bleakley K, Yamanishi Y. Supervised prediction of drug-target interactions using bipartite
> local models. *Bioinformatics* 25(18):2397-2403 (2009).
> [doi:10.1093/bioinformatics/btp433](https://doi.org/10.1093/bioinformatics/btp433)

## 1. Install

Install the package from its folder in the repository:

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC2735674/package"
```

```python
import blmdti as B

print("blmdti", B.__version__)
print(B.CITATION)
```

```text
blmdti 0.1.0
Bleakley K, Yamanishi Y. Supervised prediction of drug-target interactions using bipartite local models. Bioinformatics 25(18):2397-2403 (2009). doi:10.1093/bioinformatics/btp433
```

## 2. The example input

The package ships a small synthetic network: 12 drugs, 8 target proteins and 44 known
interactions, with a chemical similarity matrix between drugs and a sequence similarity matrix
between targets. Four interactions were deleted from the network before it was saved; finding
them again is the test. `data/README.md` says how the files were made.

The network file has target proteins as rows and drugs as columns, as the benchmark files of
the paper do; `read_network` returns it as drugs by targets.

```python
drugs, targets, adjacency = B.read_network(B.example_path('example_admat.txt'))
_, _, chemical = B.read_matrix(B.example_path('example_simmat_dc.txt'))
_, _, genomic = B.read_matrix(B.example_path('example_simmat_dg.txt'))

print(len(drugs), 'drugs:', ' '.join(drugs))
print(len(targets), 'targets:', ' '.join(targets))
print(int(adjacency.sum()), 'known interactions out of', adjacency.size, 'pairs')
```

```text
12 drugs: D01 D02 D03 D04 D05 D06 D07 D08 D09 D10 D11 D12
8 targets: T01 T02 T03 T04 T05 T06 T07 T08
44 known interactions out of 96 pairs
```

## 3. Run the method

The similarity matrices are not kernels as they stand (a similarity matrix can be asymmetric
and have negative eigenvalues), so `make_psd` symmetrizes each one and adds the smallest
multiple of the identity that lifts every eigenvalue to zero, as the paper's Section 3.5
describes. Then each local model is fitted, leaving out the vertex it scores.

`blm_drug_scores` scores a pair from its target's local model over the drugs, which is what the
method would give for a drug it has never seen. `blm_target_scores` does the mirror image.
`aggregate` is the paper's m(x, y) = max(x, y).

```python
drug_kernel, drug_shift = B.make_psd(chemical)
target_kernel, target_shift = B.make_psd(genomic)
print(f'identity added to the kernels: {drug_shift:.4f} (chemical), {target_shift:.4f} (genomic)')

blmd = B.blm_drug_scores(adjacency, drug_kernel)
blmt = B.blm_target_scores(adjacency, target_kernel)
scores = B.aggregate(blmd, blmt)
print('scores:', scores.shape, f'from {scores.min():.3f} to {scores.max():.3f}')
```

```text
identity added to the kernels: 0.0000 (chemical), 0.0000 (genomic)
scores: (12, 8) from -0.961 to 0.976
```

The highest scoring pairs that the network does not already contain are the method's
predictions. Here are the ten best:

```python
ranked = sorted(
    ((scores[i, j], drugs[i], targets[j])
     for i in range(len(drugs)) for j in range(len(targets)) if adjacency[i, j] == 0),
    reverse=True,
)
for rank, (score, drug, target) in enumerate(ranked[:10], start=1):
    print(f'{rank:2d}  {drug} - {target}  {score:+.4f}')
```

```text
 1  D11 - T08  +0.9758
 2  D08 - T05  +0.9758
 3  D04 - T03  +0.9758
 4  D01 - T01  +0.9758
 5  D12 - T04  -0.9600
 6  D12 - T03  -0.9600
 7  D12 - T02  -0.9600
 8  D12 - T01  -0.9600
 9  D10 - T04  -0.9600
10  D10 - T03  -0.9600
```

## 4. Compare with the expected output

The four interactions that were deleted from the network should come back at the top. That
expectation comes from the way the data were built, not from this package: the two blocks of
the network are separable, so a pair inside a block must score above any pair across blocks.

```python
import json

expected = json.loads(B.example_path('example_expected.json').read_text())
planted = [tuple(pair) for pair in expected['planted_pairs']]
found = [(drug, target) for _, drug, target in ranked[:len(planted)]]
hits = sum(pair in planted for pair in found)
print(f'{hits} of {len(planted)} planted interactions are in the top {len(planted)}')
for pair in planted:
    position = next(i for i, (_, d, t) in enumerate(ranked, start=1) if (d, t) == pair)
    print(f'  {pair[0]} - {pair[1]}: rank {position}')
assert hits == len(planted), 'the planted interactions did not come back'
```

```text
4 of 4 planted interactions are in the top 4
  D01 - T01: rank 4
  D04 - T03: rank 3
  D08 - T05: rank 2
  D11 - T08: rank 1
```

## 5. Scoring a ranking

The paper judges a ranking by the area under the ROC curve and the area under the
precision-recall curve, over every pair of the network. `auc` averages tied scores and `aupr`
takes the trapezoid rule by default, which is what reproduces the paper's tables.

```python
labels = B.interactions(adjacency)
print(f'AUC  {100 * B.auc(labels, scores):.1f}')
print(f'AUPR {100 * B.aupr(labels, scores):.1f} (trapezoid)')
print(f'AUPR {100 * B.aupr(labels, scores, rule="step"):.1f} (step)')
```

```text
AUC  94.4
AUPR 87.2 (trapezoid)
AUPR 88.1 (step)
```

## 6. The same run from the command line

The console script takes the three files and writes the score matrix, drugs as rows.

```python
import subprocess, sys, tempfile, pathlib

out = pathlib.Path(tempfile.mkdtemp()) / 'scores.tsv'
subprocess.run([sys.executable, '-m', 'blmdti', str(B.example_path('example_admat.txt')),
                '--chemical', str(B.example_path('example_simmat_dc.txt')),
                '--genomic', str(B.example_path('example_simmat_dg.txt')),
                '-o', str(out)], check=True)
rows, columns, from_cli = B.read_matrix(out)
import numpy as np
print('same as the API:', bool(np.allclose(from_cli, scores, rtol=1e-9, atol=1e-12)))
print(out.read_text().splitlines()[0][:60], '...')
```

```text
same as the API: True
	T01	T02	T03	T04	T05	T06	T07	T08 ...
```

## 7. Your own data

Three tab separated files, each with a header row and a label column:

| File | Rows | Columns | Values |
| --- | --- | --- | --- |
| network | target proteins | drugs | 1 for a known interaction, 0 otherwise |
| chemical | drugs | drugs | similarity between drugs, for example a SIMCOMP score |
| genomic | targets | targets | similarity between targets, for example a normalized Smith-Waterman score |

The labels and their order must agree between the files. The options that matter:

- `C`: the SVM regularization. The paper fixes it at 1 and does not weight the classes, which
  is the default here.
- `no_positive`: what a local model returns when the pair being scored is the only known edge
  of its drug or of its target, so there is nothing positive to train on. The paper does not
  say; `minus_one` is the rule that reproduces its tables.
- `standardize` in `aggregate`: take the maximum of the z-scores rather than of the raw
  scores. Two local models fitted on different numbers of examples do not give scores on the
  same scale, and the paper's aggregated rows come back only with this on.

A run costs one SVM fit per pair in each direction, so time grows with drugs times targets.
The example here is a second; the paper's enzyme network (445 drugs, 664 targets) is a few
hours on one core, and the reproduction splits it over a cluster.

## 8. The reproduction

The pipeline that checks this package against every table and figure of the paper, the scores
it reaches and the two settings the paper leaves open are in
[`PMC2735674`](https://github.com/jeonglab-bcm/fossil/tree/main/PMC2735674): the results page
is at <https://jeonglab-bcm.github.io/fossil/PMC2735674/> and the pipeline is
`PMC2735674/figure-reproduction/main.nf`.

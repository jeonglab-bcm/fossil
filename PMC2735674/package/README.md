# blmdti

Bipartite local models for drug-target interaction prediction: a drug-target network is a
bipartite graph, and the method scores every candidate pair twice with a local support vector
machine, once from the target's side over drugs and once from the drug's side over targets, then
combines the two.

The method comes from:

> Bleakley K, Yamanishi Y. Supervised prediction of drug-target interactions using bipartite local
> models. *Bioinformatics* 25(18):2397-2403 (2009).
> [doi:10.1093/bioinformatics/btp433](https://doi.org/10.1093/bioinformatics/btp433)

The authors' MATLAB implementation is lost (the project page is gone and no copy is archived), so
this package implements the method from the paper's text. Its reproduction, which checks it
against every table and figure of the paper, is in
[`PMC2735674`](https://github.com/jeonglab-bcm/fossil/tree/main/PMC2735674).

**Why Python:** the paper's own code was MATLAB with LIBSVM, and nothing in the method needs an R
or Bioconductor package, so the default rule of the reproduction skill applies: Python.

## Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC2735674/package"
```

Or with uv:

```bash
uv pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC2735674/package"
```

Python 3.10 or later, with NumPy, SciPy and scikit-learn.

## Use

```python
import blmdti as B

drugs, targets, adjacency = B.read_network(B.example_path("example_admat.txt"))
_, _, chemical = B.read_matrix(B.example_path("example_simmat_dc.txt"))
_, _, genomic = B.read_matrix(B.example_path("example_simmat_dg.txt"))

drug_kernel, _ = B.make_psd(chemical)      # symmetrize, then lift the eigenvalues
target_kernel, _ = B.make_psd(genomic)

blmd = B.blm_drug_scores(adjacency, drug_kernel)      # a new drug against known targets
blmt = B.blm_target_scores(adjacency, target_kernel)  # a known drug against a new target
scores = B.aggregate(blmd, blmt)                      # the paper's m(x, y) = max(x, y)
```

From the command line:

```bash
blmdti "$(blmdti --example-path)" \
  --chemical .../example_simmat_dc.txt --genomic .../example_simmat_dg.txt -o scores.tsv
```

The tutorial walks through the whole thing: [`tutorial/TUTORIAL.md`](tutorial/TUTORIAL.md).

## What is in it

| Function | Does |
| --- | --- |
| `make_psd` | Symmetrize a similarity matrix and add the smallest multiple of the identity that makes it a kernel (the paper's Section 3.5). |
| `blm_drug_scores`, `blm_target_scores` | The two local models, leaving the scored vertex out of training. |
| `aggregate` | m(x, y) = max(x, y), with `standardize=True` for the maximum of the z-scores. |
| `nn_drug_scores`, `nn_target_scores` | The nearest-profile baseline the paper compares with. |
| `krm_drug_scores`, `krm_target_scores` | The kernel regression method of Yamanishi et al. (2008), the paper's comparison method. |
| `auc`, `aupr`, `precision_recall` | The ranking metrics, with the paper's tie handling. |
| `read_network`, `read_matrix`, `write_matrix` | The benchmark file format. |

## Two settings the paper does not give

Both were identified in the reproduction and are recorded there with their sensitivity:

- **A local model with no positive example.** When the pair being scored is the only known edge of
  its target (or of its drug), the local model has nothing positive to learn from. `no_positive`
  controls what it returns; `minus_one` reproduces the paper's tables.
- **The scale of two scores before the maximum.** `aggregate(..., standardize=True)` turns each
  matrix into z-scores first. That reproduces the paper's aggregated rows; the plain maximum does
  not.

## Licence

MIT, the repository's licence: the method is implemented from the paper's text, not ported from
the authors' code.

## Citation

Cite the paper above. The reproduction is at
<https://github.com/jeonglab-bcm/fossil/tree/main/PMC2735674>.

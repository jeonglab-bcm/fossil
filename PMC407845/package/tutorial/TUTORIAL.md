<!-- Generated from tutorial.ipynb by check_package.py --write. Do not edit by hand. -->

# manetworker tutorial

`manetworker` infers how active each transcription factor (TF) is in each experiment, by regressing every experiment's expression log ratios on the TFs' ChIP binding log ratios (Step 1), and then calls a bound gene a functional target when its expression across experiments correlates with the TF's activity profile (Step 2). Bound genes are split into B+/C+ (bound and coupled) and B+/C- (bound but not coupled).

The method is MA-Networker, from:

> Gao F, Foat BC, Bussemaker HJ. Defining transcriptional networks through integrative modeling of mRNA expression and transcription factor binding data. *BMC Bioinformatics* 5:31 (2004). doi:10.1186/1471-2105-5-31

The authors' code was never released; this package implements the method from the paper's Methods.

## 1. Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC407845/package"
```

It needs Python 3.10 or later, NumPy and SciPy. This notebook was run in a fresh environment with the package installed from its wheel.

```python
import json

import numpy as np

import manetworker as mn

print("manetworker", mn.__version__)
```

```text
manetworker 0.1.0
```

## 2. The example input

Three tab-separated files with the same genes in the same order: expression log2 ratios (genes x experiments), ChIP enrichment ratios and ChIP P-values (genes x TFs). They are synthetic: 500 genes, 8 TFs and 60 experiments, with three active TFs planted by `scripts/make_example_data.py` (see `data/README.md`).

```python
genes, experiments, E = mn.read_matrix(mn.example_path("expression.tsv"))
_, tfs, ratio = mn.read_matrix(mn.example_path("binding_ratio.tsv"))
_, _, chip_p = mn.read_matrix(mn.example_path("binding_p.tsv"))
print(f"{len(genes)} genes, {len(experiments)} experiments, {len(tfs)} TFs: {', '.join(tfs)}")
print(f"missing expression values: {int(np.isnan(E).sum())}; missing ChIP ratios: {int(np.isnan(ratio).sum())}")
print("first rows of the expression file:")
for g, row in zip(genes[:3], E[:3]):
    print(" ", g, " ".join(f"{v:6.2f}" for v in row[:6]), "...")
```

```text
500 genes, 60 experiments, 8 TFs: TF1, TF2, TF3, TF4, TF5, TF6, TF7, TF8
missing expression values: 10; missing ChIP ratios: 5
first rows of the expression file:
  G000  -0.32  -0.31  -0.19   0.57   0.10   0.21 ...
  G001  -0.21   0.31  -0.09  -0.85   0.24  -0.23 ...
  G002   0.23   0.34   0.24   0.04   0.30  -0.15 ...
```

## 3. Run the method

`mn.run` takes the ChIP data as log2 ratios (`mn.log_ratio`), keeps the TFs that predict expression by backward selection (P < 0.005 / number of experiments, as in the paper), computes their activity profiles and couplings, and classifies every gene for every kept TF.

```python
res = mn.run(E, mn.log_ratio(ratio), chip_p, tfs)
print("TFs kept:", ", ".join(res["tfs"]))
print(f"{'TF':<5}" + "".join(f"{c:>14}" for c in mn.CLASSES))
for tf, row in zip(res["tfs"], res["counts"]):
    print(f"{tf:<5}" + "".join(f"{int(v):>14}" for v in row))
```

```text
TFs kept: TF1, TF2, TF3
TF               B-         B+/C+         B+/C-  unclassified
TF1             459            24            16             1
TF2             458            25            15             2
TF3             460            25            15             0
```

## 4. Compare with the expected output

`expected.json` holds what the generating formula planted, not output of this package: the active TFs and their functional and non-functional bound genes. The data README states the expected result: exactly TF1 to TF3 kept, at least 72 of the 75 functional targets B+/C+, none of the non-functional bound genes B+/C+.

```python
expected = json.loads(mn.example_path("expected.json").read_text())
found = planted = wrong = 0
for j, tf in enumerate(res["tfs"]):
    coupled = {genes[i] for i in np.nonzero(res["classes"][:, j] == 1)[0]}
    found += len(coupled & set(expected["functional_targets"][tf]))
    planted += len(expected["functional_targets"][tf])
    wrong += len(coupled & set(expected["nonfunctional_bound"][tf]))
    r = np.corrcoef(res["activity_t"][j], expected["true_activity"][tf])[0, 1]
    print(f"{tf}: activity profile correlates {r:.3f} with the planted one")
print(f"active TFs: {res['tfs'] == expected['active_tfs']} ({', '.join(expected['active_tfs'])} planted)")
print(f"{found} of {planted} functional targets called B+/C+; {wrong} non-functional bound genes called B+/C+")
assert res["tfs"] == expected["active_tfs"] and found >= 72 and wrong == 0
```

```text
TF1: activity profile correlates 0.965 with the planted one
TF2: activity profile correlates 0.976 with the planted one
TF3: activity profile correlates 0.968 with the planted one
active TFs: True (TF1, TF2, TF3 planted)
74 of 75 functional targets called B+/C+; 0 non-functional bound genes called B+/C+
```

## 5. From the command line

The same run as `manetworker EXPRESSION BINDING_RATIO BINDING_P -o OUTDIR` (`--example` uses the bundled files). It writes `counts.csv`, `classes.tsv`, `activity.tsv`, `coupling_r.tsv` and `selection.json`.

```python
!manetworker --example -o tutorial_out
!cat tutorial_out/counts.csv
```

```text
3 of 8 TFs kept: TF1, TF2, TF3; outputs in tutorial_out
tf,B-,B+/C+,B+/C-,unclassified
TF1,459,24,16,1
TF2,458,25,15,2
TF3,460,25,15,0
```

## 6. Your own data

- **Expression:** genes x experiments, log2 ratios, blank where missing. Each experiment's regression uses the genes measured in it; each coupling uses the experiments in which the gene was measured.
- **ChIP:** two genes x TFs files, enrichment ratios (not logged; missing or non-positive ratios count as unmeasured and those genes are unclassified for that TF) and P-values. A gene is bound when P < `bind_p` (1e-3, as in the paper).
- **Options:** `alpha` (backward selection threshold), `q` (false discovery rate, 0.05), `scope` (`per_tf`, `all` or `bound`), `select=False` to keep every TF, `expr_available` to mark which genes have enough expression data.
- **Outputs:** `res["activity_t"]` (TF activity profiles as regression t-values), `res["coupling"]` (`r` and two-sided `p`, genes x TFs), `res["classes"]` (0 B-, 1 B+/C+, 2 B+/C-, 3 unclassified) and `res["counts"]`.

By default `mn.run` follows the paper's text: coefficient activity profiles and a two-sided coupling test. The reproduction of the paper found that the paper's figures fit `profile="t"` (t-value activity profiles, as Fig. 1b plots) and `sided="one"` (positive coupling only, as Fig. 1c shows) better.

## 7. The paper's data

The reproduction of the paper with this package, on the Lee et al. (2002) ChIP data and a rebuilt 677-array expression library, is in the fossil repository: [PMC407845](https://github.com/jeonglab-bcm/fossil/tree/main/PMC407845), with its [results page](https://jeonglab-bcm.github.io/fossil/PMC407845/).

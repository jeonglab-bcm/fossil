<!-- Generated from tutorial.ipynb by check_package.py --write. Do not edit by hand. -->

# spsvm tutorial

`spsvm` predicts which cysteines and histidines of a protein bind zinc. It reads PSI-BLAST profiles, scores each residue with a local SVM and each pair of nearby candidates with a semi-pattern SVM, and combines the two with a gating rule. The method is the SP-SVM of

> Passerini A, Andreini C, Menchetti S, Rosato A, Frasconi P. Predicting zinc binding at the proteome level. *BMC Bioinformatics* 8:39 (2007). doi:10.1186/1471-2105-8-39

The authors' program is lost; this package implements the method from the paper's text.

## 1. Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC1800866/package"
```

It needs Python 3.10 or later, NumPy, SciPy and scikit-learn.

```python
import spsvm

print("spsvm", spsvm.__version__)
```

```text
spsvm 0.1.0
```

## 2. The example input

The package ships three files (see `data/README.md`):

- a small training set: PSI-BLAST profiles of 150 PDB chains of the paper's data set and their zinc labels from the paper's Additional file 1;
- the PSI-BLAST profile of the human protein NP_060357.1 (CZIB), which the paper predicted to bind zinc (its Fig. 8);
- the zinc ligands of CZIB in the crystal structure 5ZLQ, released in 2018, after the paper.

```python
profiles = spsvm.read_profiles(spsvm.example_path("example_train_profiles.npz"))
labels = spsvm.read_table(spsvm.example_path("example_train_labels.txt"))
n_zinc = sum(1 for c in labels.values() if any(c.values()))
n_res = sum(len(c) for c in labels.values())
n_pos = sum(sum(c.values()) for c in labels.values())
print(f"{len(labels)} training chains ({n_zinc} with zinc), {n_res} C and H residues, {n_pos} bind zinc")

query = spsvm.read_ascii_pssm(spsvm.example_path("czib_NP_060357.1.pssm"))
print("CZIB:", len(query), "residues;", query.sequence[:40], "...")
print("first profile row (A R N D ...):", (query.frequencies[0] * 100).astype(int)[:10], "info", query.information[0], "weight", query.weight[0])
```

```text
150 training chains (50 with zinc), 1266 C and H residues, 193 bind zinc
CZIB: 160 residues; MGKIALQLKATLENITNLRPVGEDFRWYLKMKCGNCGEIS ...
first profile row (A R N D ...): [0 0 0 0 0 0 0 0 0 0] info 2.88 weight 0.76
```

## 3. Run the method

Train the SPCH-SVM (cysteines and histidines) with the paper's tuned parameters, then predict CZIB. Each candidate gets three probabilities: local, semi-pattern (the best pair it belongs to) and gated, `P = P_sp + (1 - P_sp) P_local`.

```python
chains = [spsvm.Chain(n, profiles[n].sequence, spsvm.descriptors(profiles[n]), labels[n]) for n in sorted(labels)]
model = spsvm.SPSVM("CH").fit(chains)

czib = spsvm.chain_from_profile("CZIB", query, min_weight=0.015)
probs = model.predict_chain(czib)
top = sorted(probs, key=lambda p: -probs[p]["gated"])
print(f"{'residue':<9}{'local':>7}{'semi-pattern':>14}{'gated':>7}")
for p in top[:8]:
    v = probs[p]
    print(f"{query.sequence[p]}{p + 1:<8}{v['local']:7.2f}{v['semipattern']:14.2f}{v['gated']:7.2f}")
print("zinc-binding protein (3 residues above 0.7):", spsvm.predict_protein(probs))
```

```text
residue    local  semi-pattern  gated
C70         0.66          0.82   0.94
C67         0.59          0.82   0.93
C33         0.54          0.70   0.86
C36         0.39          0.70   0.82
H155        0.07          0.14   0.19
C160        0.03          0.14   0.16
C102        0.06          0.00   0.06
zinc-binding protein (3 residues above 0.7): True
```

## 4. Compare with the expected output

The expected output is the set of residues that bind zinc in the crystal structure 5ZLQ (Cys33, Cys36, Cys67 and Cys70), read from the structure, not from this package. The paper numbered them 31, 34, 65 and 68 in its homology model. Here the four highest-scoring residues should be these four.

```python
import csv

with open(spsvm.example_path("czib_5zlq_zinc_ligands.csv")) as f:
    expected = sorted(int(r["position"]) for r in csv.DictReader(f))
ours = sorted(p + 1 for p in top[:4])
hits = len(set(ours) & set(expected))
print(f"{hits} of {len(expected)} zinc ligands of 5ZLQ are among our 4 highest-scoring residues: {ours}")
assert ours == expected
```

```text
4 of 4 zinc ligands of 5ZLQ are among our 4 highest-scoring residues: [33, 36, 67, 70]
```

## 5. From the command line

`spsvm` reads one or more ASCII PSSMs and writes one CSV row per candidate residue (1-based positions). Without `--train` and `--labels` it trains on the bundled set.

```python
path = spsvm.example_path("czib_NP_060357.1.pssm")
!spsvm "{path}" | head -6
```

```text
protein,position,residue,p_local,p_semipattern,p_gated,protein_called
czib_NP_060357.1,33,C,0.5431,0.6974,0.8617,1
czib_NP_060357.1,36,C,0.3931,0.6974,0.8163,1
czib_NP_060357.1,67,C,0.5897,0.8173,0.9250,1
czib_NP_060357.1,70,C,0.6581,0.8173,0.9375,1
czib_NP_060357.1,102,C,0.0643,0.0000,0.0643,1
```

## 6. Your own data

- **Profiles:** run `psiblast -query protein.fa -db <protein database> -num_iterations 3 -out_ascii_pssm protein.pssm -save_pssm_after_last_round`. The reproduction used UniRef100 release 2010_01; the paper used NCBI nr of 2005.
- **Training data:** the bundled set is small. For real predictions train on the 2,458 chains of the paper's Additional file 1: `PMC1800866/figure-reproduction/output/profiles/pdb_profiles.npz` with the labels of Additional file 1 (`spsvm.read_table`; positions mapped to today's SEQRES in `output/predictions/candidates.tsv`).
- **Options:** `SPSVM("CHDE")` adds aspartate and glutamate; `min_weight` (0.015 in the paper) skips residues with too few aligned sequences; the protein call uses `predict_protein(probs, threshold=0.7, min_residues=3)`.
- **Output:** `local`, `semipattern` and `gated` probabilities per residue. The gated one is the prediction.

## 7. The full reproduction

The pipeline that reruns the paper's evaluations with this package, and the comparison with every figure and table, are in [PMC1800866](https://github.com/jeonglab-bcm/fossil/tree/main/PMC1800866) (results page: https://jeonglab-bcm.github.io/fossil/PMC1800866/).

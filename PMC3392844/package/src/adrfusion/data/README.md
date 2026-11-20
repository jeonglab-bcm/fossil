# Example data

| File | What it is |
| --- | --- |
| `example_drugs.txt` | 120 synthetic drugs in the pipe-delimited format of Liu et al.'s training file: `drug id|name|compound id|ADR bits (30)|chem bits (40)|target bits (20)|transporter bits (5)|enzyme bits (6)|pathway bits (10)|indication bits (25)|fold of the drug for each ADR (30, comma-separated)`. |
| `example_expected.csv` | The expected cross-validated SVM decision value of every (drug, ADR) pair with the full feature set (`chem+bio+pheno`): columns `drug`, `adr`, `label`, `decision`. |

**Where they come from.** Synthetic, made by `scripts/make_example_data.py` (in the package folder, not
installed), seed 20120630. The 120 drugs fall in four groups; each group carries each feature and each
ADR with its own chance (0.7 or 0.05, 0.6 or 0.04 for ADRs), so drugs of a group look alike and share
ADRs. Every ADR has at least 8 drugs, and its 5 folds are stratified.

**The expected output is not written by adrfusion.** The same script trains the official LIBSVM
(`libsvm-official` 3.37, the C library of Chang and Lin, which the paper used) on the raw 0/1
features with the paper's settings (`-s 0 -t 2 -g 0.008 -c 2`), one model per ADR and fold, the
other ADRs as features, and writes its decision values. adrfusion builds the same RBF kernel from
per-block Hamming distances and trains scikit-learn's copy of libsvm. Compare at an absolute
tolerance of 1e-3, the solvers' stopping tolerance: half the values agree to 1e-10, the largest
difference is 7e-4.

**Licence.** MIT, like the package. No data of the paper, SIDER, DrugBank, PubChem or KEGG are
included; the paper's own training data come from Zhang et al. 2015 (see the reproduction).

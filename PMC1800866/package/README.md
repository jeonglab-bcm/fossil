# spsvm

Zinc-binding residues of proteins from PSI-BLAST profiles, with the SP-SVM of

> Passerini A, Andreini C, Menchetti S, Rosato A, Frasconi P. Predicting zinc binding at the proteome level. *BMC Bioinformatics* 8:39 (2007). [doi:10.1186/1471-2105-8-39](https://doi.org/10.1186/1471-2105-8-39)

The method has three parts. A local SVM scores each cysteine and histidine from a window of profile descriptors. A semi-pattern SVM scores each pair of candidates separated by 0 to 7 residues; it uses the paper's semi-pattern kernel (Eq. 1). Both margins pass through Platt sigmoids, and the gating rule of Eq. 2 combines them: P = P_sp + (1 − P_sp) P_local. A protein is called zinc-binding when at least three residues are above 0.7.

The authors' C++ program ("Zinc Finder") is no longer available. This package implements the method from the paper's text, with the tuned parameters of the paper's Additional file 1 (`spsvm.PAPER_PARAMS`). Our reproduction of the paper's figures and tables with it is in [`PMC1800866/`](https://github.com/jeonglab-bcm/fossil/tree/main/PMC1800866) of the fossil repository.

## Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC1800866/package"
```

Python 3.10 or later, with NumPy, SciPy and scikit-learn.

**Why Python.** The paper's method has no R or Bioconductor dependency, and the authors' code was C++, so the default rule gives Python. The SVMs are scikit-learn's `SVC` (LIBSVM) with an RBF kernel on explicit feature maps; the semi-pattern kernel is the dot product of such a map, so no custom kernel code is needed.

## Use

```python
import spsvm

# Train on profiles and labels (here the small bundled training set).
profiles = spsvm.read_profiles(spsvm.example_path("example_train_profiles.npz"))
labels = spsvm.read_table(spsvm.example_path("example_train_labels.txt"))
chains = [spsvm.Chain(n, profiles[n].sequence, spsvm.descriptors(profiles[n]), labels[n]) for n in sorted(labels)]
model = spsvm.SPSVM("CH").fit(chains)          # the SPCH-SVM with the paper's parameters

# Predict a new protein from its PSI-BLAST ASCII PSSM.
query = spsvm.read_ascii_pssm(spsvm.example_path("czib_NP_060357.1.pssm"))
probs = model.predict_chain(spsvm.chain_from_profile("CZIB", query, min_weight=0.015))
print(spsvm.predict_protein(probs))            # at least 3 residues above 0.7?
```

From the command line (trains on the bundled set unless `--train` and `--labels` are given):

```bash
spsvm "$(spsvm --example-path)" -o czib.csv
```

The [tutorial](tutorial/TUTORIAL.md) runs this on the bundled example and checks the result against the zinc ligands of a crystal structure that was released after the paper.

## Input and output

- **Profiles.** PSI-BLAST `-out_ascii_pssm` files (`read_ascii_pssm`), or many at once in an `.npz` (`write_profiles`, `read_profiles`). The descriptor of a position is the 20 weighted observed percentages divided by 100, the information per position, the relative weight of gapless real matches to pseudocounts, and a flag that is 1 outside the chain. Make profiles with `psiblast -num_iterations 3 -out_ascii_pssm` against a protein database; the paper used NCBI nr of 2005, the reproduction used UniRef100 release 2010_01.
- **Training labels.** Rows `class chain position residue [cofactor]`, `class` 1 (binds zinc) or -1, `position` 0-based: the format of the paper's Additional file 1.
- **Output.** For each candidate residue: `local`, `semipattern` (the largest probability of the semi-patterns that contain it; 0 if none) and `gated` (Eq. 2). The command line writes CSV with 1-based positions and the protein call.

Other functions: `semipattern_kernel` (Eq. 1 computed directly), `aurpc`, `auc_with_se` (Wilcoxon-Mann-Whitney AUC with the Hanley-McNeil standard error), `pr_curve`, `protein_scores` (each chain's third-highest probability, for protein-level curves).

## Limits

The bundled training set is small and meant for the tutorial. For real use, train on the paper's 2,458 chains (`PMC1800866/figure-reproduction/output/profiles/pdb_profiles.npz` with Additional file 1). The parameters were tuned by the authors on 2005 profiles; profiles from another database shift the margins, so the Platt constants may be off.

## Licence

MIT, see [LICENSE](LICENSE). The example data are described in [data/README.md](src/spsvm/data/README.md).

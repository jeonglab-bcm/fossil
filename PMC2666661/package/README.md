# rfld

Random forest variable importance for SNPs in linkage disequilibrium, with the revised tree builder (RF1) and revised importance measure (IM1) of

> Meng YA, Yu Y, Cupples LA, Farrer LA, Lunetta KL. Performance of random forest when SNPs are in linkage disequilibrium. *BMC Bioinformatics* 10:78 (2009). [doi:10.1186/1471-2105-10-78](https://doi.org/10.1186/1471-2105-10-78)

- **RF0** is Breiman and Cutler's Random Forests 5.1 for categorical predictors, ported step by step from its Fortran (`prog.f`): bootstrap weights, mtry candidates drawn with replacement, exhaustive subset splits by the Gini criterion, node size 1, permutation importance over the out-of-bag cases of the trees that split on a variable.
- **RF1** keeps SNPs in LD out of the same tree: after a tree splits on a SNP, every SNP whose pairwise genotypic r² with it exceeds R leaves that tree's pool.
- **IM0** is the importance Random Forests 5.1 prints (100 × the mean decrease in accuracy over all T trees); **IM1** averages over the T_v trees that split on the SNP.

The authors' program (a modified Random Forests 5.1, "Random Forests Linkage Disequilibrium project") is lost; this package implements it from the paper's Methods. The reproduction of the paper's figures and tables with it is in [`PMC2666661/`](https://github.com/jeonglab-bcm/fossil/tree/main/PMC2666661) of the fossil repository.

## Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC2666661/package"
```

Python 3.10 or later, with NumPy and Numba.

**Why Python.** The method is a Fortran program with no R or Bioconductor dependency, so the default rule gives Python. The tree builder is compiled with Numba; 5000 trees on 500 people and 100 SNPs take about 5 s on one core.

## Use

```python
import rfld

X, y, names = rfld.read_genotypes(rfld.example_path())       # status column + one column per SNP (0, 1, 2)
rows = rfld.importance_table(X, y, names, ntree=5000, mtry=35, seed=1,
                             revised_tree=True, ld_threshold=0.5)   # RF1
best = sorted(rows, key=lambda r: -r["im1"])[:10]                   # rank by IM1
```

`rfld.grow_forest` returns the arrays (`im0`, `im1`, `trees`, `oob_error`). From the command line:

```bash
rfld genotypes.csv --revised-tree --ld-threshold 0.5 -o importance.csv
```

The [tutorial](tutorial/TUTORIAL.md) runs both forests on the bundled example and checks them against the Fortran program.

Also in the package: the paper's simulation models (`MODELS`, `DESIGNS`, `LD_MODELS`, `snp_dataset`, `haplotype_dataset`, `haplotype_frequencies`, `table1_statistics`) and two-SNP haplotype phasing (`haplotype_em`, `phase_posterior`, `sample_haplotype_pairs`), which match haplo.stats' `haplo.em` to 1e-5 (frequencies) and 1e-4 (phase posteriors).

## How it was checked

- RF0 against the unmodified Fortran program on 20 simulated data sets: the importances differ from Fortran's about as much (1.01 times) as two runs of `rfld` with different seeds differ from each other, and the mean risk-SNP importance differs by z = 0.08.
- RF1 against our own patch of the Fortran program (the paper's revised program is lost): 1.01 times, z = 0.07.
- The phasing against haplo.stats 1.9.9.1 on 66 simulated data sets.

## Limits

- The paper does not give the threshold R. For perfect proxies (r² = 1) any R from 0.1 (above the largest chance r² among the paper's noise SNPs in our replicates, 0.090) to just below 1 gives the same forests; a low R also drops noise SNPs that correlate by chance and changes the results.
- Large data: the forest keeps the genotypes in memory and grows trees on one core.

## Licence

MIT, see [LICENSE](LICENSE). The code is written from the paper and from reading Random Forests 5.1; it contains no code of either. The example data are described in [data/README.md](src/rfld/data/README.md).

# Example data

| File | What it is |
| --- | --- |
| `example_genotypes.csv` | 300 cases and 300 controls genotyped at 60 SNPs (0, 1 or 2 copies of the minor allele). Column `status` is 1 for a case and 0 for a control. |
| `example_expected.csv` | The expected output: which SNPs are the disease loci, their B statistics (single SNPs and the pair) and single-locus chi-squared tests. |

Both files are synthetic and made by [`scripts/make_example_data.py`](../../scripts/make_example_data.py)
(NumPy and SciPy, seed 20090130), not by this package. The data follow the paper's simulation design:
the threshold model (model 3) of Marchini, Donnelly and Cardon (2005) with prevalence 0.1 and marginal
effect 1.0 (the paper's values), both disease loci at minor allele frequency 0.3 and genotyped directly
(SNPs `snp17` and `snp44`); the other 58 SNPs are unlinked, with minor allele frequencies from
U(0.05, 0.5).

The expected output comes from the generator, not from the package: the disease SNPs are known by
construction, and the script computes the B statistic from the formula printed in the paper (with its
own NumPy code) and the chi-squared test with `scipy.stats.chi2_contingency`. Compare the statistics
and p-values at a relative tolerance of 1e-8; epiForest should report both disease SNPs.

Licence: MIT, like the package (the data are generated, with no third-party content).

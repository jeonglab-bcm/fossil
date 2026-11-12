# Example data

| File | What it is | Where it comes from |
| --- | --- | --- |
| `example_data.csv` | 1000 features (rows) by 20 samples (`X1`–`X10`, `Y1`–`Y10`), with the truth in `null` (800 null, 200 non-null features) | Simulated by `inst/scripts/make_example_data.R` with the paper's design (Additional File 1, section 8): bitriangular effects (Langaas et al. 2005, a = log2 1.2, b = log2 4, mode log2 2), `log(exp(R) + exp(eps))` noise with SD 0.1 per feature, `set.seed(2010)`; values rounded to 6 significant digits |
| `expected_fdr_power.csv` | Rejections, achieved FDR and power at BH 5% after removing 0, 25, 50 or 75% of the features with each filter | Computed by the same script with base R only (`t.test`, `quantile`, `p.adjust`), not with filterfdr. The package must give the same rejections exactly and the same FDR and power to 1e-12 |
| `fig1_published.csv` | The p-value densities of the paper's Fig. 1 at p = 0.05, 0.10, …, 0.95 | Read from the authors' original vector figure (BMC Bioinformatics 11:450, Additional file "Authors' original file for figure 1") by the reproduction's `figure-reproduction/pipeline/published.py` and `make_example_published.py`. The alternative's variance-filter curve is left out: the package does not reproduce it (see the reproduction README). Compare at 0.01 |

Licence: the simulated files are released with the package (MIT). The Fig. 1 values come from
van Iterson, Boer and Menezes (2010), published under the Creative Commons Attribution License 2.0;
cite the paper when you use them.

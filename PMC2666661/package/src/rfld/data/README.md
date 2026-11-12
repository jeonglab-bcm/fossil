# Example data

| File | What it is | Source | Licence |
| --- | --- | --- | --- |
| `h4m4_r1.csv` | One simulated case-control data set: 250 cases and 250 controls (`status` 1 and 0), 104 SNPs coded as the number of risk alleles (0, 1, 2). `snp1`-`snp4` are the risk SNPs of one system of the H4M4 model (Table 1 of Meng et al. 2009; allele frequency 0.282, penetrance factors 1.2e-8, 0.79, 1), `snp5`-`snp100` are noise SNPs, and `snp101`-`snp104` are perfect LD proxies (r^2 = 1) of `snp1`-`snp4` (LD model r1 of the paper's Table 5). | Written by `scripts/make_example_data.py` (seed 20090305) with `rfld.snp_dataset`. | MIT, as the package |
| `h4m4_r1_expected.csv` | Expected importances of every SNP: Breiman and Cutler's Fortran Random Forests 5.1 (`prog.f`, built with gfortran) on `h4m4_r1.csv`, 5000 trees, mtry 35, every SNP categorical; mean and SD over 5 seeds. `rf0_*` is the unmodified program (RF0); `rf1_*` is the program with our patch of its tree builder for RF1 (R = 0.5). `im0` is the program's printed importance (100 × the mean decrease in accuracy over all trees), `im1` the same over the trees that split on the SNP, `trees` that number. | `PMC2666661/figure-reproduction/pipeline/fortran_expected.py` in the fossil repository; the Fortran program is downloaded from https://www.stat.berkeley.edu/~breiman/RandomForests/cc_software.htm and is not included here. | MIT |

Forests are random, and the Fortran program and `rfld` use different random number streams, so the
same data give importances that differ by the seed-to-seed spread (column `*_sd`, about 0.01-0.03).
Compare a run of `rfld` with the expected values at 4 SD of the difference between one run and a
5-seed mean, `4 * sd * sqrt(1 + 1/5)`. The RF0 values come from Breiman and Cutler's own program;
the RF1 values check `rfld` against a second implementation of the same rule (ours, in Fortran),
because the authors' revised program is lost.

# Example data

| File | What it is |
| --- | --- |
| `miller_clinical.csv` | The training set of Huang et al. (2014): the 236 Uppsala tumours of Miller et al. (2005, GEO GSE3494) that have a relapse status. Columns: `tumour` (ID), `time` (relapse-free survival in years, days / 365; empty for two patients), `event` (1 = relapse), `age`, `er` and `pgr` (1 = positive), `size_mm`, `grade` (1 to 3), `node` (1 = positive), `p53` (1 = mutant). |
| `paper_values.csv` | The expected output for `miller_clinical.csv`: the log-rank p-values of Fig. 1 and the univariate Cox p-values of Table 2 (clinical model), as printed in the paper. |
| `synthetic_expression.csv` | Synthetic log2 expression: 76 genes (rows) by 150 tumours. Genes `GA01` to `GA12`, `GB01` to `GB12` and `GC01` to `GC12` follow the activity of gene sets A, B and C; `BG01` to `BG40` are background. |
| `synthetic_sets.gmt` | The three gene sets, in GMT format. |
| `synthetic_survival.csv` | Relapse time (years) and event of each synthetic tumour. |
| `synthetic_truth.csv` | The expected output for the synthetic data, part 1: the activity of each set in each tumour, which the expression and the hazard were drawn from. |
| `synthetic_effects.csv` | The expected output, part 2: the true log hazard ratio of each set's activity (A 1.0, B 0.7, C 0). |

## Where they come from

The clinical columns are from the Bioconductor data package breastCancerUPP 1.40.0 (Schroeder M,
Haibe-Kains B, et al.; Artistic-2.0), which carries the Uppsala cohort's relapse-free survival,
and p53 mutation status is from the GEO file `GSE4922_Clinical_file_for_both_Uppsala_Singapore_Samples.txt`
(Ivshina et al. 2006, the same tumours). Both are redistributable: Artistic-2.0 for breastCancerUPP,
and NCBI GEO places no restrictions on its data.

The expected output of the clinical example comes from the paper, not from this package. It is
reproduced exactly when the two patients without a time are given time 0 and the patients
without p53 status count as wild type, the two settings that also give the paper's Table 1
(mean RFS 8.167 years; p53 55 mutated, 181 wild type, 0 unknown). Compare at the printed
precision (half a unit in the last printed digit).

The synthetic data are written by `scripts/make_example_data.R` (seed 20140929) from this formula:
gene g of set k is `8 + 0.9 * activity_k + N(0, 0.5)`, background genes are `8 + N(0, 0.7)`, and the
hazard is `0.08 * exp(1.0 * activity_A + 0.7 * activity_B)` per year, censored at a uniform 4 to 12
years. The expected output is the formula itself: each set's deregulation score should follow its
activity (we check a correlation of at least 0.9), and the fitted Cox-LASSO coefficients should
rank the sets as their true log hazard ratios do (A above B above C). The synthetic data carry the
package's MIT licence.

Huang S, Yee C, Ching T, Yu H, Garmire LX. A novel model to combine clinical and pathway-based
transcriptomic information for the prognosis prediction of breast cancer. PLoS Comput Biol
10(9):e1003851 (2014). doi:10.1371/journal.pcbi.1003851. CC BY 4.0.

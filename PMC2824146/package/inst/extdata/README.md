# Example data

| File | What it is | Source |
| --- | --- | --- |
| `missing_shares.csv` | The missingness design: the share of the incomplete cases missing each covariate, and each pair | The paper's Methods ("approximately 70%, 55%, 20% and 10% ... 35% ... 10% ... 5%"), typed from the article |
| `table3_expected.csv` | Table 3: odds ratios between the missingness indicators at 5 to 75% incomplete cases, as printed (strings, so the printed precision is kept) | Table 3 of the article, typed |
| `lp_expected.csv` | The linear predictor coefficients of the full Cox model on the breast cancer data, as printed | The Methods equation of the article, typed |
| `example_cohort_mar25.csv` | One simulated cohort of 1000 cases with 25% of cases made incomplete by the MAR mechanism, to try the methods on. Columns X1 to X7, X8g (tumour size group 1 to 3), time (days), status (1 = event); NA marks a deleted value | Written by `scripts/make_example_data.R` with this package (seeds 2010 and 7); input only, it has no expected output |

The expected outputs (`table3_expected.csv`, `lp_expected.csv`) come from the paper, not from this
package. The tutorial compares `table3_odds_ratios()` with Table 3 at printed precision (half a unit
in the last printed digit), and the full Cox model on `TH.data::GBSG2` with the printed coefficients
at the same precision.

The article (Marshall A, Altman DG, Royston P, Holder RL. BMC Medical Research Methodology 10:7, 2010,
doi:10.1186/1471-2288-10-7) is open access under CC BY 2.0. The numbers here are facts reported in
it. The simulated cohort is ours (MIT, like the package).

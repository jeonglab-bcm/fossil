# Example data

| File | What it is | Source |
| --- | --- | --- |
| `cumulative_trials.csv` | 12 two-arm trials (events and patients per arm), in the order they would be published. | Synthetic: drawn by `scripts/make_example_data.py` as Appendix S2 of the paper describes (Cochrane trial-size mixture, control risk uniform on 5% to 15%, tau^2 = 0.15, no true effect), seed 3196500. Trial T03's treatment events are set to 0 so that the 0.5 correction is used. |
| `cumulative_expected.csv` | The cumulative DerSimonian-Laird analysis after each trial: cumulative patients and events, pooled RR, RRR and tau^2. | Computed by `scripts/make_example_data.py` with plain Python loops written from Appendix S1's formulas, not with the package. Compare at a relative tolerance of 1e-8. |
| `table2_printed.csv` | The paper's Table 2 rows for PC 3% and RRR 30% (9 OIS values for patients and events). | Thorlund et al. (2011), Table 2, as printed. The paper rounds its values inconsistently, so compare the unrounded formula within one rounding step (500 patients above 10,000, 100 below; 50 events). |

All files are synthetic or quoted from a CC BY article (Thorlund et al., PLoS ONE 2011; doi:10.1371/journal.pone.0025491) and are released with the package under its MIT licence. Total size under 2 kB.

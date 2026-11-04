# PMC2349296 reproduction check

**Result: all must-hold checks pass**


## Agreement at the published precision

| Item | All five corpora | HPRD50, IEPA, LLL |
| --- | --- | --- |
| Table 2, co-occurrence | 11 of 15 | 9 of 9 |
| Table 2, RelEx | 3 of 15 | 0 of 9 |
| Table 3 | 25 of 30 | 18 of 18 |
| Table 4, co-occurrence | 6 of 10 | 6 of 6 |
| Table 4, RelEx | 1 of 10 | 1 of 6 |

## Tables (published / ours)

### Table 2

| Corpus | cooc_P | cooc_R | cooc_F | relex_P | relex_R | relex_F |
| --- | --- | --- | --- | --- | --- | --- |
| AIMed | 0.17 / 0.17 | 0.95 / 1.00 ≠ | 0.29 / 0.29 | 0.40 / 0.40 | 0.50 / 0.50 | 0.44 / 0.44 |
| BioInfer | 0.13 / 0.26 ≠ | 0.99 / 1.00 ≠ | 0.23 / 0.42 ≠ | 0.39 / 0.59 ≠ | 0.45 / 0.30 ≠ | 0.41 / 0.40 ≠ |
| HPRD50 | 0.38 / 0.38 | 1.0 / 1.0 | 0.55 / 0.55 | 0.76 / 0.72 ≠ | 0.64 / 0.61 ≠ | 0.69 / 0.66 ≠ |
| IEPA | 0.41 / 0.41 | 1.0 / 1.0 | 0.58 / 0.58 | 0.74 / 0.70 ≠ | 0.61 / 0.53 ≠ | 0.67 / 0.60 ≠ |
| LLL | 0.50 / 0.50 | 1.0 / 1.0 | 0.66 / 0.66 | 0.82 / 0.93 ≠ | 0.72 / 0.68 ≠ | 0.77 / 0.78 ≠ |

### Table 3

| Corpus | tokens | entities | entity_pairs | interactions | no_entities | no_interactions |
| --- | --- | --- | --- | --- | --- | --- |
| AIMed | 25.2 / 25.2 | 2.2 / 2.2 | 3.0 / 3.0 | 0.5 / 0.5 | 0.18 / 0.18 | 0.69 / 0.71 ≠ |
| BioInfer | 31.3 / 31.3 | 4.2 / 4.0 ≠ | 9.4 / 8.8 ≠ | 1.3 / 2.3 ≠ | 0.00 / 0.00 | 0.48 / 0.29 ≠ |
| HPRD50 | 26.1 / 26.1 | 2.8 / 2.8 | 3.0 / 3.0 | 1.1 / 1.1 | 0.00 / 0.00 | 0.38 / 0.38 |
| IEPA | 32.2 / 32.2 | 2.3 / 2.3 | 1.7 / 1.7 | 0.7 / 0.7 | 0.00 / 0.00 | 0.37 / 0.37 |
| LLL | 29.6 / 29.6 | 3.1 / 3.1 | 4.3 / 4.3 | 2.1 / 2.1 | 0.00 / 0.00 | 0.00 / 0.00 |

### Table 4

| Corpus | cooc_P | cooc_F | relex_P | relex_F |
| --- | --- | --- | --- | --- |
| AIMed | 0.53 / 0.54 ≠ | 0.68 / 0.70 ≠ | 0.85 / 0.89 ≠ | 0.63 / 0.64 ≠ |
| BioInfer | 0.53 / 0.49 ≠ | 0.70 / 0.65 ≠ | 0.78 / 0.73 ≠ | 0.57 / 0.43 ≠ |
| HPRD50 | 0.64 / 0.64 | 0.78 / 0.78 | 0.93 / 0.88 ≠ | 0.76 / 0.72 ≠ |
| IEPA | 0.88 / 0.88 | 0.94 / 0.94 | 1.00 / 1.00 | 0.75 / 0.69 ≠ |
| LLL | 0.50 / 0.50 | 0.66 / 0.66 | 0.82 / 0.93 ≠ | 0.77 / 0.78 ≠ |

## Claims in the text

| Statistic | Paper text | From published tables | Ours | Ours with the paper's BioInfer row |
| --- | --- | --- | --- | --- |
| method_gap_pts | 13 | 13.4 | 8.19 | 11.5 |
| relex_pairwise_pts | 19 | 19.4 | 19.5 | 19.2 |
| relex_pairwise_filtered_pts | 11 | 10.6 | 15.7 | 10.1 |
| cooc_pairwise_pts | NA | 23 | 18.2 | 23.1 |
| error_reduction_min_pct | 21 | 21.1 | -2.31 | 4.07 |
| error_reduction_max_pct | 32 | 32.4 | 35 | 35 |
| cooc_beats_relex_filtered_n | NA | 4 | 4 | 4 |
| cooc_beats_relex_filtered_all_but_LLL | 1 | 1 | 1 | 1 |
| kendall_IEP_tau | NA | 0.8 | 0.6 | 0.8 |
| kendall_IEP_p | 0.08 | 0.0833 | 0.233 | 0.0833 |
| kendall_noint_tau | NA | -0.6 | -0.2 | -0.6 |
| kendall_noint_p | NA | 0.233 | 0.817 | 0.233 |

## Figures

| Figure | Render | Mean abs. grey diff. | Pixels within ±24 | Chamfer (px) | Global shift |
| --- | --- | --- | --- | --- | --- |
| 1 | ours | 6.414 | 94.18% | 1.476 | 0, 0 |
| 1 | published-values | 4.52 | 95.33% | 0.36 | 0, 0 |
| 2 | ours | 7.075 | 93.27% | 1.268 | 0, 0 |
| 2 | published-values | 4.46 | 95.3% | 0.212 | 0, 0 |

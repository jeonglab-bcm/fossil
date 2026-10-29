# Rebuilt ASH against Additional File 3

138 pairs: each of the 69 queries against its false positive and its true template.

| Quantity | Correlation | Median difference | Note |
| --- | --- | --- | --- |
| NER | 0.972 | 3.63 | ours higher by 3.46 on average; 0 pairs more than 10 lower, 15 more than 10 higher |
| SAS, all aligned pairs | 0.707 | 2.76 | |
| SAS, pairs within 8 Å | 0.855 | 0.28 | |
| Sequence identity, % of aligned pairs | 0.573 | 1.76 | |
| Score from eq. 1 on published NER and SAS, NER_rel in percent | 0.976 | | published = 10.678 x eq. 1 -11.06 |
| Same, NER_rel as a fraction | 0.762 | | |
| Score from eq. 1, every term rebuilt | 0.783 | | published = 8.784 x eq. 1 -9.77 |

False positive scoring above the true template: published 62 of 69 rows, rebuilt 38; the same order in 45.

## Check

Eq. 1 on the published NER and SAS stays at r >= 0.97, and our NER at r >= 0.95.

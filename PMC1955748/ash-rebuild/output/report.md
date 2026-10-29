# Rebuilt ASH against Additional File 3

138 pairs: each of the 69 queries against its false positive and its true template.

| Quantity | Correlation | Median difference | Note |
| --- | --- | --- | --- |
| NER | 0.972 | 3.14 | ours higher by 3.85 on average; 1 pairs more than 10 lower, 12 more than 10 higher |
| SAS, all aligned pairs | 0.727 | 2.58 | |
| SAS, pairs within 8 Å | 0.853 | 0.28 | |
| Sequence identity, % of aligned pairs | 0.671 | 1.6 | |
| Score from eq. 1 on published NER and SAS, NER_rel in percent | 0.977 | | published = 10.608 x eq. 1 -10.87 |
| Same, NER_rel as a fraction | 0.764 | | |
| Score from eq. 1, every term rebuilt | 0.796 | | published = 9.064 x eq. 1 -11.83 |

False positive scoring above the true template: published 62 of 69 rows, rebuilt 44; the same order in 51.

## Check

Eq. 1 on the published NER and SAS stays at r >= 0.97, and our NER at r >= 0.95.

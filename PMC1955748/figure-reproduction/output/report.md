# PMC1955748 reproduction report

| Item | Paper | Ours |
| --- | --- | --- |
| Additional File 2 transcription | image of 210 values | 884 glyphs, 0 closer to another character than to their own |
| Training set (Additional File 1) | 2911 sequence-unique domains | 2911 IDs, 2911 unique, 2911 in CATH 3.0.0 |
| CATH and SCOP domains compared, equivalent (75% of the larger) | 63,010, 43,773 | 71578 CATH domains (62816 SCOP domains) in 23344 shared PDB entries; 51173 equivalent |
| Training domains without a SCOP 1.69 equivalent | 0 (all were chosen from equivalent domains) | 12 under the stated rule, 1 under 75% of the smaller domain |
| Queries with a template of the same CATH topology and SCOP fold | 1,641 | 2325 (of the 2899 with a SCOP fold) |
| Additional File 3 rows (top template false) | 69 | 69 |
| Additional File 3 domain lengths equal to CATH 3.0.0 |  | 207 of 207 |
| Additional File 3 true negatives with same topology and fold |  | 69 of 69 |
| Additional File 3 false positives with different topology and fold | all ("according to both") | 63 of 69 |
| Additional File 3 false positive scoring above the true negative | all | 62 of 69 |
| ASH matrix vs BLOSUM62 (1/3 bit, AF4's axis): slope, r | .52, .94 | 0.286, 0.925 (Additional File 2) |
| Additional File 4 black diagonal points vs Additional File 2 | same matrix | CC: 9.24 vs 9.27; WW: 8.49 vs 7.12; YY: 5.83 vs 4.27 |
| AAindex entries | 98 | 94 (AAindex2 today) |
| Closest AAindex matrix by dot product | Gonnet (.89) | CROG050101 (0.953); Gonnet 0.933, rank 6 |
| Closest AAindex matrix by RMSD | SDM (.13) | same order as the dot product for unit-length matrices; no tried normalization gives Gonnet first by dot product and SDM first by RMSD |
| Table 2, CPU/Align = CPU (s) / 2071 | 6.2, 1.8, 1.5, .69, .31 | 6.226, 1.788, 1.544, 0.688, 0.311 |
| Table 2, Rel. to FAST | 20, 5, 5, 2, 1 | 19.99, 5.74, 4.96, 2.21, 1.0 |
| Test-set pairs, 2930 domains | 4,298,905 (abstract); 2930 x 2929/2 (text) | 4290985 |
| LASH CPU, 891 h over 2930 x 2930 pairs | .37 s per alignment | 0.3736 |
| Reduced training set, 2911 minus 2514 removed | 1397 | 397 |

## Check

Every result is as recorded.

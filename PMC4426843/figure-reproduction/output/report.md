# PMC4426843 reproduction check

| Item | Quantity | Paper | Ours | Match | Note |
| --- | --- | --- | --- | --- | --- |
| GO universe | human genes | 15733 | 15733 | yes |  |
| GO universe | S1 terms with equal size | 9462 | 9462 | yes |  |
| GO universe | ion transport (GO:0006811) size | 327 | 327 | yes |  |
| S1 | P-values equal (floor of mean) | 9462 | 9462 | yes |  |
| S1 | P-values equal (rounded mean) |  | 3716 | no | the caption's rule |
| Table 1 | rows equal at 3 digits, from S1 means | 10 | 10 | yes |  |
| Table 1 | paper's top 10 in our top 10 (our null) | 10 | 10 | yes |  |
| Table 1 | paper's top 10 in our top 20 (our null) | 10 | 10 | yes |  |
| Fig. 1 | ion transport mean targets, 39 random miRNAs | 250.6 | 250.57 | yes | Section 3.1 text: 250 |
| Fig. 1 | hypergeometric P of the mean | 5.97e-07 | 5.97e-07 | yes | text: 5.97e-07 |
| S1 | Pearson r of empirical means, ours vs S1 | 1 | 1.0 | yes |  |
| S3 | study-gene target pairs found | 155795 | 155595 | yes | 99.8716% |
| S3 | target genes not in S3 | 0 | 0 | yes |  |
| S3 | lists with identical target sets | 29 | 3 | no |  |
| S3 | Sokolov targets (n of Section 3.1) | 10057 | 10043 | no |  |
| Table 2 | Human lists with any significant term, basic | 5 of 22 | 6 of 22 | no |  |
| Table 2 | Mouse lists with any significant term, basic | 0 of 7 | 0 of 7 | yes |  |
| Table 2 | lists with the same zero/non-zero call, basic | 29 | 28 | no |  |
| Table 2 | Chen (176 miRNAs), basic | 6017 | 6010 | no | -0.1% |
| Table 2 | Collino (11 miRNAs), basic | 0 | 1 | no |  |
| Table 2 | Romero-Cordoba (130 miRNAs), basic | 5573 | 5550 | no | -0.4% |
| Table 2 | Sanchez-Diaz (26 miRNAs), basic | 2502 | 2499 | no | -0.1% |
| Table 2 | Tanic (46 miRNAs), basic | 3353 | 3360 | no | +0.2% |
| Table 2 | Wu (25 miRNAs), basic | 2480 | 2473 | no | -0.3% |
| Table 2 | Human lists with any significant term, multi-hit | 9 of 22 | 9 of 22 | yes |  |
| Table 2 | Mouse lists with any significant term, multi-hit | 2 of 7 | 1 of 7 | no |  |
| Table 2 | lists with the same zero/non-zero call, multi-hit | 29 | 28 | no |  |
| Table 2 | Chartoumpekis (10 miRNAs), multi-hit | 17 | 17 | yes | +0.0% |
| Table 2 | Chen (176 miRNAs), multi-hit | 1193 | 1300 | no | +9.0% |
| Table 2 | Chen2 (15 miRNAs), multi-hit | 6 | 5 | no | -16.7% |
| Table 2 | Liu (27 miRNAs), multi-hit | 1 | 0 | no | -100.0% |
| Table 2 | Munch (10 miRNAs), multi-hit | 22 | 72 | no | +227.3% |
| Table 2 | Raponi (15 miRNAs), multi-hit | 239 | 120 | no | -49.8% |
| Table 2 | Romero-Cordoba (130 miRNAs), multi-hit | 206 | 266 | no | +29.1% |
| Table 2 | Sanchez-Diaz (26 miRNAs), multi-hit | 28 | 31 | no | +10.7% |
| Table 2 | Sokolov (39 miRNAs), multi-hit | 337 | 842 | no | +149.9% |
| Table 2 | Tanic (46 miRNAs), multi-hit | 317 | 526 | no | +65.9% |
| Table 2 | Wu (25 miRNAs), multi-hit | 138 | 192 | no | +39.1% |
| S5 | target genes of the 8 miRNAs | 1064 | 1049 | no |  |
| S5 | significant terms (BH 0.05) | 1580 | 1552 | no |  |
| S5 | significant in both | 1580 | 1551 | no |  |
| S5 | regulation of axonogenesis significant | True | True | yes |  |
| Fig. 1 drawing | chamfer distance, all ink (px), published-values | 0 | 0.126 | yes |  |
| Fig. 1 drawing | pixels within 24 grey levels (%), published-values | 100 | 97.86 | yes |  |
| Fig. 1 drawing | chamfer distance, all ink (px), ours | 0 | 0.13 | yes |  |
| Fig. 1 drawing | pixels within 24 grey levels (%), ours | 100 | 97.85 | yes |  |

## Claims that must hold

- All hold.
- No committed targets_vs_s3.csv to compare with.
- No committed table1.csv to compare with.
- No committed table2.csv to compare with.
- No committed axonogenesis.json to compare with.

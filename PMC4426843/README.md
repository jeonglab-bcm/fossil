# PMC4426843 — Bias in microRNA functional enrichment analysis (Bleazard et al. 2015)

Bleazard T, Lamb JA, Griffiths-Jones S. Bias in microRNA functional enrichment analysis.
*Bioinformatics* 31(10):1592–1598 (2015).
[doi:10.1093/bioinformatics/btv023](https://doi.org/10.1093/bioinformatics/btv023) ·
[PMC4426843](https://pmc.ncbi.nlm.nih.gov/articles/PMC4426843/)

The paper is © The Author 2015, published by Oxford University Press under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). In keeping with the rest of this
repository, this folder does not contain the paper or its full text.
`figure-reproduction/published/figure-1.jpg` is the paper's Figure 1, and
`figure-reproduction/pipeline/inputs/s*.tsv` are Supplementary Tables S1–S5 converted to TSV.
Both are redistributed under CC BY 4.0 with the attribution above.

miRBase 20 and Ensembl 75 are downloaded by the pipeline and checked against SHA-256 sums; they
are not redistributed. `figure-reproduction/pipeline/inputs/sites_{hsa,mmu}.txt.xz` are our own
miRanda predictions (gene-level site counts), computed from them.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | Figure 1, Tables 1 and 2 and the Supplementary Table S1, S3 and S5 checks, rerun with regenerated miRanda 3.3a predictions on miRBase 20 and Ensembl 75 and a rebuilt empirical test. Figure 1 drawn with base R on the published pixel grid. Nextflow pipeline. |

## Results

| Item | Status | Evidence |
| --- | --- | --- |
| GO universe | Identical data | Ensembl 75 BioMart dumps, by gene name, direct annotations: 15,733 human genes and all 9,462 S1 term sizes equal (ion transport 327). |
| Table 1, from S1 | Identical arithmetic | All 9,462 S1 P-values to 1e-13, with the empirical mean truncated (`floor`), not rounded as the caption says (3,716 of 9,462 with rounding). All 10 Table 1 values at the printed precision. |
| Table 1, our null | Same setup | The paper's 10 terms are our top 10 (ranks 8 and 9 swapped); 7 of 10 P-values identical. Our empirical means against S1's: Pearson r = 1.0000, median relative difference −0.008% (terms with mean ≥ 10). |
| miRanda targets (S3) | Same setup, 99.87% | 155,595 of S3's 155,795 study–gene pairs over the 29 lists; none of ours outside S3. 3 lists identical (Cheng, Keck-Wherley, Schonrock); Sokolov 10,043 of 10,057. |
| Fig. 1 | Same setup | Ion-transport mean of 39 random miRNAs 250.57 (paper 250.60); hypergeometric P 5.97e-07 (paper 5.97e-07). Drawn with base R on the published grid: chamfer distance 0.13 px with our data and with the paper's bar heights. |
| Table 2, basic | Same setup | 28 of 29 zero/non-zero calls agree; the 5 large lists within 0.4% (Chen 6,010 vs 6,017). Collino gets 1 term against 0, so 6 of 22 human lists have an enriched term (paper 5); 0 of 7 mouse (paper 0). |
| Table 2, multi-hit | Not reproducible from the Methods | 28 of 29 zero/non-zero calls agree (Liu 0 vs 1); counts differ in both directions, by up to 3.3× (Munch 72 vs 22, Raponi 120 vs 239). The paper does not define the site counts and no supplement records them; six readings of the method and a second seed do not reproduce the counts, and Chartoumpekis's exact match is chance (17 → 3 under another seed). The multi-hit test supports only a secondary point; the main claim rests on the basic test. See `figure-reproduction/README.md`, "Why the multi-hit counts differ". |
| S5 positive control | Same setup | 1,551 of S5's 1,580 significant terms are significant in ours (ours 1,552); 'regulation of axonogenesis' significant in both. |
| Main claim | Holds | Random miRNA sets give hypergeometric P ≈ 1e-28 to 1e-11 for common terms; after correction 6/22 human and 0/7 mouse published lists have any enriched term (paper 5/22, 0/7). |
| Table 3 (rice) | Not reproduced | psRNATarget's 2011 server and the agriGO tables are gone; psRNATarget V2 scores differently. |
| Section 3.3 robustness (KEGG, intersection, CLIP, BP_FAT) | Not reproduced | Text and S2 only; PITA v6, DIANA-microT-v4, the starBase v2 CLIP sets and DAVID 6.7's BP_FAT are no longer available as used. |

Kept local and gitignored: `sources/` (the paper's full text, figure and supplement), `work/`
(downloads, miRanda output, scratch runs and Slurm logs) and `.env/` (the conda environment).

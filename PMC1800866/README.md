# PMC1800866: Predicting zinc binding at the proteome level (Passerini et al. 2007)

Passerini A, Andreini C, Menchetti S, Rosato A, Frasconi P. Predicting zinc binding at the proteome level.
*BMC Bioinformatics* 8:39 (2007).
[doi:10.1186/1471-2105-8-39](https://doi.org/10.1186/1471-2105-8-39) ·
[PMC1800866](https://pmc.ncbi.nlm.nih.gov/articles/PMC1800866/) · issue #19

The paper is © 2007 Passerini et al., licensee BioMed Central, under
[CC BY 2.0](https://creativecommons.org/licenses/by/2.0/). In keeping with the rest of this repository,
this folder does not contain the paper, its full text or its supplements; the pipeline downloads them.
`figure-reproduction/published/` holds the paper's nine figures (the JPEGs PMC serves, and Figs 3 to 6
rendered at 600 dpi from the PDF) for comparison, redistributed under CC BY 2.0 with the attribution above.

The authors' predictor (Zinc Finder, C++) is lost. We implemented the SP-SVM from the paper's text as the
Python package [`package/`](package/) (`spsvm`) and reran it on the paper's own evaluation sets
(Additional file 1: every residue, label, LOO set and CV fold, and the tuned parameters).

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | Tables 1 to 3 and Figs 1 and 2 from today's PDB files; the LOO and five-fold CV of Figs 3 to 6 with our profiles; the proteome sample scan; Figs 8 and 9's probabilities; Nextflow pipeline and cluster scripts. |
| [`package/`](package/) | `spsvm`, the SP-SVM as an installable Python package, with example data, tests and an [executed tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every figure panel, table and number of the paper, with our values and computed verdicts. |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

Results page: <https://jeonglab-bcm.github.io/fossil/PMC1800866/>

## Results

<!-- generated from results.json by check_results.py --markdown; summary below -->

38 results: 2 exact, 6 agree, 14 partly agree, 5 inconclusive, 6 differ, 5 not attempted
(`python3 figure-reproduction/pipeline/check_results.py results.json --markdown` prints the full table).

| Result | Verdict | Ours against the paper |
| --- | --- | --- |
| Main claim: gated beats local | exact | Yes in LOO and CV, on C and on H; overall by more than the two standard errors (9 of 9 comparisons). On LOO histidines alone the AUC gap (0.017) is below the two SEs (0.025). |
| LOO, AUC | partly | 0.893 ± 0.007 and 0.913 ± 0.007 against 0.895 ± 0.007 and 0.914 ± 0.006 |
| LOO, AURPC | partly | 0.678 and 0.709 against 0.590 and 0.633 |
| CV, AUC and AURPC | partly | AUC 0.852 and 0.877 against 0.867 and 0.890; AURPC 0.494 and 0.552 against 0.428 and 0.500 |
| D and E (SPCHDE-SVM) | partly | LOO 0.74 ± 0.03 and 0.70 ± 0.06 as printed; CV 0.70 and 0.63 against 0.73 and 0.65 |
| Protein level | exact | Zn4 chains easiest; SPCHDE better than SPCH on Zn3, in LOO and CV |
| Table 1 | partly | 11 of 21 values; the 11 multiple-site-type counts exactly; 450 sites in 295 chains against 464 in 305 |
| Tables 2 and 3, Fig. 2 | partly | Short by the sites of the chains Additional file 1 does not list (mostly Zn4) |
| Fig. 1 | agrees | 95% (a) and 87% (b) of our curve within 2 px of the published one (96% and 99% the other way); best control 62% and 47% |
| Figs 3 to 6 | partly, inconclusive or differs | Our curves do not overlay the published ones at 2 px (8% to 39%) |
| Human proteome | differs | About 2,010 (SE 101) zinc proteins estimated from a 300-protein sample, against 2,833 |
| Figs 8 and 9 | differs | Fig. 8: the same four cysteines ranked highest, at lower probabilities (CZIB 0.81, 0.82, 0.48, 0.54 against 0.90, 0.98, 0.67, 0.82) |
| Later structures | agrees | 5ZLQ (2018) binds zinc with exactly Fig. 8's four cysteines; 2HD5 has the UBP family's CX2CX43CX2C site |
| Text arithmetic | agrees | 29 of 29 claims come back from the paper's own tables and Additional file 3 (one rounding slip in Table 2) |
| Fig. 7, reliability counts | not attempted | Need Andreini et al. 2006's paywalled per-protein reliability levels |

The paper's main claim holds: the gated predictor beats the local one in both tests, on cysteines and on
histidines, and overall by more than the error bars. The AURPCs, the proteome count and the single probabilities
do not come back; the likely causes, still open, are our 2010 profiles in place of the lost 2005 ones and the
Platt constants tuned on those.

Kept local and gitignored: `sources/` (the paper, its supplements, the structures and the human proteome),
`work/` (the BLAST database, PSSMs, Slurm logs and scratch runs) and `.venv/`.

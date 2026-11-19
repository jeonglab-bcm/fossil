# PMC3446288: Mammalian tissues defective in nonsense-mediated mRNA decay display highly aberrant splicing patterns (Weischenfeldt et al. 2012)

Weischenfeldt J, Waage J, Tian G, Zhao J, Damgaard I, Jakobsen JS, Kristiansen K, Krogh A, Wang J,
Porse BT. Mammalian tissues defective in nonsense-mediated mRNA decay display highly aberrant splicing
patterns. *Genome Biology* 13(5):R35 (2012).
[doi:10.1186/gb-2012-13-5-r35](https://doi.org/10.1186/gb-2012-13-5-r35),
[PMC3446288](https://pmc.ncbi.nlm.nih.gov/articles/PMC3446288/), issue
[jeonglab-bcm/fossil#91](https://github.com/jeonglab-bcm/fossil/issues/91).

The paper is © 2012 Weischenfeldt et al.; licensee BioMed Central Ltd, published under the
[Creative Commons Attribution License 2.0](https://creativecommons.org/licenses/by/2.0/). This folder
does not contain the paper, its supplements or its full text; `figure-reproduction/published/` holds
Figs 1a, 2a, 3, 5, 6 and 7 and Figs S2, S4 and S5 (converted to PNG, unchanged otherwise) for
comparison, under that licence and with this attribution.

The paper mapped RNA-seq of Upf2 knockout and wild-type mouse liver and bone-marrow macrophages to
mm9 and to a combinatorial exon-exon junction database, called premature termination codons (PTCs)
by the 50-nucleotide rule and sorted splicing into seven classes. Its pipeline, RAINMAN, lived only on
a lab web page that is gone. We rebuilt it from the paper and Additional file 1 as the Python package
[`package/`](package/) (`nmdsplice`), rebuilt the junction database from today's UCSC mm9 tables, mapped
the four SRA runs (62 million reads) with Bowtie, took the TopHat junctions from the authors' own
TopHat alignments in GEO, and redid every table and figure with computed results.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | The Nextflow pipeline: downloads, junction database, mapping, PTC calls, splice classes, conservation, every table, figure and claim, and the check against the committed outputs. |
| [`package/`](package/) | `nmdsplice`, the method as an installable Python package, with example data, tests and a [tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every figure, table and claim of the paper, with our values and computed verdicts. |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

Results page: <https://jeonglab-bcm.github.io/fossil/PMC3446288/>

Install the package: `pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC3446288/package"`.

## Results

<!-- summary and table from results.json (check_results.py --markdown); do not edit by hand -->
<!--RESULTS-SUMMARY-->
3 agrees, 12 partly, 1 inconclusive, 20 differs, 9 not attempted; 30 open causes.

| Item | Verdict | Measure |
| --- | --- | --- |
| Text (Additional file 1): 5,574,728 junctions in the combinatorial database | differs | 0 of 1 fields as printed |
| Fig. 1a, reads by category and mapping frequency | differs | 0 of 24 fields as printed |
| Fig. 1b, Upf2 locus in the UCSC browser | not attempted | not attempted |
| Text: 84% mapped, 28% on junctions, 323,474 and about 150,000 junctions, 4 to 7% by truncation, 11 to 16% by TopHat | partly | 1 of 8 fields as printed |
| Text (Additional file 1): reads recovered by truncation | differs | 0 of 4 fields as printed |
| Text (Additional file 1): TMM normalisation factors | differs | 0 of 4 fields as printed |
| Table S1, junctions from the combinatorial database, TopHat or both | differs | 0 of 16 fields as printed |
| Table S2, TopHat contribution to all and PTC+ junctions | differs | 0 of 12 fields as printed |
| Text (Additional file 1): junctions and genes removed by the PTC filters | differs | 0 of 8 fields as printed |
| Fig. 2a, regulated junctions and genes, all and PTC+ | partly | 4 of 72 fields as printed |
| Text: junction counts, junctions per gene, PTC+ share up-regulated, genes affected, chi-square | partly | 3 of 10 fields as printed |
| Text: 516 up-regulated PTC+ junctions shared by both tissues, in 448 genes | differs | 0 of 2 fields as printed |
| Text and Table S3: GO top cluster of the core targets, mRNA processing, P 9.0e-18 | not attempted | not attempted |
| Fig. 2b and Table S4, GO terms of tissue-unique PTC+ genes | not attempted | not attempted |
| Fig. 3a, regulation of canonical and AS junctions and their PTC+ share | partly | 7 of 24 fields as printed |
| Text: about 10,000 and 35,000 AS junctions; NMD degrades 16% and 18% of AS | differs | 0 of 3 fields as printed, 1 paper errors |
| Fig. 3b, AS junctions per sample, per million junction reads, and slopes | differs | 0 of 18 fields as printed |
| Table 1, splice events and PTC+ classification | differs | 0 of 58 fields as printed |
| Text: dPSI of Mgea5, Tmem183a, Rps12, Smg5 and Srsf9; Soat2 fold change | differs | 0 of 11 fields as printed |
| Fig. 4a and 4d, schematics of the classes and of Pkm2 | not attempted | not attempted |
| Fig. 4b, 4c and Fig. S3: RT-PCR (49 of 50 events), western blots, qPCR (R = 0.975), Srsf9 cloning | not attempted | not attempted |
| Table S5, gene and canonical fold changes of 25 splice factors | partly | 1 of 77 fields as printed |
| Text: of 19 liver factors with AS-NMD, 10 deregulated more than 1.5-fold (5 up, 5 down) | partly | 1 of 4 fields as printed |
| Table S7, PTC-upon-inclusion SES events up in both tissues | differs | 0 of 1 fields as printed |
| Table S8, PTC-upon-exclusion SES events up in both tissues | differs | 0 of 2 fields as printed |
| Fig. 5a, conservation around exclusion events, liver | inconclusive | 40.36% within 3 px (pass 90.0%, best control 44.3%) |
| Fig. 5b, conservation around inclusion events, liver | differs | 31.37% within 3 px (pass 90.0%, best control 39.8%) |
| Fig. 5 caption: events per group, liver, and mm9 RefSeq exons | differs | 0 of 6 fields as printed |
| Fig. S4, conservation around SES events, BMM (event counts) | differs | 0 of 6 fields as printed |
| Text: conservation of regulated SES exons and introns (Kolmogorov-Smirnov) | partly | 4 of 7 fields as printed |
| Fig. 6, PTC+/PTC- ratio by junction RPKM | differs | 0.04% within 3 px (pass 90.0%, best control 0.0%) |
| Text: PTC+ fraction higher in liver and at low expression | partly | 3 of 4 fields as printed |
| Fig. 7a, conservation at PTCs and normal stops minus random exons | differs | 0.00% within 3 px (pass 90.0%, best control 1.1%) |
| Figs 7a and S5 captions: PTC+ and RefSeq stop positions | differs | 0 of 3 fields as printed |
| Fig. 7b, stop codon identity | partly | 20 of 23 fields as printed |
| Fig. S2a, stop to 3' end, stops in the last exon (50-nt bins) | partly | 13 of 42 fields as printed |
| Fig. S2b, stop to the next junction, stops in the second-to-last exon (2-nt bins) | partly | 35 of 52 fields as printed |
| Text (Additional file 1): mapping simulation, 830,000 reads, R2 0.93, 93.73% mapped, 89.12% correct | not attempted | not attempted |
| Table S6, manual check of the class calls in 62 genes | not attempted | not attempted |
| Text (Additional file 1): RNA-seq against microarray, correlation about 0.63 | not attempted | not attempted |
| Fig. S1 (Pion browser view, pipeline diagram) and Table S9 (primers) | not attempted | not attempted |
| PTC detection against the paper's PTC distances (Additional files 8 and 9) | partly | 58 of 76 fields as printed |
| TMM in nmdsplice against edgeR on our junction counts | agrees | nmdsplice.tmm_factors and edgeR 4.4.0 calcNormFactors on our junction counts (252,921 junctions, BMM and liver pairs) matrix: largest difference 3.4e-11 (ours 0.9805, 1.0199, 0.7938, 1.2597) |
| The paper's claims recomputed from its own tables | agrees | 18 of 25 claims come back from the paper's own tables; the other 7 are slips in the paper: up junctions per gene, BMM 2.3; Table S2 BMM: TopHat share of all junctions 4%; Table S2 BMM: TopHat share of PTC+ junctions 20%; Table S2 Liver: TopHat share of all junctions 11%; Table S2 Liver: TopHat share of PTC+ junctions 24%; SES PTC+ share 40% (BMM) and 60% (liver), Table 1; PTC upon inclusion share of SES inclusion 40% BMM / 55% liver (320/573 = 55.8%) |
| Python package nmdsplice and its tutorial | agrees | nmdsplice 0.1.0: wheel installed in a fresh environment and imported from it; tests 5 passed; tutorial 5 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |
<!--/RESULTS-SUMMARY-->

The direction of the main finding holds on our run: losing NMD up-regulates PTC+ junctions and
alternative splicing far more often than canonical splicing, and the stops of regulated PTCs prefer
UGA. Many counts differ by more than a few per cent: the junction database is rebuilt from today's
annotation, liver maps more reads, and truncation recovers about twice as many. We call 24 to 28% of the
paper's PTC+ junctions, and counts built on them come back at 24 to 77% of the paper's. Why is open:
the junctions we must exclude because TROMER, one of the paper's exon sources, is gone are numerous
enough to explain the gap, but that is not shown.

## Kept local, not in the repository

`sources/` (the paper, supplements, SRA reads, mm9 genome and Bowtie index, UCSC tables, phastCons,
GEO TopHat alignments) and `work/` (scratch runs) are git-ignored. `fetch_inputs.sh` downloads them
and checks their SHA-256.

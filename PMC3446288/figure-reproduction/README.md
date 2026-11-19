# PMC3446288 figure reproduction

Weischenfeldt et al. (2012), every table, figure and number with computed results, from the Python
package `nmdsplice` ([`../package`](../package)), which rebuilds the lost RAINMAN pipeline from the
paper's text and Additional file 1. The paper is CC BY 2.0; `published/` holds its figures for
comparison (see [`published/README.md`](published/README.md)).

## Results

<!-- full table from ../results.json (check_results.py --markdown); do not edit by hand -->
<!--RESULTS-TABLE-->
3 agrees, 12 partly, 1 inconclusive, 20 differs, 9 not attempted; 30 open causes.

| Item | Verdict | Measure | Why |
| --- | --- | --- | --- |
| Text (Additional file 1): 5,574,728 junctions in the combinatorial database | differs | 0 of 1 fields as printed | 5,093,205 junctions against 5,574,728 (-8.6%): the rule is the paper's, the annotation versions are today's. The paper's 2011 RefSeq and Ensembl dumps are not available. |
| Fig. 1a, reads by category and mapping frequency | differs | 0 of 24 fields as printed | Mapped reads agree within 2% in BMM WT (8,114,319 against 8,240,605) but liver maps 99% against 88%, and more reads fall in introns and between genes than in the paper. How the paper classed reads is not stated. |
| Fig. 1b, Upf2 locus in the UCSC browser | not attempted | not attempted | A genome-browser screenshot; there is nothing to recompute. |
| Text: 84% mapped, 28% on junctions, 323,474 and about 150,000 junctions, 4 to 7% by truncation, 11 to 16% by TopHat | partly | 1 of 8 fields as printed | More reads map than in the paper (92% against 84%), mostly in liver, and truncation recovers about twice as many; the junction share (24.7% against 28%) and the TopHat-only share (8 to 16% against 11 to 16%) are close. 252,921 unique junctions against 323,474. |
| Text (Additional file 1): reads recovered by truncation | differs | 0 of 4 fields as printed | We recover 1.46 to 1.97 million reads per sample by truncation against 0.72 to 0.79 million. The paper does not say whether it trimmed both ends at each step or how it counted a read whose two halves map. |
| Text (Additional file 1): TMM normalisation factors | differs | 0 of 4 fields as printed | Normalising each tissue's WT and KO pair gives the paper's structure (each pair multiplies to 1.000), but the factors differ: BMM 0.980 and 1.020 against 0.998 and 1.002; liver 0.794 and 1.260 against 1.188 and 0.841. |
| Table S1, junctions from the combinatorial database, TopHat or both | differs | 0 of 16 fields as printed | BMM totals are within 4% (130,518 against 135,307) and Both is close; liver finds far fewer database-only junctions (41,032 against 89,890), so the liver totals are 26% lower. The TopHat arm is the authors' own. |
| Table S2, TopHat contribution to all and PTC+ junctions | differs | 0 of 12 fields as printed | We call fewer PTC+ junctions than the paper: 28% of its count in BMM (1,139 against 4,047) and 24% in liver (3,446 against 14,387); counts built on them come back at 24% to 77% of the paper's. Our PTC rule and the false-positive filter do not explain the gap. Junctions we must exclude as unannotated (no TROMER) are numerous enough to explain it, but that is not shown. |
| Text (Additional file 1): junctions and genes removed by the PTC filters | differs | 0 of 8 fields as printed | Without TROMER we exclude 1.7 to 4.0 times as many junctions as unannotated; the paper gives no threshold for its false-positive gene filter, and ours removes 251 and 269 genes against 118 and 190. |
| Fig. 2a, regulated junctions and genes, all and PTC+ | partly | 4 of 72 fields as printed | All junctions in BMM come back within 7% (up, unregulated and down 14,145, 70,924, 12,020 against 14,056, 72,499, 11,311) and common up within 2% (2,226 against 2,257); liver is 8% low for up and 14% low for down. The PTC+ rows are 13% to 54% of the paper's, from the PTC calls (see Table S2), and 'common unregulated' counts junctions the paper did not count as common. |
| Text: junction counts, junctions per gene, PTC+ share up-regulated, genes affected, chi-square | partly | 3 of 10 fields as printed | We call fewer PTC+ junctions than the paper: 28% of its count in BMM (1,139 against 4,047) and 24% in liver (3,446 against 14,387); counts built on them come back at 24% to 77% of the paper's. Our PTC rule and the false-positive filter do not explain the gap. Junctions we must exclude as unannotated (no TROMER) are numerous enough to explain it, but that is not shown. |
| Text: 516 up-regulated PTC+ junctions shared by both tissues, in 448 genes | differs | 0 of 2 fields as printed | We call fewer PTC+ junctions than the paper: 28% of its count in BMM (1,139 against 4,047) and 24% in liver (3,446 against 14,387); counts built on them come back at 24% to 77% of the paper's. Our PTC rule and the false-positive filter do not explain the gap. Junctions we must exclude as unannotated (no TROMER) are numerous enough to explain it, but that is not shown. |
| Text and Table S3: GO top cluster of the core targets, mRNA processing, P 9.0e-18 | not attempted | not attempted | DAVID's 2012 knowledgebase is not available, and the paper does not give the DAVID version, background or settings. |
| Fig. 2b and Table S4, GO terms of tissue-unique PTC+ genes | not attempted | not attempted | As for the core targets: DAVID's 2012 knowledgebase and settings are not available. |
| Fig. 3a, regulation of canonical and AS junctions and their PTC+ share | partly | 7 of 24 fields as printed | Regulation of canonical and AS junctions agrees in BMM to 2 points (AS up 33% against 35%); the PTC+ share of up-regulated AS junctions is about half the paper's (20% against 47%; liver 24% against 45%), from the PTC calls. |
| Text: about 10,000 and 35,000 AS junctions; NMD degrades 16% and 18% of AS | differs | 0 of 3 fields as printed, 1 paper errors | With no read cutoff, as the Fig. 3b caption says, we count 48,787 AS junctions in BMM against about 10,000; with three reads we count 9,633 (BMM) but 19,240 in liver against 33,164. The NMD shares follow from the PTC calls. |
| Fig. 3b, AS junctions per sample, per million junction reads, and slopes | differs | 0 of 18 fields as printed | AS junction counts depend on the read cutoff the caption says was not used: without one we find 1.5 to 3.7 times as many per sample; with three reads per sample, 5,783 and 8,190 in BMM against 8,107 and 9,447. Slopes are lower (BMM AS 0.26 against 0.35); liver KO has the steepest slope, as in the paper. |
| Table 1, splice events and PTC+ classification | differs | 0 of 58 fields as printed | We find fewer regulated events with the three-read evidence rule (BMM ES 275 against 730) and far more without it (2,255). The share of ES events that are PTC+ comes back (BMM 37% against 38%), the other classes' PTC+ shares are lower (PTC calls), and MXE is rare under our stricter rule. |
| Text: dPSI of Mgea5, Tmem183a, Rps12, Smg5 and Srsf9; Soat2 fold change | differs | 0 of 11 fields as printed | Tmem183a comes back (dPSI 49% and 57% against 51% and 54%) and Srsf9 rises in liver (45%, against the paper's -40%, which for a PTC-upon-inclusion event has the wrong sign). Mgea5, Rps12 and Smg5 are not called as the class the paper names; the paper does not give their junctions (Mgea5's are in Additional file 9, but its skipped exon is not a single annotated exon in today's tables). |
| Fig. 4a and 4d, schematics of the classes and of Pkm2 | not attempted | not attempted | Diagrams; there is nothing to recompute. |
| Fig. 4b, 4c and Fig. S3: RT-PCR (49 of 50 events), western blots, qPCR (R = 0.975), Srsf9 cloning | not attempted | not attempted | Wet-lab experiments on tissue that is not available; nothing computational to rerun. |
| Table S5, gene and canonical fold changes of 25 splice factors | partly | 1 of 77 fields as printed | Gene fold changes of the 25 factors agree to about 10% (BMM Srsf6 1.32 against 1.31, Ptbp2 4.39 against 4.38); the canonical fold changes need the paper's 'major up-regulated PTC-eliciting event' per gene, which we find for fewer genes (PTC calls), so most are missing. |
| Text: of 19 liver factors with AS-NMD, 10 deregulated more than 1.5-fold (5 up, 5 down) | partly | 1 of 4 fields as printed | We find a PTC+ event for 8 of the liver factors against 19, and 5 of them are deregulated more than 1.5-fold (all down). The count follows from the PTC calls. |
| Table S7, PTC-upon-inclusion SES events up in both tissues | differs | 0 of 1 fields as printed | We call fewer PTC+ junctions than the paper: 28% of its count in BMM (1,139 against 4,047) and 24% in liver (3,446 against 14,387); counts built on them come back at 24% to 77% of the paper's. Our PTC rule and the false-positive filter do not explain the gap. Junctions we must exclude as unannotated (no TROMER) are numerous enough to explain it, but that is not shown. |
| Table S8, PTC-upon-exclusion SES events up in both tissues | differs | 0 of 2 fields as printed | We call fewer PTC+ junctions than the paper: 28% of its count in BMM (1,139 against 4,047) and 24% in liver (3,446 against 14,387); counts built on them come back at 24% to 77% of the paper's. Our PTC rule and the false-positive filter do not explain the gap. Junctions we must exclude as unannotated (no TROMER) are numerous enough to explain it, but that is not shown. |
| Fig. 5a, conservation around exclusion events, liver | inconclusive | 40.36% within 3 px (pass 90.0%, best control 44.3%) | The curves have the paper's shape (exons high, introns low) but the event groups are smaller and differently composed, and the score cannot tell ours from a curve shifted by 3 nt. |
| Fig. 5b, conservation around inclusion events, liver | differs | 31.37% within 3 px (pass 90.0%, best control 39.8%) | Inclusion events: ours scores below the exclusion events drawn in their place, so the comparison cannot confirm this panel. |
| Fig. 5 caption: events per group, liver, and mm9 RefSeq exons | differs | 0 of 6 fields as printed | Fewer SES events in most groups (liver exclusion PTC+ 310 against 439, unregulated 1,845 against 3,494), more in the inclusion groups (97 and 171 against 64 and 162); RefSeq exons 180,246 unique internal exons against 274,281. |
| Fig. S4, conservation around SES events, BMM (event counts) | differs | 0 of 6 fields as printed | As Fig. 5: fewer BMM events in most groups. |
| Text: conservation of regulated SES exons and introns (Kolmogorov-Smirnov) | partly | 4 of 7 fields as printed | The direction of every comparison but one comes back (regulated introns more conserved than unregulated, PTC- introns above PTC+ for exclusion); the P values are larger than the paper's 2.2e-16 with our smaller groups, and PTC- inclusion introns are not above PTC+ in liver. |
| Fig. 6, PTC+/PTC- ratio by junction RPKM | differs | 0.04% within 3 px (pass 90.0%, best control 0.0%) | Our curves fall with expression as the paper's do, but our PTC+ fraction lies well below the paper's at every expression level (the PTC calls), so no curve lies within 3 px. |
| Text: PTC+ fraction higher in liver and at low expression | partly | 3 of 4 fields as printed | Low-expressed junctions are enriched in PTC+ and KO lies above WT, as in the paper; liver lies below BMM in the two lowest bins (1 and 2 RPKM) and above it from 3 RPKM up. |
| Fig. 7a, conservation at PTCs and normal stops minus random exons | differs | 0.00% within 3 px (pass 90.0%, best control 1.1%) | Our curves lie below the paper's (no pixel within 3 px): the random-exon baseline (which exons, which window) is described in one sentence. |
| Figs 7a and S5 captions: PTC+ and RefSeq stop positions | differs | 0 of 3 fields as printed | We call fewer PTC+ junctions than the paper: 28% of its count in BMM (1,139 against 4,047) and 24% in liver (3,446 against 14,387); counts built on them come back at 24% to 77% of the paper's. Our PTC rule and the false-positive filter do not explain the gap. Junctions we must exclude as unannotated (no TROMER) are numerous enough to explain it, but that is not shown. |
| Fig. 7b, stop codon identity | partly | 20 of 23 fields as printed | The codon shares come back within 0.02 for 18 of 18 bars and UGA is preferred in both tissues (Fisher P 0.0065 and 4e-14); there are fewer junctions (196 and 504 against 497 and 670), from the PTC calls. |
| Fig. S2a, stop to 3' end, stops in the last exon (50-nt bins) | partly | 13 of 42 fields as printed | Today's RefSeq has more short 3' UTRs in the first bin (2,135 against about 600); after 100 nt our bars fall as the paper's do but run 10 to 20% lower, 13 of 42 bins within tolerance. |
| Fig. S2b, stop to the next junction, stops in the second-to-last exon (2-nt bins) | partly | 35 of 52 fields as printed | Same RefSeq version; the bars agree within tolerance in 35 of 52 bins and the cut at about 46 nt comes back. |
| Text (Additional file 1): mapping simulation, 830,000 reads, R2 0.93, 93.73% mapped, 89.12% correct | not attempted | not attempted | The simulated reads are not published and the simulation is described in one sentence (no error model, read placement or seed). |
| Table S6, manual check of the class calls in 62 genes | not attempted | not attempted | A manual inspection; there is nothing to recompute. |
| Text (Additional file 1): RNA-seq against microarray, correlation about 0.63 | not attempted | not attempted | The array data come from ref. 11 with no accession or probe mapping given. |
| Fig. S1 (Pion browser view, pipeline diagram) and Table S9 (primers) | not attempted | not attempted | A screenshot, a diagram and a primer list. |
| PTC detection against the paper's PTC distances (Additional files 8 and 9) | partly | 58 of 76 fields as printed | 58 of 76 events give the printed distance. Of the 18 misses, 5 lose their annotated start or have no coding model in today's tables, 7 are not called PTC+ (Arih2, Il4ra, Prpf38b, Rps9, Scaf1, Tra2b, Phkg2) and 6 give another distance (Luc7l, Rabggtb, Srsf6, Abhd10, Hsf1, Prei4); that these come from changed annotation is not shown. |
| TMM in nmdsplice against edgeR on our junction counts | agrees | nmdsplice.tmm_factors and edgeR 4.4.0 calcNormFactors on our junction counts (252,921 junctions, BMM and liver pairs) matrix: largest difference 3.4e-11 (ours 0.9805, 1.0199, 0.7938, 1.2597) |  |
| The paper's claims recomputed from its own tables | agrees | 18 of 25 claims come back from the paper's own tables; the other 7 are slips in the paper: up junctions per gene, BMM 2.3; Table S2 BMM: TopHat share of all junctions 4%; Table S2 BMM: TopHat share of PTC+ junctions 20%; Table S2 Liver: TopHat share of all junctions 11%; Table S2 Liver: TopHat share of PTC+ junctions 24%; SES PTC+ share 40% (BMM) and 60% (liver), Table 1; PTC upon inclusion share of SES inclusion 40% BMM / 55% liver (320/573 = 55.8%) |  |
| Python package nmdsplice and its tutorial | agrees | nmdsplice 0.1.0: wheel installed in a fresh environment and imported from it; tests 5 passed; tutorial 5 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |  |
<!--/RESULTS-TABLE-->

The direction of the main finding holds on our run: losing NMD up-regulates PTC+ junctions and
alternative splicing far more often than canonical splicing, and regulated PTCs prefer UGA. We call 24 to
28% of the paper's PTC+ junctions; the cause is open, and the lost TROMER exon set is the main suspect.

## What the code does, against the paper

| Step | Paper (Additional file 1) | Here |
| --- | --- | --- |
| Junction database | Exons of UCSC Known Genes, Ensembl, RefSeq, GENSCAN and Exoniphy in all combinations within each RefSeq gene, 4 nt overlap; 5,574,728 junctions | The same rule on today's UCSC mm9 dumps (refGene 2020, knownGene and ensGene 2011, GENSCAN and Exoniphy 2007): 5,093,205 junctions (`nmdsplice.junctiondb`) |
| Mapping | Bowtie 0.11.3, two mismatches in the first 68 bp, best stratum, genome and database together | Bowtie 1.0.0 (the oldest on Bioconda), the same settings; genome and database searched separately, the hit with fewer mismatches kept, the genome on a tie (`pipeline/map_sample.py`) |
| Truncation | Unmapped reads trimmed from either side in 10-nt steps to 35 nt and remapped | Both ends trimmed at each step; a read counts once when either half maps |
| TopHat | TopHat 1.0.14 | The authors' own TopHat 1.0.14 alignments from GEO GSE26561 (`pipeline/tophat_junctions.sh`) |
| Expression | Cufflinks RPKM (upper quartile); junction reads TMM-normalised (edgeR 1.6.12) and divided by the gene's fold change; >= 3 reads; two-fold | Upper-quartile RPKM of reads in the longest RefSeq model; TMM within each tissue (`nmdsplice.quant`, checked against edgeR 4.4.0); the rest as stated |
| PTC calls | Longest compatible RefSeq, then Ensembl, model; stop more than 49 nt before the last junction; exons from six repositories including TROMER; false-positive genes untagged | The same, without TROMER (no mouse data online); a gene is a false positive when its own model is called PTC+ (`nmdsplice.ptc`) |
| Classes and PSI | SES, MES, A5SS, A3SS, AFE, ALE, MXE; PSI formulas printed as equation objects | The class rules as code; PSI read as a proportion (`nmdsplice.classes`) |
| Conservation | phastCons30way mm9, mean per position, smoothing spline | The same (`pipeline/conservation.py`) |
| GO | DAVID (2012) | Not attempted: the 2012 knowledgebase is not available |

## Layout

| Path | Content |
| --- | --- |
| `main.nf`, `nextflow.config`, `environment.yml`, `requirements.txt` | The pipeline and its pinned environment |
| `results_notes.json` | Labels, sources, assumptions and causes of every item (written by `pipeline/make_notes.py` from `pipeline/causes.py` and `pipeline/page_notes.json`) |
| `pipeline/` | `fetch_inputs.sh`, `build_junction_db.py`, `map_sample.py`, `tophat_junctions.sh`, `summarize_mapping.py`, `build_junction_table.py`, `analyze.py`, `refseq_stops.py`, `conservation.py`, `port_checks.py`, `figures.py` and `pixel_score.py`, `compare.py`, `build_results.py`, `check_results.py`, `build_page.py`, `check_reproduction.py`, `compare_runs.py`, `check_package.py`, `update_readmes.py`, `hypotheses.py` |
| `published/` | The paper's figures for comparison |
| `output/mapping/` | Junction counts of the four samples (database and TopHat), gene counts, read categories and mapping statistics: the result of the six-hour mapping, which the default run reads |
| `output/` | `analysis.json` (every number), `events.tsv.gz` (splice events with PSI), `figure_data.json`, `conservation.json`, `refseq_stops.json`, `port_checks.json`, `comparison.json`, `figs/` (renders and overlays), `hypotheses.json` (the hypothesis tests behind the causes; run once with `pipeline/hypotheses.py`, not part of the pipeline) |

## Run

From the repository root, with [micromamba](https://mamba.readthedocs.io/) and Nextflow 26.04.3:

```bash
micromamba create -f PMC3446288/figure-reproduction/environment.yml
```

```bash
micromamba run -n pmc3446288 nextflow run PMC3446288/figure-reproduction/main.nf --outdir results
```

The default run (the CI run of `.github/workflows/reproduce-pmc3446288.yml`, about 15 minutes)
downloads the UCSC mm9 tables and genome and the paper's supplementary files, reads the committed
mapping in `output/mapping/` and the committed phastCons profiles, and recomputes everything else.
`--full` (the workflow started by hand with `full`) also downloads the reads, the Bowtie index, the GEO
alignments and phastCons (about 9 GB), maps the four samples (about 6 hours on 4 cores; resumable),
and rebuilds the profiles.

## Pipeline steps

1. `FETCH`: download the inputs and check their SHA-256.
2. `--full` only: `JUNCTION_DB` (build and index the database), `MAP` (each sample), `SUMMARIZE` (read categories, gene counts, TopHat junctions), `JUNCTION_TABLE`.
3. `REFSEQ_STOPS`: RefSeq stop distances (Fig. S2) and genome stop-codon shares (Fig. 7b).
4. `ANALYZE`: TMM, fold changes, PTC calls, splice classes, every number.
5. `CONSERVATION` (`--full`; otherwise the committed profiles), `PORT_CHECKS` (PTC distances against Additional files 8 and 9, TMM against edgeR, the paper's arithmetic).
6. `FIGURES`: renders, overlays, pixel scores with negative controls, bar heights read off the figures.
7. `COMPARE`, `RESULTS`: `comparison.json`, `results.json` with computed verdicts.
8. `PACKAGE`: the package check (wheel, fresh install, tests, tutorial).
9. `PAGE`: the results page. `CHECK`: `check_results.py`, unchanged verdicts, and the fresh run equal to `output/`.

## Limits

- `CHECK` compares every committed output with the fresh run, numbers to 1e-9 and images by decoded pixels, except `figs/fig7b_*.png` and `figs/figS2_*.png`: on GitHub's runners their bar edges antialias differently by a few pixels. The values they draw (`figs/figures.json`) are still compared.

- The junction database and every annotation are today's, not the paper's. Counts move by a few per cent to several fold (Fig. 1a intronic reads, truncation, Fig. 3b).
- TROMER, one of the paper's six exon sources for PTC calls, has no mouse data online. We call 24 to 28% of the paper's PTC+ junctions. The junctions we exclude as unannotated are enough to explain that, but it is not shown that they would be PTC+.
- The paper's PSI formulas, its false-positive gene filter, its random-exon baseline (Fig. 7a) and its read cutoff for Fig. 3b are not fully stated.
- Pixel scores are on the 1200-px published figures with a 3-px tolerance; Figs 6 and 7a differ in level, Fig. 5a cannot be told from a 3-nt shift.
- The mapping simulation, GO analyses, the microarray comparison, Table S6 and the wet-lab results are not attempted (see `../results.json`).

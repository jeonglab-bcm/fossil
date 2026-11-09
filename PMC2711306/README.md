# PMC2711306 — Geometric de-noising of protein-protein interaction networks (Kuchaiev et al. 2009)

Kuchaiev O, Rašajski M, Higham DJ, Pržulj N. Geometric de-noising of protein-protein interaction
networks. *PLoS Computational Biology* 5(8):e1000454 (2009).
[doi:10.1371/journal.pcbi.1000454](https://doi.org/10.1371/journal.pcbi.1000454) ·
[PMC2711306](https://pmc.ncbi.nlm.nih.gov/articles/PMC2711306/)

The paper is © 2009 Kuchaiev et al., published under
[CC BY](https://creativecommons.org/licenses/by/4.0/). In keeping with the rest of this repository,
this folder does not contain the paper, its full text or its supplement files.
`figure-reproduction/published/figure-*.png` are the paper's Figures 1–5 and S1–S3, converted to
PNG from the original TIFF files, and are redistributed under CC BY with the attribution above.

The issue that set this reproduction up (#17) said the software was lost. It was not: the
authors' three Matlab functions (`embed_novi.m`, `assign_scores.m`, `EM.m`, "free for
non-commercial purposes") are on the Wayback Machine at kuchaev.com/Denoising. So are Collins et
al.'s purification-enrichment (PE) scores for all 401,820 yeast pairs, at
interactome-cmp.ucsf.edu (2010). That file is the yeast test data the issue thought needed a
manual download from a 403 page. Neither is redistributed here. The pipeline downloads both and
checks their SHA-256.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | Figures 1–5 and S1–S3 redrawn on the published pixel grids with negative controls, Tables S1–S6 and the claims in the text, the port check against the authors' Matlab under GNU Octave. Nextflow pipeline. |
| [`package/`](package/) | `geodenoise`, the method as a Python package, with example data, tests and an executed [tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every figure, table and number of the paper, with our values and the verdict computed from them. |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

Install the method: `pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC2711306/package"`.

## Results

| Item | Verdict | Measure | Why |
| --- | --- | --- | --- |
| Fig. 1A, densities of Yhigh distances in 5 dimensions | agrees | 97.61% within 2 px (pass 91.4%, best control 89.4%) |  |
| Fig. 1B, densities of HumanBG distances in 5 dimensions | partly | 69.93% within 2 px (pass 90.0%, best control 62.7%) | The edge density comes back (peak at 0.20-0.21 over 20 seeds, as published); the non-edge density depends on the random training sample and EM start: its middle component's mean moves between 0.39 and 0.62 over 20 seeds. The embedding itself agrees (2,837 edges beyond 0.4 against 2,838). |
| Fig. 2, ROC curves on Yhigh for dimensions 2 to 7 | agrees | 92.56% within 2 px (pass 90.0%, best control 31.7%) | Assumed: Collins et al.'s low-confidence edges are the pairs with 1.85 <= PE < 3.19 between Yhigh proteins (5,356 pairs); The markers sit at epsilon 0.01 to 0.1 in steps of 0.01 and 0.2 to 1.4 in steps of 0.1 (Figs 2, 3); 0.01, 0.03, 0.05, 0.1 to 0.5 and (1, 1) (Figs 4, 5) |
| Fig. 2, the (TP, FP) labels of the dimension 7 curve | differs | 0 of 8 fields as printed | Every count is within 6% of the paper's with Collins et al.'s own scores, and within 1.4% with BioGRID's copy of their high-confidence set. Neither copy has the paper's Yhigh (1,004 proteins and 8,323 edges against 1,004 and 8,319, or 1,002 and 8,313), and the low-confidence cut is inferred. |
| Fig. 3, precision against recall on Yhigh for dimensions 2 to 7 | partly | 44.15% within 2 px (pass 90.0%, best control 25.5%) | The curves have the published shapes and order, but precision is a ratio of small counts on a 0-0.25 axis: a 2% change in TP or FP moves a curve by 3-8 pixels, more than the 2-pixel tolerance. The counts differ by up to 6% (fig2.labels). |
| Fig. 4, one iteration against iterating to convergence (dimension 4) | agrees | 95.07% within 2 px (pass 90.0%, best control 49.9%) | Assumed: Collins et al.'s low-confidence edges are the pairs with 1.85 <= PE < 3.19 between Yhigh proteins (5,356 pairs); The markers sit at epsilon 0.01 to 0.1 in steps of 0.01 and 0.2 to 1.4 in steps of 0.1 (Figs 2, 3); 0.01, 0.03, 0.05, 0.1 to 0.5 and (1, 1) (Figs 4, 5) |
| Fig. 5, ROC for recovering 500 to 3,000 deleted Yhigh edges | partly | 52.98% within 2 px (pass 90.0%, best control 43.6%) | The 500 to 2,000 curves come back; the published 3,000 curve is much lower (AUC about 0.90) than any of ours (0.950 to 0.960 over 10 deletions). |
| Fig. S1, p(edge|dist) for HumanBG | inconclusive | 92.03% within 2 px (pass 95.5%, best control 93.5%) | On this axis (0 to 0.12) every plausible density is a flat line near 0.003 with a spike at 0: the densities fitted to Yhigh score as well as ours, so the pixel comparison cannot tell them apart. |
| Fig. S2, p(nonedge|dist) for HumanBG | inconclusive | 38.18% within 2 px (pass 90.0%, best control 43.5%) | The non-edge density depends on the random training sample and EM start; ours runs 3% above the published curve beyond 0.3, and the Yhigh densities happen to fall closer. |
| Fig. S3, confidence score against distance for HumanBG | inconclusive | 89.21% within 2 px (pass 92.1%, best control 90.1%) | Outside the spike at 0 the score is a smooth curve near 0.1 for any of the fitted densities; the comparison cannot tell ours from the Yhigh control. |
| Table 1, sensitivity and specificity of five published predictors | not attempted | not attempted | Values quoted from other papers; the paper's own row (90% and 85%) is the item text.yeast_performance. |
| Table S1, the 251 high-confidence predictions | differs | 0 of 2 fields as printed | Our run predicts 369 new pairs, including 247 of the 251 published ones (the other 4 involve proteins our HumanBG lacks). The count depends on the width of the EM spike at distance 0: over 20 seeds it is 253 to 386. |
| Table S2 and text, predictions found in HPRD and BioGRID 2.0.50 (our predictions) | differs | 0 of 4 fields as printed | We predict 369 pairs rather than 251 (tableS1) and HPRD is a later release; the paper's own 251 pairs through our check give BioGRID 2.0.50 = 5 as printed and HPRD 11 against 12 (validation.published_pairs). |
| Table S3 and text, predictions sharing a GO BP or CC term (our predictions) | differs | 0 of 2 fields as printed | Counts scale with our 369 predictions; on the paper's 251 pairs our check gives 105 of 158 against 105 of 159. |
| Table S4 and text, predictions sharing a GO BP term (our predictions) | differs | 0 of 2 fields as printed | Counts scale with our 369 predictions; on the paper's 251 pairs our check gives 55 of 128 against 55 of 129. |
| Table S5 and text, predictions in the same KEGG pathway (our predictions) | differs | 0 of 2 fields as printed | KEGG of March 2009 is not freely archived; the current KEGG (372 human pathways against 205) puts many more of the paper's own pairs in pathways (80 against 26). |
| Table S6, predicted false positives (edges beyond 0.4 sharing no CC term) | differs | 0 of 1 fields as printed | 1,450 pairs against 1,455, 1,421 of them the paper's: HumanBG differs by 6 edges and the GO release is our closest match, not the paper's. |
| Table S7, BioGRID systems treated as physical | not attempted | not attempted | An input definition; we use it to build HumanBG. |
| Network sizes in the text | partly | 2 of 8 fields as printed | HumanBG is rebuilt from BioGRID 2.0.35 to within 6 edges and 1 protein of the largest component; the whole network is 138 proteins short (how the paper counted proteins is not stated). The Collins scores we found give 9,070 high-confidence edges against 9,074. |
| AUC, sensitivity and precision on Yhigh (text, Table 1's own row) | partly | 1 of 3 fields as printed | AUC 0.932 (printed 0.9) comes back. Sensitivity at 85% specificity is 90.6% against 90%, within the few-percent difference of the counts (fig2.labels). 'Precision about 0.15 at recall about 0.35' rounds the paper's own dimension 7 marker at epsilon 0.2 (Fig. 3: 0.142 at 0.335); ours at that epsilon is 0.144 at 0.319, and 0.143 at recall exactly 0.35. |
| Dimension 2 is clearly worst; higher dimensions change little (text) | agrees | 2 of 2 fields as printed | Assumed: Collins et al.'s low-confidence edges are the pairs with 1.85 <= PE < 3.19 between Yhigh proteins (5,356 pairs) |
| Iterating converges in about 10 iterations and is only slightly worse (text, Fig. 4) | partly | 1 of 2 fields as printed | The paper gives no stopping rule. Ours (stop when no new pair is predicted) takes 6 to 14 iterations, median 8, against 'about 10, depending on the network and the dimension'. The converged curve lies just under the first, as printed. |
| Candidate false positives (text) | partly | 3 of 4 fields as printed | 2,837 edges beyond 0.4 against 2,838: our HumanBG has 6 more edges. The shares sharing a CC term are taken over edges whose two proteins both have a CC term (72% and 66%, as printed); over all edges they would be 54% and 49%. |
| Pairs with CS >= 0.975: 1,685, of them 1,434 edges and 251 new (text) | differs | 0 of 3 fields as printed | The count depends on the EM spike at distance 0, which moves with the random training sample: over 20 seeds 1,679 to 2,361 pairs (the paper's 1,685 is inside) and 253 to 386 new ones. |
| GO background counts of Text S1 (HumanBG proteins annotated, pairs sharing a term) | differs | 0 of 4 fields as printed | GOA release 70 gives 6,292 annotated proteins against 6,278 (0.2%) and 5,877 against 5,864; the exact release and filters are not given. |
| The paper's Table S1 through our validation code (BioGRID 2.0.50, HPRD, GO, KEGG) | partly | 3 of 8 fields as printed | BioGRID 2.0.50 and the GO 'sharing' counts come back as printed; the annotated counts are one short (GO release), HPRD one short (release 9 for the 2009 release), KEGG far higher (current KEGG). |
| Claims recomputed from the paper's own numbers (Text S1 p-values, ratios) | exact | 13 of 13 fields as printed, 4 paper errors |  |
| 32 of 251 predictions co-mentioned in PubMed abstracts (CiteXplorer) | not attempted | not attempted | CiteXplorer was retired; its successor (Europe PMC) indexes a different, larger literature, so a count today does not test the 2009 one. |OK results.json: {"items": 30, "exact": 1, "agrees": 6, "partly": 8, "inconclusive": 3, "differs": 9, "not_attempted": 3, "open_causes": 5}
| Port against the authors' Matlab embedding (embed_novi.m under GNU Octave) | agrees | embed_novi.m under GNU Octave against geodenoise.embed on Yhigh, dimensions 2-7: distances differ by at most 0.018 (the authors' iteration stops at a change of 1e-3), TP counts at the epsilon grid by at most 0.9% (output/port_check.json) |  |
| Python package geodenoise and its tutorial | agrees | geodenoise 0.1.0: wheel installed in a fresh environment and imported from it; tests 7 passed; tutorial 7 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |  |

1 exact, 6 agrees, 8 partly, 3 inconclusive, 9 differs, 3 not attempted; 5 open causes.

## Claims in the text

| Claim | Kind | Paper | Ours | Verdict |
| --- | --- | --- | --- | --- |
| Network sizes in the text: HumanBG proteins | ours | 7930 | 7792 | partly |
| Network sizes in the text: HumanBG interactions | ours | 23543 | 23538 | partly |
| Network sizes in the text: HumanBG largest component, proteins | ours | 7513 | 7514 | partly |
| Network sizes in the text: HumanBG largest component, interactions | ours | 23372 | 23378 | partly |
| Network sizes in the text: Collins high-confidence interactions | ours | 9074 | 9070 | partly |
| Network sizes in the text: Collins high-confidence proteins | ours | 1622 | 1622 | partly |
| Network sizes in the text: Yhigh proteins | ours | 1004 | 1004 | partly |
| Network sizes in the text: Yhigh interactions | ours | 8323 | 8319 | partly |
| AUC, sensitivity and precision on Yhigh (text, Table 1's own row): AUC, dimension 7 | ours | 0.9 | 0.932 | partly |
| AUC, sensitivity and precision on Yhigh (text, Table 1's own row): sensitivity at 85% specificity, dimension 7 (%) | ours | 90 | 90.6 | partly |
| AUC, sensitivity and precision on Yhigh (text, Table 1's own row): precision at recall 0.35, dimension 7 | ours | 0.15 | 0.143 | partly |
| Dimension 2 is clearly worst; higher dimensions change little (text): dimension 2 has the lowest AUC | ours | yes | yes | agrees |
| Dimension 2 is clearly worst; higher dimensions change little (text): AUCs of dimensions 4 to 7 within 0.01 of each other | ours | yes | yes | agrees |
| Iterating converges in about 10 iterations and is only slightly worse (text, Fig. 4): iterations to converge (median over epsilon) | ours | 10 | 8 | partly |
| Iterating converges in about 10 iterations and is only slightly worse (text, Fig. 4): iterating is no better than one iteration at any epsilon | ours | yes | yes | partly |
| Candidate false positives (text): edges further apart than 0.4 | ours | 2838 | 2837 | partly |
| Candidate false positives (text): share of all edges (%) | ours | 12 | 12 | partly |
| Candidate false positives (text): edges sharing a CC term, of those with both proteins annotated (%) | ours | 72 | 72 | partly |
| Candidate false positives (text): candidates sharing a CC term, of those annotated (%) | ours | 66 | 66 | partly |
| Pairs with CS >= 0.975: 1,685, of them 1,434 edges and 251 new (text): pairs with CS >= 0.975 | ours | 1685 | 2292 | differs |
| Pairs with CS >= 0.975: 1,685, of them 1,434 edges and 251 new (text): of them edges | ours | 1434 | 1923 | differs |
| Pairs with CS >= 0.975: 1,685, of them 1,434 edges and 251 new (text): of them new | ours | 251 | 369 | differs |
| GO background counts of Text S1 (HumanBG proteins annotated, pairs sharing a term): HumanBG proteins with a BP or CC term | ours | 6278 | 6292 | differs |
| GO background counts of Text S1 (HumanBG proteins annotated, pairs sharing a term): pairs of them sharing a term (K) | ours | 7400424 | 7428577 | differs |
| GO background counts of Text S1 (HumanBG proteins annotated, pairs sharing a term): HumanBG proteins with a BP term | ours | 5864 | 5877 | differs |
| GO background counts of Text S1 (HumanBG proteins annotated, pairs sharing a term): pairs of them sharing a BP term (K) | ours | 1354495 | 1358313 | differs |
| The paper's Table S1 through our validation code (BioGRID 2.0.50, HPRD, GO, KEGG): in BioGRID 2.0.50 | our validation code on the paper's Table S1 | 5 | 5 | partly |
| The paper's Table S1 through our validation code (BioGRID 2.0.50, HPRD, GO, KEGG): in HPRD | our validation code on the paper's Table S1 | 12 | 11 | partly |
| The paper's Table S1 through our validation code (BioGRID 2.0.50, HPRD, GO, KEGG): annotated (BP or CC) | our validation code on the paper's Table S1 | 159 | 158 | partly |
| The paper's Table S1 through our validation code (BioGRID 2.0.50, HPRD, GO, KEGG): sharing a BP or CC term | our validation code on the paper's Table S1 | 105 | 105 | partly |
| The paper's Table S1 through our validation code (BioGRID 2.0.50, HPRD, GO, KEGG): annotated (BP) | our validation code on the paper's Table S1 | 129 | 128 | partly |
| The paper's Table S1 through our validation code (BioGRID 2.0.50, HPRD, GO, KEGG): sharing a BP term | our validation code on the paper's Table S1 | 55 | 55 | partly |
| The paper's Table S1 through our validation code (BioGRID 2.0.50, HPRD, GO, KEGG): both proteins in a KEGG pathway | our validation code on the paper's Table S1 | 26 | 80 | partly |
| The paper's Table S1 through our validation code (BioGRID 2.0.50, HPRD, GO, KEGG): in the same KEGG pathway | our validation code on the paper's Table S1 | 12 | 42 | partly |
| Claims recomputed from the paper's own numbers (Text S1 p-values, ratios): pairs among 7,513 HumanBG proteins (Text S1 M) | arithmetic check (the paper's own numbers) | 28218828 | 28218828 | exact |
| Claims recomputed from the paper's own numbers (Text S1 p-values, ratios): pairs among 6,278 GO BP/CC-annotated proteins (M) | arithmetic check (the paper's own numbers) | 19703503 | 19703503 | exact |
| Claims recomputed from the paper's own numbers (Text S1 p-values, ratios): pairs among 5,864 GO BP-annotated proteins (M) | arithmetic check (the paper's own numbers) | 17190316 | 17190316 | exact |
| Claims recomputed from the paper's own numbers (Text S1 p-values, ratios): HPRD p-value, Text S1 (12 of 251, K = 34,119) | arithmetic check (the paper's own numbers) | 7.5e-8 | 7.5e-16 | exact |
| Claims recomputed from the paper's own numbers (Text S1 p-values, ratios): HPRD p-value, main text | arithmetic check (the paper's own numbers) | 7e-8 | 7e-16 | exact |
| Claims recomputed from the paper's own numbers (Text S1 p-values, ratios): GO BP or CC p-value (105 of 159) | arithmetic check (the paper's own numbers) | 7.26e-8 | 3.38e-13 | exact |
| Claims recomputed from the paper's own numbers (Text S1 p-values, ratios): GO BP p-value (55 of 129) | arithmetic check (the paper's own numbers) | 1.4e-8 | 6.2e-27 | exact |
| Claims recomputed from the paper's own numbers (Text S1 p-values, ratios): annotated pairs, 251 - 92 | arithmetic check (the paper's own numbers) | 159 | 159 | exact |
| Claims recomputed from the paper's own numbers (Text S1 p-values, ratios): share of GO-annotated predictions sharing a term (%) | arithmetic check (the paper's own numbers) | 66 | 66 | exact |
| Claims recomputed from the paper's own numbers (Text S1 p-values, ratios): high-confidence pairs, 1,434 edges + 251 new | arithmetic check (the paper's own numbers) | 1685 | 1685 | exact |
| Claims recomputed from the paper's own numbers (Text S1 p-values, ratios): candidate false positives, share of edges (%) | arithmetic check (the paper's own numbers) | 12 | 12 | exact |
| Claims recomputed from the paper's own numbers (Text S1 p-values, ratios): KEGG: predictions with both proteins in a pathway (% of 251) | arithmetic check (the paper's own numbers) | 10 | 10 | exact |
| Claims recomputed from the paper's own numbers (Text S1 p-values, ratios): KEGG: same pathway (% of 26) | arithmetic check (the paper's own numbers) | 46 | 46 | exact |
| Claims recomputed from the paper's own numbers (Text S1 p-values, ratios): KEGG: same pathway (% of 251), 'about 5%' | arithmetic check (the paper's own numbers) | 5 | 5 | exact |
| Claims recomputed from the paper's own numbers (Text S1 p-values, ratios): validated in HPRD or BioGRID 2.0.50: 12 + 5 - 4 | arithmetic check (the paper's own numbers) | 13 | 13 | exact |
| Claims recomputed from the paper's own numbers (Text S1 p-values, ratios): recall 0.35 of 154,000 human interactions | arithmetic check (the paper's own numbers) | 53900 | 53900 | exact |
| Claims recomputed from the paper's own numbers (Text S1 p-values, ratios): Collins: 12,122 - 7,504 kept, + 4,456 new | arithmetic check (the paper's own numbers) | 9074 | 9074 | exact |
| 32 of 251 predictions co-mentioned in PubMed abstracts (CiteXplorer) | ours | | not attempted | not_attempted |

The paper's main claim holds: the embedding recovers Collins' low-confidence yeast edges with AUC 0.93 and finds the human predictions of Table S1 (247 of 251). Some counts differ; the causes are the random EM fit behind the 0.975 cut, the later GO, HPRD and KEGG releases, and copies of the yeast data that differ from the paper's by a few edges.

Kept local and gitignored: `sources/` (the paper, its supplement, the authors' code, downloads),
`work/` (scratch runs and Slurm logs), `.venv/` and `.octave/` (the Python and Octave environments).

# PMC4110735 reproduction check

## results.json

| Item | Verdict | Measure | Why |
| --- | --- | --- | --- |
| Fig. 1, shifting and scaling patterns | not attempted | not attempted | A sketch of two kinds of pattern; it plots no data. |
| Fig. 2, inverted profiles of Mrps26 and Pfn2 (GDS3702) | agrees | 92.92% within 2 px (pass 90.0%, best control 85.3%) | Assumed: Line width 5 px and marker size 20 px (presentation) |
| Fig. 3, mixed patterns of YBL002W, YBL003C and YBL006W (yeast) | agrees | 96.26% within 2 px (pass 90.0%, best control 75.4%) | Assumed: The data are Cheng and Church's yeast matrix (ref. 25, yeast.matrix and yeast.genes), whose rows match the figure value for value; the figure's YBL006W is the matrix's YBL006C; Line width 2 px and marker size 16 px (presentation) |
| Fig. 4a, AUPR bars against Table 2 | agrees | 51 of 51 fields as printed | Assumed: Bar heights read off the published panel (axes fitted to the frame and tick marks; one pixel is 0.0015) |
| Fig. 4b, AUROC bars against Table 2 | agrees | 50 of 50 fields as printed, 1 paper errors | Assumed: Bar heights read off the published panel (one pixel is 0.0013) |
| Fig. 4c, F0.5 bars against Table 2 | agrees | 51 of 51 fields as printed | Assumed: Bar heights read off the published panel (one pixel is 0.0015) |
| Fig. 5, run time of GeCON and ARACNE | agrees | 6 of 6 fields as printed | Assumed: The six sizes (250, 1000, 1500, 2000, 2585, 3000 genes) read off the figure's markers |
| Fig. 6, networks, profiles and heat maps of selected modules | not attempted | not attempted | Pictures of selected modules from the real datasets; the paper does not say which modules, which theta, or how a module was cut from the network, and gives no module's gene list except three GDS3702 modules in the text. |
| Fig. 7, the worked example drawn | agrees | 95.36% within 2 px (pass 90.0%, best control 25.5%) | Assumed: Line width 3 px (presentation) |
| Fig. 7 and Eq. (5): G = {343, 314, 409} becomes {138, -1; 52, 1} | exact | 4 of 4 fields as printed |  |
| Table 1, the 13 in silico networks and their sizes | exact | 13 of 13 fields as printed |  |
| Table 2, AUPR of GeCON, ARACNE, CLR and MRNET on D1 to D13 | differs | 0 of 52 fields as printed | GeCON as the paper describes it ranks pairs no better than chance on these data (mean AUPR 0.203, the share of true pairs is 0.203; mean AUROC 0.485), while minet's methods reach AUPR 0.275 to 0.291 and AUROC 0.535 to 0.61. At theta 0.5 and tau 20 it connects 84% to 100% of all pairs, because on positive values almost every edge angle of Eq. (5) sits near 45 or 135 degrees. No variant we tried brings GeCON's mean scores near the paper's (best mean AUPR 0.255 against 0.633); the few single cells that fall within printed precision are not counted as agreement. The comparators' values differ too, so the authors' simulations and scoring cannot be recovered. |
| Table 2, AUROC | partly | 1 of 52 fields as printed | GeCON as the paper describes it ranks pairs no better than chance on these data (mean AUPR 0.203, the share of true pairs is 0.203; mean AUROC 0.485), while minet's methods reach AUPR 0.275 to 0.291 and AUROC 0.535 to 0.61. At theta 0.5 and tau 20 it connects 84% to 100% of all pairs, because on positive values almost every edge angle of Eq. (5) sits near 45 or 135 degrees. No variant we tried brings GeCON's mean scores near the paper's (best mean AUPR 0.255 against 0.633); the few single cells that fall within printed precision are not counted as agreement. The comparators' values differ too, so the authors' simulations and scoring cannot be recovered. |
| Table 2, F0.5 | differs | 0 of 52 fields as printed | GeCON as the paper describes it ranks pairs no better than chance on these data (mean AUPR 0.203, the share of true pairs is 0.203; mean AUROC 0.485), while minet's methods reach AUPR 0.275 to 0.291 and AUROC 0.535 to 0.61. At theta 0.5 and tau 20 it connects 84% to 100% of all pairs, because on positive values almost every edge angle of Eq. (5) sits near 45 or 135 degrees. No variant we tried brings GeCON's mean scores near the paper's (best mean AUPR 0.255 against 0.633); the few single cells that fall within printed precision are not counted as agreement. The comparators' values differ too, so the authors' simulations and scoring cannot be recovered. |
| Table 3, gene and sample counts of the real datasets | partly | 4 of 7 fields as printed | The public files have 17 conditions for Yeast KY and the cell cycle set, not 18, and GEO's GDS825 has 4 samples, not 8. The sporulation file (TLS failure from our runner, no reachable archive) and the 517-gene Arabidopsis matrix could not be obtained, so they have no field. The subset sizes of GDS958 and GDS3702 are our filter's. |
| Table 4, GO terms of selected modules (GeneMANIA) | partly | 4 of 10 fields as printed | Terms not found in our modules: GeneMANIA's and FuncAssociate's 2014 annotations and the authors' modules are gone, and our module cut and filters are guesses. Rows of Sporulation, Thaliana are left out: the sporulation file failed TLS verification from our runner and no archive was reachable, and the 517 x 13 Arabidopsis matrix was not located. |
| Table 5, GO terms of selected modules (FuncAssociate) | partly | 3 of 7 fields as printed | Terms not found in our modules: GeneMANIA's and FuncAssociate's 2014 annotations and the authors' modules are gone, and our module cut and filters are guesses. Rows of GDS825, Sporulation are left out: GEO's GDS825 has 4 samples, not the paper's 8, and the sporulation file could not be fetched. |
| Claims recomputed from the paper's own Table 2 | agrees | Average row: 7 of 12 exact, 12 within one unit in the last digit; improvements from the row means: 4 of 9 exact, 9 within one unit (from the printed averages 0 of 9). The table itself has GeCON best in 38 of 39 dataset-score cells (not: D13 AUROC), against "in all cases". "More than 200 times better" in AUPR is 3.7 times (269.72%). |  |
| "GeCON outperforms all other algorithms ... on all three scores" (Fig. 4, Table 2) | differs | 0 of 3 fields as printed | GeCON as the paper describes it ranks pairs no better than chance on these data (mean AUPR 0.203, the share of true pairs is 0.203; mean AUROC 0.485), while minet's methods reach AUPR 0.275 to 0.291 and AUROC 0.535 to 0.61. At theta 0.5 and tau 20 it connects 84% to 100% of all pairs, because on positive values almost every edge angle of Eq. (5) sits near 45 or 135 degrees. No variant we tried brings GeCON's mean scores near the paper's (best mean AUPR 0.255 against 0.633); the few single cells that fall within printed precision are not counted as agreement. The comparators' values differ too, so the authors' simulations and scoring cannot be recovered. |
| Average improvement of GeCON over ARACNE, CLR and MRNET (Table 2, last row) | differs | 0 of 9 fields as printed | GeCON as the paper describes it ranks pairs no better than chance on these data (mean AUPR 0.203, the share of true pairs is 0.203; mean AUROC 0.485), while minet's methods reach AUPR 0.275 to 0.291 and AUROC 0.535 to 0.61. At theta 0.5 and tau 20 it connects 84% to 100% of all pairs, because on positive values almost every edge angle of Eq. (5) sits near 45 or 135 degrees. No variant we tried brings GeCON's mean scores near the paper's (best mean AUPR 0.255 against 0.633); the few single cells that fall within printed precision are not counted as agreement. The comparators' values differ too, so the authors' simulations and scoring cannot be recovered. |
| D6: AUPR .84, AUROC .78, F .86 | differs | 0 of 3 fields as printed | GeCON as the paper describes it ranks pairs no better than chance on these data (mean AUPR 0.203, the share of true pairs is 0.203; mean AUROC 0.485), while minet's methods reach AUPR 0.275 to 0.291 and AUROC 0.535 to 0.61. At theta 0.5 and tau 20 it connects 84% to 100% of all pairs, because on positive values almost every edge angle of Eq. (5) sits near 45 or 135 degrees. No variant we tried brings GeCON's mean scores near the paper's (best mean AUPR 0.255 against 0.633); the few single cells that fall within printed precision are not counted as agreement. The comparators' values differ too, so the authors' simulations and scoring cannot be recovered. |
| Mrps26 and Pfn2 "clearly show negative behaviour" (Fig. 2) | exact | 1 of 1 fields as printed |  |
| YBL002W and YBL003C co-regulated, YBL006W inverted (Fig. 3) | partly | 1 of 2 fields as printed | Over all 16 steps GeCON finds YBL006W positively, not negatively, related to the other two (positive support 0.69, negative 0.31); the inversion the text describes holds only at some steps, which the paper calls mixed regulation in the same paragraph. |
| "GeCON is much faster than ARACNE" (Fig. 5) | exact | 1 of 1 fields as printed |  |
| GeCON "is insensitive to normalization of data" (Methods, advantage iv) | differs | 0 of 1 fields as printed | Eq. (5) applies atan2 to the two raw values, so the angle depends on their ratio, not their difference. On Yeast KY's log values (around 7) almost every angle sits near 45 or 135 degrees and GeCON connects all 27,966 pairs; on the site's normalised version of the same genes it connects 1,226 (tau 20, theta 0.6). 97% of the log data's angles lie within 5 degrees of 45 or 135. |
| "GeCON can extract functionally enriched network modules from real expression data" | exact | 3 of 3 fields as printed |  |
| Python port of GeneNetWeaver's simulation against the DREAM4 release | agrees | All 10 DREAM4 networks: gold standards from the network files equal the released ones; the port's wild-type steady state tracks the released wild type with log correlation 0.95 to 0.99 |  |
| Python package gecon and its tutorial | agrees | gecon 0.1.0: wheel installed in a fresh environment and imported from it; tests 6 passed; tutorial 5 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |  |

5 exact, 10 agrees, 5 partly, 6 differs, 2 not attempted; 8 open causes.
OK results.json: {"items": 28, "exact": 5, "agrees": 10, "partly": 5, "inconclusive": 0, "differs": 6, "not_attempted": 2, "open_causes": 8}

## Package

gecon 0.1.0: wheel installed in a fresh environment and imported from it; tests 6 passed; tutorial 5 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync

## Fresh run against the committed outputs

| File | Fresh vs committed | Detail |
| --- | --- | --- |
| claims.json | same |  |
| datasets.json | same |  |
| dream.json | same |  |
| enrich.json | same |  |
| fig4.json | same |  |
| fig5.json | same |  |
| normalisation.json | same |  |
| port_check.json | same |  |
| profiles.json | same |  |
| table3.json | same |  |
| timing.json | same |  |
| dream/D1.tsv | same |  |
| dream/D10.tsv | same |  |
| dream/D10_gold.tsv | same |  |
| dream/D11.tsv | same |  |
| dream/D11_gold.tsv | same |  |
| dream/D12.tsv | same |  |
| dream/D12_gold.tsv | same |  |
| dream/D13.tsv | same |  |
| dream/D13_gold.tsv | same |  |
| dream/D1_gold.tsv | same |  |
| dream/D2.tsv | same |  |
| dream/D2_gold.tsv | same |  |
| dream/D3.tsv | same |  |
| dream/D3_gold.tsv | same |  |
| dream/D4.tsv | same |  |
| dream/D4_gold.tsv | same |  |
| dream/D5.tsv | same |  |
| dream/D5_gold.tsv | same |  |
| dream/D6.tsv | same |  |
| dream/D6_gold.tsv | same |  |
| dream/D7.tsv | same |  |
| dream/D7_gold.tsv | same |  |
| dream/D8.tsv | same |  |
| dream/D8_gold.tsv | same |  |
| dream/D9.tsv | same |  |
| dream/D9_gold.tsv | same |  |
| dream/datasets.json | same |  |
| figures/fig2_ours.png | same |  |
| figures/fig2_overlay.png | same |  |
| figures/fig3_ours.png | same |  |
| figures/fig3_overlay.png | same |  |
| figures/fig4_ours.png | same |  |
| figures/fig4_overlay.png | same |  |
| figures/fig4_run.png | same |  |
| figures/fig5_ours.png | same |  |
| figures/fig5_overlay.png | same |  |
| figures/fig7_ours.png | same |  |
| figures/fig7_overlay.png | same |  |

49 of 49 files agree.

**PASS**

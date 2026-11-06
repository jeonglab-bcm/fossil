# PMC4015815 reproduction check

## results.json

| Item | Verdict | Measure | Why |
| --- | --- | --- | --- |
| Gist 2.3 port against Gist's own sample run | agrees | Gist's printed weights through our kernel give its printed training discriminants within 0.003 (weight rounding). Retrained with the sample's settings and seed: objective 0.0173670 against Gist's 0.0173686, 1591 of 1644 weights equal as printed, 196 passes against 200. The sample came from Gist 2.0. |  |
| Fig. 1 | not attempted | not attempted | A worked example of the feature vector (AGLP to KFFK, dMAX = 2); nothing to recompute. |
| Fig. 2 | not attempted | not attempted | Pseudocode of the Distance-based Top-1-gram vector; it is the method, implemented in features.py. |
| Fig. 3, SVM-DR curve | partly | 84.40% within 2 px (pass 85.0%, best control 75.9%) | Nine of ten points come back within 0.0005 ROC; dMAX 20 is 0.0013 above the published point (0.9004 against 0.8991, about 10 px). |
| Fig. 3, SVM-DT curve | inconclusive | 0.43% within 2 px (pass 85.0%, best control 4.6%) | The SVM-DT curve rises and flattens as published, but our profiles are not the paper's; the points sit up to a few thousandths of ROC from the published ones. |
| Fig. 3, SVM-DR points (values) | partly | 9 of 10 fields as printed | Nine of ten points come back within 0.0005 ROC; dMAX 20 is 0.0013 above the published point (0.9004 against 0.8991, about 10 px). |
| Fig. 3, SVM-DT points (values) | differs | 0 of 10 fields as printed | The SVM-DT curve rises and flattens as published, but our profiles are not the paper's; the points sit up to a few thousandths of ROC from the published ones. |
| Table 1, SVM-DR (ROC, ROC50) | partly | 1 of 2 fields as printed | ROC comes back exactly (0.919); ROC50 does not (0.497 against 0.715). Our ROC matches at every dMAX, so the rankings agree; the gap is in how ROC50 was computed, which the paper's one-line definition does not settle. |
| Table 1, SVM-DT (ROC, ROC50) | differs | 0 of 2 fields as printed | Two causes: the profiles (2016 database, settings from the lab's 2017 code) move ROC by a few thousandths, and ROC50 is computed some other way than the stated definition (see Table 1, SVM-DR). |
| Table 1, the nine other methods | not attempted | not attempted | Quoted by the paper from earlier work (Monomer-dist, SVM-LA, SVM-Pairwise, SVM-Top-n-gram and -LSA, SVM-PDT-Profile, PseAACIndex-Profile, BioSVM-2L, HHSearch); not results of this paper. |
| Fig. 4A, Top-1-gram pairs (SVM-DT) | partly | 73.25% within 24 grey levels per cell px (pass 95.0%, best control 69.2%) | Our Top-1-gram sequences come from a 2016 database with PSI-BLAST settings taken from the lab's 2017 code; the 2014 profiles are gone. The SVM-DT heatmap keeps (G,G) on top but (L,L) drops, and its correlation with the published panel is little better than the SVM-DR panel's. |
| Fig. 4B, residue pairs (SVM-DR) | agrees | 100.00% within 24 grey levels per cell px (pass 95.0%, best control 71.8%) | Assumed: The L2 norm of a pair (t_i, t_i) includes its distance-0 weight (the composition T0_i), as Fig. 1 counts pairs 'at distance 0, 1, 2' |
| Fig. 5A, (G,G) of SVM-DT | inconclusive | 12.84% within 2 px (pass 98.0%, best control 12.8%) | As Fig. 4A: our SVM-DT weights come from other profiles. The ladder shape and the mostly negative signs come back; the bar heights do not. |
| Fig. 5B, (L,L) of SVM-DT | partly | 10.81% within 2 px (pass 98.0%, best control 9.5%) | As Fig. 4A: our SVM-DT weights come from other profiles. The ladder shape and the mostly negative signs come back; the bar heights do not. |
| Fig. 5C, (G,G) of SVM-DR | agrees | 100.00% within 2 px (pass 98.0%, best control 89.9%) | Assumed: The bars are plotted at x = d + 1 (the bar at x shows distance x - 1; x = 1 is distance 0) |
| Fig. 5D, (L,L) of SVM-DR | agrees | 100.00% within 2 px (pass 98.0%, best control 96.6%) | Assumed: The bars are plotted at x = d + 1 (the bar at x shows distance x - 1; x = 1 is distance 0) |
| Claims recomputed from the paper's own Table 1 | agrees | From Table 1's printed values: SVM-DT minus SVM-Top-n-gram is 4.1 ROC and 10.4 ROC50 points (text: 4.1 and 10.4), and the five comparison sentences hold on the paper's own numbers (with 'outperforms Monomer-dist' resting on ROC50: both rows print ROC 0.919). |  |
| Benchmark: 54 families, 4,352 proteins | exact | 2 of 2 fields as printed |  |
| SVM-DT improves SVM-Top-n-gram by 4.1% ROC and 10.4% ROC50 | differs | 0 of 2 fields as printed | The gains are measured against SVM-Top-n-gram's values quoted from another paper. Our ROC gain is 4.3 points (paper 4.1); our ROC50 is lower across the board, so against the quoted 0.696 it shows a loss. Against our own position-independent baseline (SVM-DT at dMAX 0, Top-1-gram composition) the gains are 4.0 ROC and 25.7 ROC50 points, so the direction of the claim holds. |
| Family 2.5.1.3: SVM-DT 0.993 against SVM-DR 0.844 (ROC) | partly | 1 of 2 fields as printed | SVM-DR comes back (0.844); SVM-DT is 0.961 against 0.993, from other profiles. It still beats SVM-DR on this family by a wide margin. |
| ROC rises from dMAX 0 to 100 and is stable over 100 to 200 | agrees | 2 of 2 fields as printed | Assumed: PSI-BLAST profiles from the lab's 2016 nrdb90 (Pse-in-One 2.0), 3 iterations, E = 0.001, BLAST+ 2.17.0; Top-1-gram = largest weighted observed percentage, an all-zero column giving the query residue |
| (G,G) and (L,L) are the two most discriminative pairs for both methods | partly | 1 of 2 fields as printed | True for SVM-DR. For SVM-DT (G,G) comes first but (L,L) is sixth, behind (V,G) and (G,V): our Top-1-gram sequences come from other profiles. |
| Distance 0 always has the largest weight (Fig. 5) | agrees | 3 of 3 fields as printed, 1 paper errors | Assumed: PSI-BLAST profiles from the lab's 2016 nrdb90 (Pse-in-One 2.0), 3 iterations, E = 0.001, BLAST+ 2.17.0; Top-1-gram = largest weighted observed percentage, an all-zero column giving the query residue |
| Shorter distances weigh more than longer ones (Fig. 5) | agrees | 4 of 4 fields as printed | Assumed: PSI-BLAST profiles from the lab's 2016 nrdb90 (Pse-in-One 2.0), 3 iterations, E = 0.001, BLAST+ 2.17.0; Top-1-gram = largest weighted observed percentage, an all-zero column giving the query residue |
| Most (G,G) weights of SVM-DT are positive; SVM-DR has more positive ones | agrees | 1 of 1 fields as printed, 1 paper errors | Assumed: PSI-BLAST profiles from the lab's 2016 nrdb90 (Pse-in-One 2.0), 3 iterations, E = 0.001, BLAST+ 2.17.0; Top-1-gram = largest weighted observed percentage, an all-zero column giving the query residue |
| SVM-DR outperforms Monomer-dist and SVM-Pairwise and is comparable with SVM-LA | partly | 2 of 3 fields as printed | SVM-DR beats SVM-Pairwise and is within a point of SVM-LA. 'Outperforms Monomer-dist' rests on ROC50 (both rows print ROC 0.919), and our ROC50 (0.497) is computed differently from the paper's (see Table 1). |
| SVM-DT outperforms every other method except SVM-PDT-Profile in average ROC | partly | 1 of 2 fields as printed | Our SVM-DT reaches ROC 0.9502, above every quoted profile method including SVM-PDT-Profile (0.950) by 0.0002; with Pse-in-One's Top-1-gram rule it is 0.9412, below it. The ranking against SVM-PDT-Profile turns on the profiles. |

1 exact, 9 agrees, 9 partly, 2 inconclusive, 3 differs, 3 not attempted; 6 open causes.
OK ./results.json: {"items": 27, "exact": 1, "agrees": 9, "partly": 9, "inconclusive": 2, "differs": 3, "not_attempted": 3, "open_causes": 6}

## This run against the committed output/

| File | Fresh vs committed | Detail |
| --- | --- | --- |
| fig3_ours.png | same |  |
| fig3_overlay.png | same |  |
| fig3_published.json | same |  |
| fig3_scores.json | same |  |
| fig4_ours.png | same |  |
| fig4_overlay.png | same |  |
| fig4_scores.json | same |  |
| fig5_ours.png | same |  |
| fig5_overlay.png | same |  |
| fig5_published.json | same |  |
| fig5_scores.json | same |  |
| figures_check.json | same |  |
| port_check.json | same |  |
| results.json | same |  |
| sweep_dr.csv | same |  |
| sweep_dt.csv | same |  |
| tables.json | same |  |
| weights_dr_2.5.1.1.json | same |  |
| weights_dr_2.5.1.3.json | same |  |
| weights_dt_2.5.1.1.json | same |  |
| weights_dt_2.5.1.3.json | same |  |

21 of 21 files agree.

Check passed.

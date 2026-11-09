# PMC4015815 reproduction check

## results.json

| Item | Verdict | Measure | Why |
| --- | --- | --- | --- |
| Gist 2.3 port against Gist's own sample run | agrees | Gist's printed weights through our kernel give its printed training discriminants within 0.003 (weight rounding). Retrained with the sample's settings and seed: objective 0.0173670 against Gist's 0.0173686, 1591 of 1644 weights equal as printed, 196 passes against 200. The sample came from Gist 2.0. |  |
| Fig. 1 | not attempted | not attempted | A worked example of the feature vector (AGLP to KFFK, dMAX = 2); nothing to recompute. |
| Fig. 2 | not attempted | not attempted | Pseudocode of the Distance-based Top-1-gram vector; it is the method, implemented in features.py. |
| Fig. 3, SVM-DR curve | partly | 84.40% within 2 px (pass 85.0%, best control 75.9%) | Nine of ten points come back within 0.0005 ROC; dMAX 20 is 0.0013 above the published point (0.9004 against 0.8991, about 10 px). |
| Fig. 3, SVM-DT curve | differs | 0.00% within 2 px (pass 85.0%, best control 0.0%) | The SVM-DT curve rises and flattens as published but sits 0.008 to 0.021 ROC above the published points (0.957 against 0.948 at dMAX 150). Our profiles follow the paper's ref. [28] but come from the lab's 2016 nrdb90, while the paper names only 'a non-redundant database' and its copy is not available. The 3-iteration profiles gave 0.950 at dMAX 150 (output/causes/dt_profiles_2008.json). |
| Fig. 3, SVM-DR points (values) | partly | 9 of 10 fields as printed | Nine of ten points come back within 0.0005 ROC; dMAX 20 is 0.0013 above the published point (0.9004 against 0.8991, about 10 px). |
| Fig. 3, SVM-DT points (values) | differs | 0 of 10 fields as printed | The SVM-DT curve rises and flattens as published but sits 0.008 to 0.021 ROC above the published points (0.957 against 0.948 at dMAX 150). Our profiles follow the paper's ref. [28] but come from the lab's 2016 nrdb90, while the paper names only 'a non-redundant database' and its copy is not available. The 3-iteration profiles gave 0.950 at dMAX 150 (output/causes/dt_profiles_2008.json). |
| Table 1, SVM-DR (ROC, ROC50) | partly | 1 of 2 fields as printed | ROC comes back exactly (0.919); ROC50 does not with the stated definition (0.497 against 0.715). Our ROC matches at every dMAX, so the rankings agree and the gap is in how ROC50 was computed. The paper's values match an ordinary ROC on the ranking cut at the 50th false positive, which divides by the positives found there instead of by all positives (0.712 against 0.715). |
| Table 1, SVM-DT (ROC, ROC50) | differs | 0 of 2 fields as printed | ROC 0.957 against 0.948: with profiles built as in the paper's ref. [28] our SVM-DT sits about 0.01 above the paper at every dMAX while family 2.5.1.3 comes back (0.993); our 2016 nrdb90 is not the paper's database. ROC50: the stated definition gives 0.720; the paper's values match an ordinary ROC on the ranking cut at the 50th false positive (see Table 1, SVM-DR), which gives 0.838 here, above 0.800 as ROC is above 0.948. |
| Table 1, the nine other methods | not attempted | not attempted | Quoted by the paper from earlier work (Monomer-dist, SVM-LA, SVM-Pairwise, SVM-Top-n-gram and -LSA, SVM-PDT-Profile, PseAACIndex-Profile, BioSVM-2L, HHSearch); not results of this paper. |
| Fig. 4A, Top-1-gram pairs (SVM-DT) | partly | 82.50% within 24 grey levels per cell px (pass 95.0%, best control 78.2%) | Our Top-1-gram profiles follow the paper's ref. [28] (10 PSI-BLAST iterations, BLOSUM62 pseudocounts) but come from the lab's 2016 nrdb90; the 2014 profiles are gone. The heatmap keeps (G,G) first and (L,L) second as published and correlates 0.875 with the published panel (Spearman; 0.770 with the earlier 3-iteration profiles), but cell values still differ. |
| Fig. 4B, residue pairs (SVM-DR) | agrees | 100.00% within 24 grey levels per cell px (pass 95.0%, best control 71.8%) | Assumed: The L2 norm of a pair (t_i, t_i) includes its distance-0 weight (the composition T0_i), as Fig. 1 counts pairs 'at distance 0, 1, 2' |
| Fig. 5A, (G,G) of SVM-DT | inconclusive | 10.14% within 2 px (pass 98.0%, best control 17.6%) | As Fig. 4A: our SVM-DT weights come from profiles built as in ref. [28] on another database. The ladder shape and the mostly negative signs come back and the bars follow the published ones more closely (r 0.58; 0.39 with the 3-iteration profiles), but the bar heights do not. |
| Fig. 5B, (L,L) of SVM-DT | inconclusive | 10.14% within 2 px (pass 98.0%, best control 12.2%) | As Fig. 4A: our SVM-DT weights come from profiles built as in ref. [28] on another database. The ladder shape and the mostly negative signs come back and the bars follow the published ones more closely (r 0.50; 0.28 with the 3-iteration profiles), but the bar heights do not. |
| Fig. 5C, (G,G) of SVM-DR | agrees | 100.00% within 2 px (pass 98.0%, best control 89.9%) | Assumed: The bars are plotted at x = d + 1 (the bar at x shows distance x - 1; x = 1 is distance 0) |
| Fig. 5D, (L,L) of SVM-DR | agrees | 100.00% within 2 px (pass 98.0%, best control 96.6%) | Assumed: The bars are plotted at x = d + 1 (the bar at x shows distance x - 1; x = 1 is distance 0) |
| Claims recomputed from the paper's own Table 1 | agrees | From Table 1's printed values: SVM-DT minus SVM-Top-n-gram is 4.1 ROC and 10.4 ROC50 points (text: 4.1 and 10.4), and the five comparison sentences hold on the paper's own numbers (with 'outperforms Monomer-dist' resting on ROC50: both rows print ROC 0.919). |  |
| Benchmark: 54 families, 4,352 proteins | exact | 2 of 2 fields as printed |  |
| SVM-DT improves SVM-Top-n-gram by 4.1% ROC and 10.4% ROC50 | differs | 0 of 2 fields as printed | The gains are measured against SVM-Top-n-gram's values quoted from another paper. Our gains are 5.0 ROC points (paper 4.1) and 2.4 ROC50 points with the stated definition (paper 10.4); with the paper's own ROC50 (an ordinary ROC on the ranking cut at the 50th false positive) 14.2 points. Our SVM-DT sits above the paper in both ROC and ROC50 (profiles from the 2016 nrdb90). Against our own position-independent baseline (SVM-DT at dMAX 0, Top-1-gram composition) the gains are 2.8 ROC and 19.9 ROC50 points, so the direction of the claim holds. |
| Family 2.5.1.3: SVM-DT 0.993 against SVM-DR 0.844 (ROC) | agrees | 2 of 2 fields as printed | Both come back: SVM-DR 0.844 and SVM-DT 0.993 with profiles built as in the paper's ref. [28]. With the earlier 3-iteration profiles SVM-DT was 0.961 (output/causes/dt_profiles_2008.json). |
| ROC rises from dMAX 0 to 100 and is stable over 100 to 200 | agrees | 2 of 2 fields as printed | Assumed: Top-1-gram profiles built as in the paper's ref. [28] (Liu et al. 2008): PSI-BLAST (BLAST+ 2.17.0) with default settings and 10 iterations against the lab's 2016 nrdb90 (Pse-in-One 2.0); last-round hits with E <= 0.002, rows under 98% identity, Henikoff weights, BLOSUM62 pseudocounts with beta = 10; Top-1-gram = largest target frequency (profile2008.py) |
| (G,G) and (L,L) are the two most discriminative pairs for both methods | agrees | 2 of 2 fields as printed | True for both. For SVM-DT (G,G) and (L,L) are the top two with profiles built as in the paper's ref. [28]; with the earlier 3-iteration profiles (L,L) was sixth, behind (V,G) and (G,V) (output/causes/dt_profiles_2008.json). |
| Distance 0 always has the largest weight (Fig. 5) | agrees | 3 of 3 fields as printed, 1 paper errors | Assumed: Top-1-gram profiles built as in the paper's ref. [28] (Liu et al. 2008): PSI-BLAST (BLAST+ 2.17.0) with default settings and 10 iterations against the lab's 2016 nrdb90 (Pse-in-One 2.0); last-round hits with E <= 0.002, rows under 98% identity, Henikoff weights, BLOSUM62 pseudocounts with beta = 10; Top-1-gram = largest target frequency (profile2008.py) |
| Shorter distances weigh more than longer ones (Fig. 5) | agrees | 4 of 4 fields as printed | Assumed: Top-1-gram profiles built as in the paper's ref. [28] (Liu et al. 2008): PSI-BLAST (BLAST+ 2.17.0) with default settings and 10 iterations against the lab's 2016 nrdb90 (Pse-in-One 2.0); last-round hits with E <= 0.002, rows under 98% identity, Henikoff weights, BLOSUM62 pseudocounts with beta = 10; Top-1-gram = largest target frequency (profile2008.py) |
| Most (G,G) weights of SVM-DT are positive; SVM-DR has more positive ones | agrees | 1 of 1 fields as printed, 1 paper errors | Assumed: Top-1-gram profiles built as in the paper's ref. [28] (Liu et al. 2008): PSI-BLAST (BLAST+ 2.17.0) with default settings and 10 iterations against the lab's 2016 nrdb90 (Pse-in-One 2.0); last-round hits with E <= 0.002, rows under 98% identity, Henikoff weights, BLOSUM62 pseudocounts with beta = 10; Top-1-gram = largest target frequency (profile2008.py) |
| SVM-DR outperforms Monomer-dist and SVM-Pairwise and is comparable with SVM-LA | partly | 2 of 3 fields as printed | SVM-DR beats SVM-Pairwise and is within a point of SVM-LA. 'Outperforms Monomer-dist' rests on ROC50 (both rows print ROC 0.919). With the stated definition SVM-DR is just below Monomer-dist (0.497 against 0.508); with the paper's own ROC50 (an ordinary ROC on the ranking cut at the 50th false positive) it is above (0.712), but Monomer-dist's 0.508 comes from another group's code, so the comparison mixes two ROC50s. |
| SVM-DT outperforms every other method except SVM-PDT-Profile in average ROC | partly | 1 of 2 fields as printed | Our SVM-DT reaches ROC 0.957, above every quoted profile method including SVM-PDT-Profile (0.950), where the paper's 0.948 is below it. Our SVM-DT sits about 0.01 above the paper at every dMAX (profiles from the 2016 nrdb90), enough to change this ranking. With the 3-iteration profiles it was 0.9502, above SVM-PDT-Profile by 0.0002. |

1 exact, 11 agrees, 6 partly, 2 inconclusive, 4 differs, 3 not attempted; 2 open causes.
OK run/results.json: {"items": 27, "exact": 1, "agrees": 11, "partly": 6, "inconclusive": 2, "differs": 4, "not_attempted": 3, "open_causes": 2}

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

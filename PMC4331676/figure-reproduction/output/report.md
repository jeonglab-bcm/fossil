# PMC4331676 reproduction check

## results.json

| Item | Verdict | Measure | Why |
| --- | --- | --- | --- |
| Benchmark and PDB186 sizes | exact | 4 of 4 fields as printed |  |
| Fig. 1, ACC and MCC against LG | partly | 12 of 28 fields as printed | Our curve has the published level (ACC 0.76 to 0.79, MCC 0.53 to 0.59) and is as flat, but single values move by up to 0.02 between 5-fold splits, more than most gaps to the paper. |
| Best LG is 5 (text and Fig. 1) | differs | 0 of 2 fields as printed | No split of ours puts the optimum at LG 5: the best LG is 7, 6, 8, 6 and 7 on five splits, and LG 5 is within 0.02 ACC of the best on every split. The paper's peak at LG 5 is a 0.016 rise over LG 4 that our runs do not show. |
| Table 1, PSSM-DT, PSSM-DDT and PSSM-SDT (jackknife) | differs | 0 of 7 fields as printed, 5 paper errors | PSSM-DT comes back within about 2 points: ACC 78.88 against 79.96, SN 82.10 against 81.91 (one chain more), SP 75.82 against 78.00 (12 chains fewer), AUC 86.34 against 86.50. No value matches at the printed precision. Five printed ACC and MCC values do not follow from the printed SN and SP and are left out of the count. The PSSMs of the 2014 nr cannot be rebuilt; each other unstated setting moves ACC by at most 1.3 points and none closes the gap in all four metrics. |
| Table 2, five PSSM encodings (jackknife) | differs | 0 of 21 fields as printed, 4 paper errors | Our comparator encodings, built as Lou et al. 2014 define them, score far above the paper's in-house versions: AvePscore-20 78.33 ACC and 85.68 AUC against 73.95 and 81.40, Pscore-100 77.40 and 84.53 against 73.12 and 80.50. ACC (73.49 and 81.02 against 73.77 and 81.90) and AvePscore-400 come closer. The paper's implementations are not given beyond citations, so its lead of 6 ACC points shrinks to 0.56 in our run. |
| Table 3, DNAbinder rows (jackknife) | differs | 0 of 9 fields as printed, 1 paper errors | Our comparator encodings, built as Lou et al. 2014 define them, score far above the paper's in-house versions: AvePscore-20 78.33 ACC and 85.68 AUC against 73.95 and 81.40, Pscore-100 77.40 and 84.53 against 73.12 and 80.50. ACC (73.49 and 81.02 against 73.77 and 81.90) and AvePscore-400 come closer. The paper's implementations are not given beyond citations, so its lead of 6 ACC points shrinks to 0.56 in our run. |
| Table 3, DNA-Prot and iDNA-Prot rows | not attempted | not attempted | The paper's in-house DNA-Prot and iDNA-Prot are given only as citations (random forests on composition, predicted secondary structure and physicochemical or grey-model features, settings not stated). A rebuild would test our reading of two other papers, not this one. Their printed ACC does not follow from their own SN and SP (72.55 against 70.98, 75.40 against 74.05). |
| Table 4, the six earlier predictors on PDB186 | exact | 25 of 25 fields as printed, 2 paper errors |  |
| Table 4, PSSM-DT on PDB186 | differs | 0 of 3 fields as printed, 2 paper errors | On PDB186 our model gets ACC 66.13 and AUC 74.44 against the paper's 80.00 and 87.40, below DBPPred (76.88, 79.29). No identity threshold for the homology filter brings it back: AUC stays between 74.4 and 76.0 for thresholds of 25 to 99%, and only training on the unfiltered benchmark, which shares 42 chains with PDB186, reaches 81.49 (87.47 with UniRef90 PSSMs). The paper does not report how many chains its filter removed. |
| Table 4, AUC of iDNA-Prot and DNA-Prot | not attempted | not attempted | Table 4 says its comparator rows come from Lou et al. 2014, but Lou et al. print N/A for the AUC of iDNA-Prot and DNA-Prot and publish no real-valued outputs for them; the 83.30 and 79.60 come from the authors' in-house versions, which are not available. |
| Fig. 2A, discriminant weights of the 400 pairs | differs | 0 of 4 fields as printed | Our largest pair weights are (G,G), (G,D), (G,P) and (N,P); (R,R), (R,P), (P,R) and (A,R) rank 326, 333, 133 and 176 of 400. Products of raw log-odds scores do not grow with arginine content (two negative R scores multiply to a large positive), and no variant of Eq. 12 we tried brings the four pairs to the top. Read as a linear grey scale, the published Fig. 2A itself ranks (A,R) about eighth. |
| Fig. 2B, weights of the top four pairs by lg | partly | 1 of 2 fields as printed | Our largest pair weights are (G,G), (G,D), (G,P) and (N,P); (R,R), (R,P), (P,R) and (A,R) rank 326, 333, 133 and 176 of 400. Products of raw log-odds scores do not grow with arginine content (two negative R scores multiply to a large positive), and no variant of Eq. 12 we tried brings the four pairs to the top. Read as a linear grey scale, the published Fig. 2A itself ranks (A,R) about eighth. |
| Fig. 2C and text, descriptor occurrences on 1AKH chain A | partly | 1 of 4 fields as printed, 1 paper errors | The five occurrences come back; the text gives three of their lags off by one ((R,R) lg 3 for lg 2, (P,R) lg 2 and 3 for lg 3 and 4). Whether all five lie in the DNA-binding region depends on how the region is drawn, which the paper does not say: by contact with the DNA in the crystal structure, (R,R) lg 1 (R25, R26) is 13.2 A away, so four are in and one is out; by the span of contacts, all five are in. |
| Fig. 2D, the occurrences drawn on the 1AKH structure | not attempted | not attempted | A drawing of panel C's occurrences on the 1AKH structure; the distances it illustrates are checked in Fig. 2C. |
| Fig. 3, PSSM-DT ROC curve | partly | 59.81% within 2.0 px (pass 75.0%, best control 54.6%) | Our PSSM-DT curve stays within 2.2 points of true positive rate of the published one (AUC 86.34 against 86.50): equal at 5 and 40% false positives, 1 to 2 points lower between 15 and 30%, where our specificity is lower. At 2 px that is enough to clear the wrong-input control by only a little. Same causes as Table 1. |
| Fig. 3, ACC ROC curve | partly | 63.73% within 2.0 px (pass 75.0%, best control 28.4%) | Our comparator curves lie above the published ones, as the AUCs of Table 2 do (for example AvePscore-20 85.68 against 81.40). The paper's implementations are not given beyond citations, so its lead of 6 ACC points shrinks to 0.56 in our run. |
| Fig. 3, AvePscore-20 ROC curve | differs | 9.91% within 2.0 px (pass 75.0%, best control 35.4%) | Our comparator curves lie above the published ones, as the AUCs of Table 2 do (for example AvePscore-20 85.68 against 81.40). The paper's implementations are not given beyond citations, so its lead of 6 ACC points shrinks to 0.56 in our run. |
| Fig. 3, AvePscore-400 ROC curve | inconclusive | 13.72% within 2.0 px (pass 75.0%, best control 27.4%) | Our comparator curves lie above the published ones, as the AUCs of Table 2 do (for example AvePscore-20 85.68 against 81.40). The paper's implementations are not given beyond citations, so its lead of 6 ACC points shrinks to 0.56 in our run. |
| Fig. 3, Pscore-100 ROC curve | inconclusive | 4.46% within 2.0 px (pass 75.0%, best control 7.6%) | Our comparator curves lie above the published ones, as the AUCs of Table 2 do (for example AvePscore-20 85.68 against 81.40). The paper's implementations are not given beyond citations, so its lead of 6 ACC points shrinks to 0.56 in our run. |
| Fig. 4, PSSM-DT ROC curve | partly | 61.62% within 2.0 px (pass 75.0%, best control 55.5%) | Our PSSM-DT curve stays within 2.2 points of true positive rate of the published one (AUC 86.34 against 86.50): equal at 5 and 40% false positives, 1 to 2 points lower between 15 and 30%, where our specificity is lower. At 2 px that is enough to clear the wrong-input control by only a little. Same causes as Table 1. |
| Fig. 4, DNAbinder(dimension 21) ROC curve | differs | 3.31% within 2.0 px (pass 75.0%, best control 22.2%) | Our comparator curves lie above the published ones, as the AUCs of Table 2 do (for example AvePscore-20 85.68 against 81.40). The paper's implementations are not given beyond citations, so its lead of 6 ACC points shrinks to 0.56 in our run. |
| Fig. 4, DNAbinder(dimension 400) ROC curve | inconclusive | 13.78% within 2.0 px (pass 75.0%, best control 25.0%) | Our comparator curves lie above the published ones, as the AUCs of Table 2 do (for example AvePscore-20 85.68 against 81.40). The paper's implementations are not given beyond citations, so its lead of 6 ACC points shrinks to 0.56 in our run. |
| Fig. 5, PSSM-DT ROC curve | differs | 13.32% within 2.0 px (pass 75.0%, best control 20.0%) | On PDB186 our model gets ACC 66.13 and AUC 74.44 against the paper's 80.00 and 87.40, below DBPPred (76.88, 79.29). No identity threshold for the homology filter brings it back: AUC stays between 74.4 and 76.0 for thresholds of 25 to 99%, and only training on the unfiltered benchmark, which shares 42 chains with PDB186, reaches 81.49 (87.47 with UniRef90 PSSMs). The paper does not report how many chains its filter removed. |
| Fig. 5, DBPPred ROC curve | agrees | 97.44% within 2.0 px (pass 75.0%, best control 38.4%) |  |
| Fig. 5, DNABIND ROC curve | agrees | 78.09% within 2.0 px (pass 75.0%, best control 22.7%) |  |
| Fig. 5, DNAbinder ROC curve | agrees | 82.22% within 2.0 px (pass 75.0%, best control 16.3%) |  |
| Fig. 4, DNA-Prot and iDNA-Prot ROC curves | not attempted | not attempted | The DNA-Prot and iDNA-Prot curves come from the authors' in-house versions of those predictors, which were not rebuilt (Table 3). |
| Fig. 5, DNA-Prot and iDNA-Prot ROC curves | not attempted | not attempted | The DNA-Prot and iDNA-Prot curves come from the authors' in-house versions of those predictors, which were not rebuilt (Table 3). |
| Fig. 6, the web server's home page | not attempted | not attempted | A screenshot of the web server, which no longer answers. |
| PSSM-DT beats the four other encodings and its two halves (text, Tables 1 to 3) | partly | 4 of 6 fields as printed | Our comparator encodings, built as Lou et al. 2014 define them, score far above the paper's in-house versions: AvePscore-20 78.33 ACC and 85.68 AUC against 73.95 and 81.40, Pscore-100 77.40 and 84.53 against 73.12 and 80.50. ACC (73.49 and 81.02 against 73.77 and 81.90) and AvePscore-400 come closer. The paper's implementations are not given beyond citations, so its lead of 6 ACC points shrinks to 0.56 in our run. |
| PSSM-DT is best on PDB186 (text, Table 4) | differs | 0 of 4 fields as printed, 2 paper errors | On PDB186 our model gets ACC 66.13 and AUC 74.44 against the paper's 80.00 and 87.40, below DBPPred (76.88, 79.29). No identity threshold for the homology filter brings it back: AUC stays between 74.4 and 76.0 for thresholds of 25 to 99%, and only training on the unfiltered benchmark, which shares 42 chains with PDB186, reaches 81.49 (87.47 with UniRef90 PSSMs). The paper does not report how many chains its filter removed. |
| Claims recomputed from the paper's own tables | agrees | 20 of 38 claims recomputed from the paper's own tables come back; the other 18 do not follow from the printed numbers (run/arithmetic.json) |  |
| PSSM-DT as in the authors' later toolkit (BioSeq-Analysis2.0) | agrees | pssmdt.pssm_dt equals the transliterated BioSeq-Analysis2.0 loops on 127 PSSMs (largest relative difference 0.0e+00) |  |
| Python package pssmdt and its tutorial | agrees | pssmdt 0.1.0: wheel installed in a fresh environment and imported from it; tests 6 passed; tutorial 7 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |  |

2 exact, 6 agrees, 7 partly, 3 inconclusive, 10 differs, 6 not attempted; 18 open causes.
OK results.json: {"items": 34, "exact": 2, "agrees": 6, "partly": 7, "inconclusive": 3, "differs": 10, "not_attempted": 6, "open_causes": 18}

## Fresh run against the committed outputs

| File | Fresh vs committed | Detail |
| --- | --- | --- |
| homology_removed.tsv | same |  |
| results.json | same |  |
| sensitivity.json | same |  |
| run/akh.json | same |  |
| run/arithmetic.json | same |  |
| run/benchmark.json | same |  |
| run/benchmark_decisions.json | same |  |
| run/datasets.json | same |  |
| run/definition_check.json | same |  |
| run/independent.json | same |  |
| run/lg_sweep.json | same |  |
| run/lou.json | same |  |
| run/pdb186_decisions.json | same |  |
| run/published_values.json | same |  |
| run/weights.json | same |  |
| figures/fig1_ours.png | same |  |
| figures/fig1_overlay.png | same |  |
| figures/fig2_ours.png | same |  |
| figures/fig2_overlay.png | same |  |
| figures/fig3_ours.png | same |  |
| figures/fig3_overlay.png | same |  |
| figures/fig4_ours.png | same |  |
| figures/fig4_overlay.png | same |  |
| figures/fig5_ours.png | same |  |
| figures/fig5_overlay.png | same |  |
| figures/scores.json | same |  |

26 of 26 files agree.

PASS

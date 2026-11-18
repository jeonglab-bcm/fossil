# PMC3392844: Large-scale prediction of adverse drug reactions (Liu et al. 2012)

Liu M, Wu Y, Chen Y, Sun J, Zhao Z, Chen XW, Matheny ME, Xu H. Large-scale prediction of adverse drug
reactions using chemical, biological, and phenotypic properties of drugs. *Journal of the American
Medical Informatics Association* 19(e1):e28-e35 (2012).
[doi:10.1136/amiajnl-2011-000699](https://doi.org/10.1136/amiajnl-2011-000699),
[PMC3392844](https://pmc.ncbi.nlm.nih.gov/articles/PMC3392844/), issue #93.

The paper is an open-access article under
[CC BY-NC 2.0](https://creativecommons.org/licenses/by-nc/2.0/). This folder does not contain the paper, its
full text or its supplement. `figure-reproduction/published/` holds crops of its Figs 2-5, rendered from the
PMC PDF at 600 dpi for comparison, redistributed for non-commercial use with the attribution above.
`figure-reproduction/output/published_values.json` holds the printed numbers of Tables 1-4 and S1 and of the
text, and `published_curves.json` the ROC curves of Figs 2-4 read from the PDF's vector paths, both made by
`extract_published.py`.

The paper predicts each of 1,385 adverse drug reactions (ADRs) of 832 drugs with one classifier per ADR,
from 881 chemical substructures, 1,142 biological features (targets, transporters, enzymes, pathways) and
2,253 phenotypic features (indications and the drug's other ADRs), and compares feature sets (Table 2,
Figs 2 and 3) and five algorithms (Table 3, Fig. 4) by micro-averaged ROC over fivefold cross-validation.
Its pipeline was never released. The authors' training file, with every feature bit and the fold of each
drug for each ADR, survives in the supplement of Zhang et al. 2015
([PMC4634905](https://pmc.ncbi.nlm.nih.gov/articles/PMC4634905/), CC BY 4.0), who received it from the
authors. We rebuilt the method from the paper's text as the Python package [`package/`](package/)
(`adrfusion`) and reran every model on that file.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | The Nextflow pipeline: the downloads, every model on every ADR and fold, the tables, the figures redrawn on the published frames, the claims, the checks. |
| [`package/`](package/) | `adrfusion`, the method as an installable Python package, with example data, tests and an [executed tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every figure, table and claim of the paper, with our values and computed verdicts. |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

Results page: <https://jeonglab-bcm.github.io/fossil/PMC3392844/>

## Results

<!-- summary from results.json (check_results.py); the full table, with the causes: figure-reproduction/README.md -->

<!--RESULTS-SUMMARY-->
3 exact, 7 agrees, 17 partly, 6 differs, 3 not attempted; 21 open causes.

| Item | Verdict | Measure |
| --- | --- | --- |
| Fig. 1, the surveillance framework | not attempted | not attempted |
| Table 1, feature dimensions | exact | 7 of 7 fields as printed |
| Table 2, SVM by feature set, all ADRs | partly | 5 of 24 fields as printed |
| Table 2, SVM by feature set, ADR_50+ | partly | 1 of 24 fields as printed |
| Table 3, SVM row | partly | 1 of 8 fields as printed |
| Table 3, RF row | differs | 0 of 8 fields as printed |
| Table 3, KNN row | partly | 3 of 8 fields as printed |
| Table 3, NB row | differs | 0 of 8 fields as printed |
| Table 3, LR row | differs | 0 of 8 fields as printed |
| Fig. 2, ROC curves of six feature sets, all ADRs (drawn) | agrees | 100.00% within 2 px (pass 95.0%, best control 56.0%) |
| Fig. 2, ROC curves of six feature sets, all ADRs, TPR at five FPRs read from the vector curves | agrees | 30 of 30 fields as printed |
| Fig. 3, ROC curves of six feature sets, ADR_50+ (drawn) | partly | 87.04% within 2 px (pass 95.0%, best control 37.5%) |
| Fig. 3, ROC curves of six feature sets, ADR_50+, TPR at five FPRs read from the vector curves | partly | 26 of 30 fields as printed |
| Fig. 4, ROC curves of five algorithms (drawn) | partly | 77.36% within 2 px (pass 95.0%, best control 50.8%) |
| Fig. 4, ROC curves of five algorithms, TPR at five FPRs read from the vector curves | partly | 17 of 25 fields as printed |
| Fig. 5, overlap of true positives of chem, bio and pheno | differs | 0 of 7 fields as printed |
| Table 4, clinical validation calls (cerivastatin, rofecoxib) | partly | 36 of 39 fields as printed |
| Table S1, share of informative features (chi-square p < 0.05) | partly | 1 of 7 fields as printed |
| SIDER: 888 drugs, 1385 side-effect terms, 61 102 associations, 68.8 side effects per drug | exact | 4 of 4 fields as printed |
| 832 drugs (56 of SIDER's 888 unmapped) with 1385 ADRs; 4276 = 881 + 1142 + 2253 features | exact | 5 of 5 fields as printed |
| Main claim: adding biological and phenotypic features to chemical structures raises AUC from 0.9054 to 0.9524, precision from 43.37% to 66.17% and recall from 49.25% to 63.06% | partly | 1 of 6 fields as printed |
| Feature assessment: pheno has the highest AUC alone; adding bio raises AUC by 0.004 (0.02 for ADR_50+), precision by ~3% and recall by ~1%; adding pheno raises precision by ~21% and recall by ~15% | partly | 6 of 7 fields as printed |
| KS tests on per-ADR AUCs (Bonferroni-corrected): chem to chem+bio p = 1.45E-07 and chem to chem+bio+pheno p = 1.10E-15, both significant; the drop from pheno to chem+bio+pheno is not (p = 0.177) | partly | 3 of 6 fields as printed |
| chem+bio+pheno has a lower global AUC than pheno alone, and its ROC curve almost overlaps that of chem+pheno | agrees | 2 of 2 fields as printed |
| Over the common ADRs (ADR_50+) AUC and accuracy fall for every feature set, and the curves separate more | agrees | 7 of 7 fields as printed |
| Method comparison: SVM performs best, followed by RF, KNN, NB and LR; SVM's precision (66.17%) and recall (63.06%) beat RF's (63.10%, 62.50%) | partly | 3 of 4 fields as printed |
| Discussion: indications alone added to chemical structures raise AUC from 0.9054 to 0.9110 | differs | 0 of 1 fields as printed |
| Discussion: class weights (1 - class share) raise RF's AUC from 0.9491 to 0.9524; SVM does not improve | partly | 1 of 3 fields as printed |
| Discussion: nausea and headache co-occur in 596 drugs; 49 pairs of ADRs co-occur in more than 400 drugs; 554 ADRs have fewer than five drugs (about 1:166 positives to negatives) | partly | 1 of 4 fields as printed |
| Clinical validation: chem detects 1 of 7 rhabdomyolysis ADRs and 0 of 4 heart-attack ADRs, chem+bio 5 and 0, chem+bio+pheno 5 and 2; every classifier detects both grouped ADRs | partly | 4 of 7 fields as printed |
| Discussion and Fig. 5: 5072 true positives come from chem or bio but not pheno, 10 581 from pheno alone | differs | 0 of 2 fields as printed |
| Chem-only AUC 0.9054 'similar to' Pauwels et al.'s 0.8930 | not attempted | not attempted |
| Claims recomputed from the paper's own tables | agrees | 44 of 44 statements follow from the paper's own tables and figures. |
| The recovered training file is the paper's | agrees | The recovered file has 59,205 positive (drug, ADR) pairs; Fig. 5's true positives over Table 2's recalls imply chem 59,214, bio 59,205, pheno 59,201, all within 0.1%. |
| The authors' code | not attempted | not attempted |
| Python package adrfusion and its tutorial | agrees | adrfusion 0.1.0: wheel installed in a fresh environment and imported from it; tests 6 passed; tutorial 6 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |
<!--/RESULTS-SUMMARY-->

Verdicts compare our value with the paper's at its printed precision (four decimals for Tables 2 and 3).

**What came back.** Table 1's dimensions and the text's dataset counts, exactly. Fig. 2, whose six ROC
curves overlay ours. Fig. 3, but for its chem curve. The SVM, random forest and KNN curves of Fig. 4. 36 of
39 calls of Table 4. Every claim recomputed from the paper's own tables, and the identity of the training
file: Fig. 5's true positives divided by Table 2's recalls give 59,201 to 59,214 positive pairs; the file
has 59,205.

**What came back close, but not in the printed digits.** Every AUC of Table 2 is within 0.0005 of the
paper's, every precision and recall within 0.0124, but only 6 of its 48 cells match at four decimals. The
SVM, random forest and KNN rows of Table 3 are within 0.0013 in AUC, and match in 1, 0 and 3 of 8 cells.

**Settings the paper does not state**, found by testing them against its tables: the SVM's scores are
LIBSVM's probability estimates (decision values give chem an AUC near 0.79, not 0.9054); ACC is read at the
maximum-accuracy point of the global ROC, precision and recall at the maximum-F1 point; KNN scores the share
of positive neighbours, ties included.

**What did not, and why.** The fourth decimals of Tables 2 and 3: the SVM's probability fit draws a
random internal split. Over four seeds it moves our AUCs by up to 0.0003 and precision and recall by up to
0.025, and the paper's value lies inside our seed range in 26 of 48 Table 2 cells. The rest is not
explained; the official LIBSVM build does not close it. The LR and NB rows of Table 3 and their curves in
Fig. 4: no LIBLINEAR setting we tried gives the paper's LR, and CLOP, the package of its naive Bayes, is gone.
Fig. 3's chem curve is not Table 2's chem row: its area is 0.7558, Table 2 prints 0.7659, and ours is 0.7658.
Fig. 5's counts differ by up to 9% (bio alone 804 against 884). Table S1 matches for targets only (chem
10.9% against 5.0%). The KS p-values keep their significance calls but not their size. Class weights lower
our RF's AUC (0.9483 against 0.9488) where the paper's rose to 0.9524. Three counts of the Discussion
differ by 1 to 6 (598, 50 and 560 against 596, 49 and 554). Each cause, with the hypotheses tested, is in
`results.json`.

<!--CLAIMS-LINE-->The main claim holds in direction, not in the printed digits: in our run adding biological and phenotypic features to chemical structures raises AUC from 0.9054 to 0.9525, precision from 43.32% to 65.31% and recall from 49.48% to 63.84% (paper 0.9054 to 0.9524, 43.37% to 66.17%, 49.25% to 63.06%). The claims that do not match come from the seed of the SVM's probability fit and the unstated cut-off rule, the unstated variant of the KS test, the LR and NB settings, the class weighting of RF (our AUC falls), small differences in three counts of the recovered file, the unstated threshold of Table 4 and the precision and recall points behind Fig. 5.<!--/CLAIMS-LINE-->

Kept local and gitignored: `sources/` (the paper, its PDF, XML and supplement, the figure JPEGs, Zhang et
al.'s supplement), `work/` (exploration runs) and `.venv/`.

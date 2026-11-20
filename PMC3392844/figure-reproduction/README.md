# PMC3392844 figure reproduction

Liu M, Wu Y, Chen Y, Sun J, Zhao Z, Chen XW, Matheny ME, Xu H. Large-scale prediction of adverse drug
reactions using chemical, biological, and phenotypic properties of drugs. *J Am Med Inform Assoc*
19(e1):e28-e35 (2012). [doi:10.1136/amiajnl-2011-000699](https://doi.org/10.1136/amiajnl-2011-000699).
CC BY-NC 2.0.

`published/fig2.png` to `fig5.png` are the paper's figures (CC BY-NC 2.0, attribution above), cropped from
the PMC PDF at 600 dpi. Nothing else of the paper is in this folder. The training data are downloaded by
`pipeline/fetch_inputs.sh` from Zhang et al. 2015's Additional file 1 (PMC4634905, CC BY 4.0) and checked by
SHA-256; they are not committed.

## Results

<!-- full table from results.json (check_results.py --markdown); regenerate with pipeline/update_readmes.py -->

<!--RESULTS-TABLE-->
3 exact, 14 agrees, 11 partly, 5 differs, 3 not attempted; 21 open causes; 7 verdicts set by a reviewer.

| Item | Verdict | Measure | Why |
| --- | --- | --- | --- |
| Fig. 1, the surveillance framework | not attempted | not attempted | A diagram. |
| Table 1, feature dimensions | exact | 7 of 7 fields as printed |  |
| Table 2, SVM by feature set, all ADRs | agrees | 5 of 24 fields as printed; computed partly, reviewer agrees | 5 of 24 fields at printed precision; largest gap chem+bio|all|recall: 0.513183 against 0.5008. Every AUC within 0.0005 and every precision and recall within 0.0124 of the paper. Over four seeds of the SVM's probability fit our AUCs move by up to 0.0003 and precision and recall by up to 0.0249; the paper's value lies inside our seed range in 26 of 48 Table 2 cells. The rest of the gap is not explained: the official LIBSVM build was tested and does not close it. |
| Table 2, SVM by feature set, ADR_50+ | partly | 1 of 24 fields as printed | 1 of 24 fields at printed precision; largest gap chem+bio|50+|recall: 0.580091 against 0.5728. Every AUC within 0.0005 and every precision and recall within 0.0124 of the paper. Over four seeds of the SVM's probability fit our AUCs move by up to 0.0003 and precision and recall by up to 0.0249; the paper's value lies inside our seed range in 26 of 48 Table 2 cells. The rest of the gap is not explained: the official LIBSVM build was tested and does not close it. |
| Table 3, SVM row | agrees | 1 of 8 fields as printed; computed partly, reviewer agrees | 1 of 8 fields at printed precision; largest gap svm|all|precision: 0.653118 against 0.6617. Every AUC within 0.0005 and every precision and recall within 0.0124 of the paper. Over four seeds of the SVM's probability fit our AUCs move by up to 0.0003 and precision and recall by up to 0.0249; the paper's value lies inside our seed range in 26 of 48 Table 2 cells. The rest of the gap is not explained: the official LIBSVM build was tested and does not close it. |
| Table 3, RF row | differs | 0 of 8 fields as printed | 0 of 8 fields at printed precision; largest gap rf|all|recall: 0.619137 against 0.625. Not explained: two scikit-learn seeds differ by 0.0002 in AUC and both fall below the paper; WEKA itself was not rerun. |
| Table 3, KNN row | partly | 3 of 8 fields as printed | 3 of 8 fields at printed precision; largest gap knn|50+|recall: 0.641302 against 0.6401. WEKA's neighbour search order cannot be replayed exactly. |
| Table 3, NB row | differs | 0 of 8 fields as printed | 0 of 8 fields at printed precision; largest gap nb|50+|precision: 0.529946 against 0.3929. CLOP's naive Bayes settings are not stated. |
| Table 3, LR row | differs | 0 of 8 fields as printed | 0 of 8 fields at printed precision; largest gap lr|all|precision: 0.59159 against 0.4152. No LIBLINEAR setting tried gives the paper's row. |
| Fig. 2, ROC curves of six feature sets, all ADRs (drawn) | agrees | 100.00% within 2 px (pass 95.0%, best control 56.0%) | Assumed: SVM scores are LIBSVM probability estimates (-b 1).; Published curves read from the PDF's vector paths; axes span the curves' corners. |
| Fig. 2, ROC curves of six feature sets, all ADRs, TPR at five FPRs read from the vector curves | agrees | 30 of 30 fields as printed | Assumed: SVM scores are LIBSVM probability estimates (-b 1).; Published curves read from the PDF's vector paths; axes span the curves' corners. |
| Fig. 3, ROC curves of six feature sets, ADR_50+ (drawn) | partly | 87.04% within 2 px (pass 95.0%, best control 37.5%) | curves within 2 px: chem 19.0%, bio 99.0%, pheno 100.0%, chem+bio 99.9%, chem+pheno 100.0%, chem+bio+pheno 100.0%. The published chem curve has area 0.7558; Table 2 prints 0.7659, ours 0.7658. |
| Fig. 3, ROC curves of six feature sets, ADR_50+, TPR at five FPRs read from the vector curves | partly | 26 of 30 fields as printed | 26 of 30 fields at printed precision; largest gap chem at FPR 0.05: 0.321346 against 0.2899. The published chem curve has area 0.7558; Table 2 prints 0.7659, ours 0.7658. |
| Fig. 4, ROC curves of five algorithms (drawn) | partly | 77.36% within 2 px (pass 95.0%, best control 50.8%) | curves within 2 px: svm 100.0%, rf 99.9%, knn 100.0%, nb 45.3%, lr 47.2%. NB and LR as in Table 3. |
| Fig. 4, ROC curves of five algorithms, TPR at five FPRs read from the vector curves | partly | 17 of 25 fields as printed | 17 of 25 fields at printed precision; largest gap lr at FPR 0.01: 0.475163 against 0.0531. NB and LR as in Table 3. |
| Fig. 5, overlap of true positives of chem, bio and pheno | differs | 0 of 7 fields as printed | 0 of 7 fields at printed precision; largest gap pheno: 10944 against 10581. Counts at the max-F1 points move with the precision and recall cells. |
| Table 4, clinical validation calls (cerivastatin, rofecoxib) | agrees | 36 of 39 fields as printed; computed partly, reviewer agrees | 36 of 39 fields at printed precision; not: Cerivastatin|Myopathy|chem, Cerivastatin|Myositis|chem+bio, Rofecoxib|Group above ADRs|chem. The paper does not state the decision threshold. |
| Table S1, share of informative features (chi-square p < 0.05) | partly | 1 of 7 fields as printed | 1 of 7 fields at printed precision; largest gap ade: 68.9011 against 78.4. Counting rule unstated. |
| SIDER: 888 drugs, 1385 side-effect terms, 61 102 associations, 68.8 side effects per drug | exact | 4 of 4 fields as printed |  |
| 832 drugs (56 of SIDER's 888 unmapped) with 1385 ADRs; 4276 = 881 + 1142 + 2253 features | exact | 5 of 5 fields as printed |  |
| Main claim: adding biological and phenotypic features to chemical structures raises AUC from 0.9054 to 0.9524, precision from 43.37% to 66.17% and recall from 49.25% to 63.06% | agrees | 1 of 6 fields as printed; computed partly, reviewer agrees | 1 of 6 fields at printed precision; largest gap precision chem+bio+pheno: 65.3118 against 66.17. Every AUC within 0.0005 and every precision and recall within 0.0124 of the paper. Over four seeds of the SVM's probability fit our AUCs move by up to 0.0003 and precision and recall by up to 0.0249; the paper's value lies inside our seed range in 26 of 48 Table 2 cells. The rest of the gap is not explained: the official LIBSVM build was tested and does not close it. |
| Feature assessment: pheno has the highest AUC alone; adding bio raises AUC by 0.004 (0.02 for ADR_50+), precision by ~3% and recall by ~1%; adding pheno raises precision by ~21% and recall by ~15% | agrees | 6 of 7 fields as printed; computed partly, reviewer agrees | 6 of 7 fields at printed precision; largest gap precision gain of bio (about, points): 1.81855 against 3. Every AUC within 0.0005 and every precision and recall within 0.0124 of the paper. Over four seeds of the SVM's probability fit our AUCs move by up to 0.0003 and precision and recall by up to 0.0249; the paper's value lies inside our seed range in 26 of 48 Table 2 cells. The rest of the gap is not explained: the official LIBSVM build was tested and does not close it. |
| KS tests on per-ADR AUCs (Bonferroni-corrected): chem to chem+bio p = 1.45E-07 and chem to chem+bio+pheno p = 1.10E-15, both significant; the drop from pheno to chem+bio+pheno is not (p = 0.177) | partly | 3 of 6 fields as printed | 3 of 6 fields at printed precision; largest gap chem to chem+bio+pheno, log10 p: -188.915 against -14.96. All three significance calls match; the p-values depend on the per-ADR AUCs and the unstated test variant. |
| chem+bio+pheno has a lower global AUC than pheno alone, and its ROC curve almost overlaps that of chem+pheno | agrees | 2 of 2 fields as printed | Assumed: SVM scores are LIBSVM probability estimates (-b 1). |
| Over the common ADRs (ADR_50+) AUC and accuracy fall for every feature set, and the curves separate more | agrees | 7 of 7 fields as printed | Assumed: SVM scores are LIBSVM probability estimates (-b 1). |
| Method comparison: SVM performs best, followed by RF, KNN, NB and LR; SVM's precision (66.17%) and recall (63.06%) beat RF's (63.10%, 62.50%) | partly | 3 of 4 fields as printed | 3 of 4 fields at printed precision; not: order by AUC over all ADRs. LR and NB rows differ (see Table 3). |
| Discussion: indications alone added to chemical structures raise AUC from 0.9054 to 0.9110 | agrees | 0 of 1 fields as printed; computed differs, reviewer agrees | 0 of 1 fields at printed precision; largest gap AUC of chem+indication: 0.911063 against 0.911. AUC 0.9111 against 0.9110, a gap smaller than the seed range of our AUCs (0.0003). |
| Discussion: class weights (1 - class share) raise RF's AUC from 0.9491 to 0.9524; SVM does not improve | partly | 1 of 3 fields as printed | 1 of 3 fields at printed precision; largest gap AUC of weighted RF: 0.948334 against 0.9524. Weighted RF AUC 0.9483 against unweighted 0.9488. |
| Discussion: nausea and headache co-occur in 596 drugs; 49 pairs of ADRs co-occur in more than 400 drugs; 554 ADRs have fewer than five drugs (about 1:166 positives to negatives) | agrees | 1 of 4 fields as printed; computed partly, reviewer agrees | 1 of 4 fields at printed precision; largest gap ADRs with fewer than five drugs: 560 against 554. Counts on the 832-drug file differ slightly. |
| Clinical validation: chem detects 1 of 7 rhabdomyolysis ADRs and 0 of 4 heart-attack ADRs, chem+bio 5 and 0, chem+bio+pheno 5 and 2; every classifier detects both grouped ADRs | partly | 4 of 7 fields as printed | 4 of 7 fields at printed precision; largest gap Cerivastatin detected by chem: 2 against 1. The paper does not state the decision threshold. |
| Discussion and Fig. 5: 5072 true positives come from chem or bio but not pheno, 10 581 from pheno alone | differs | 0 of 2 fields as printed | 0 of 2 fields at printed precision; largest gap pheno only: 10944 against 10581. Counts at the max-F1 points move with the precision and recall cells. |
| Chem-only AUC 0.9054 'similar to' Pauwels et al.'s 0.8930 | not attempted | not attempted | 0.8930 is Pauwels et al.'s result; our chem AUC is in Table 2. |
| Claims recomputed from the paper's own tables | agrees | 44 of 44 statements follow from the paper's own tables and figures. |  |
| The recovered training file is the paper's | agrees | The recovered file has 59,205 positive (drug, ADR) pairs; Fig. 5's true positives over Table 2's recalls imply chem 59,214, bio 59,205, pheno 59,201, all within 0.1%. |  |
| The authors' code | not attempted | not attempted | Never released (fossil issue #93 lists the search). Rebuilt from the text as adrfusion and checked against the paper only. |
| Python package adrfusion and its tutorial | agrees | adrfusion 0.1.0: wheel installed in a fresh environment and imported from it; tests 6 passed; tutorial 6 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |  |
<!--/RESULTS-TABLE-->

<!--CLAIMS-LINE-->The main claim holds: in our run adding biological and phenotypic features to chemical structures raises AUC from 0.9054 to 0.9525, precision from 43.32% to 65.31% and recall from 49.48% to 63.84% (paper 0.9054 to 0.9524, 43.37% to 66.17%, 49.25% to 63.06%). The claims that do not match come from the unstated variant of the KS test, the LR and NB settings, the class weighting of RF (our AUC falls), the unstated threshold of Table 4 and the precision and recall points behind Fig. 5.<!--/CLAIMS-LINE-->

## What the code does, against the paper

| Paper | Here |
| --- | --- |
| 832 drugs, 1,385 ADRs, 4,276 binary features; for ADR j the "other side effects" are the other 1,384 ADRs | The authors' file `random_group_cv_data.indication`; the other ADRs of j are the label columns but j |
| Fivefold cross-validation per ADR | The authors' folds, the last field of their file (a fold for every drug and ADR) |
| LIBSVM, RBF kernel, g = 0.008, C = 2 | scikit-learn's libsvm on a precomputed RBF kernel built from per-block Hamming distances (the same kernel; the package tests it against the official LIBSVM) |
| Scores merged into one global ROC (not stated which) | Platt probabilities (LIBSVM `-b 1`) |
| ACC, precision and recall at the "best cut-off points" | ACC at the maximum-accuracy point, precision and recall at the maximum-F1 point |
| LIBLINEAR LR, C = 10, epsilon = 1 | scikit-learn's liblinear, no bias term |
| CLOP naive Bayes (settings not stated) | Bernoulli naive Bayes, smoothing 1 |
| WEKA KNN, k = 55; WEKA RF, 100 trees | share of positives among the 55 nearest (ties included); scikit-learn RF, 13 features per split |
| KS test on per-ADR AUCs, Bonferroni-corrected | One-sided two-sample KS, times 3 (the comparisons the paper reports) |
| Clinical validation: train on the other drugs, predict cerivastatin and rofecoxib | The same, Yes when the probability is above 0.5 |
| Chi-square test of each feature against each ADR, p < 0.05 (Table S1) | The same, shares of informative (feature, ADR) pairs |

## Layout

```text
figure-reproduction/
├── main.nf, nextflow.config, requirements.txt
├── results_notes.json          labels, assumptions and causes of results.json (written by hand)
├── pipeline/
│   ├── fetch_inputs.sh         downloads and SHA-256 checks
│   ├── extract_published.py    the paper's printed values, vector curves and figure crops (--extract)
│   ├── run_models.py           every model on every ADR and fold, through adrfusion
│   ├── evaluate.py             metrics, ROC curves, Tables 1-3, S1, Fig. 5 counts, KS tests
│   ├── table4.py, claims.py    Table 4 and the claims of the text
│   ├── figures.py              our curves on the published frames, pixel scores and controls
│   ├── seed_spread.py          Table 2 over SVM seeds 0-3 (--full)
│   ├── hypotheses.py           the variants behind the causes (--full)
│   ├── build_results.py        results.json from the notes and the run
│   ├── build_page.py           the results page
│   ├── check_reproduction.py   fresh run against the committed outputs
│   └── check_results.py, compare_runs.py, check_package.py   from Paper2Repro
├── published/                  the paper's Figs 2-5 at 600 dpi
└── output/                     every number and render of the run
```

## Run

From the repository root (Python 3.12, Java 21, Nextflow 26.04.3):

```bash
pip install -r PMC3392844/figure-reproduction/requirements.txt ./PMC3392844/package
```

```bash
nextflow run PMC3392844/figure-reproduction/main.nf --outdir results
```

`--full` also reruns SVM seeds 1-3 and the hypothesis variants (about 25 minutes more; otherwise the
committed `seed_spread.json` and `hypotheses.json` are used). `--extract` downloads the paper again and
checks that its values, curves and figure crops equal the committed ones (needs `poppler-utils`).

## Pipeline steps

1. `FETCH`: Zhang et al. 2015's Additional file 1, SHA-256 checked; the authors' training file from inside it.
2. `PUBLISHED`: the committed published values and curves (or extracted again with `--extract`).
3. `RUN_SVM`, `RUN_METHODS`: every model of Tables 2 and 3, the indication-only set and the class-weighted SVM and RF.
4. `EVALUATE`, `TABLE4`, `FIGURES`, `CLAIMS`: every compared number, the renders and overlays.
5. `SEEDS`, `HYPOTHESES`: committed, or rerun with `--full`.
6. `PACKAGE`: `check_package.py` on `adrfusion`.
7. `RESULTS`: `results.json`, the results page, `figure-reproduction/results.json`, and the check against the committed outputs.
8. `CHECK`: fails the run when any check fails.

## Limits

- The authors' code is lost, so the method is rebuilt from the text and checked against the paper only.
- `output/offline_checks.json` records two one-off checks that are not part of the pipeline: the official
  LIBSVM C library with a fresh `rand()` seed per model, and RF with another seed.
- The LR and NB rows are not reproduced; the settings behind them are not stated, and CLOP is no longer available.
- The precision, recall and Table 4 calls depend on cut-off rules the paper does not state.

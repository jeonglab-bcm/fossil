# PMC522806 figure reproduction

The combinational feature selection and ensemble neural network method of Liu, Cui, Jiang and Ma
(2004) rerun on the seven Kent Ridge datasets, and every table, figure and claim compared with the
paper. The method is the package [`../package`](../package) (`cfsenn`), rebuilt from the paper's text;
the pipeline calls it and holds no second copy.

## Results

<!-- table from results.json (check_results.py --markdown); do not edit by hand -->
<!--RESULTS-TABLE-->
8 exact, 2 agrees, 6 partly, 3 differs, 4 not attempted; 8 open causes.

| Item | Verdict | Measure | Why |
| --- | --- | --- | --- |
| Table 1, the seven datasets (genes, training and test samples per class) | exact | 32 of 32 fields as printed |  |
| Fig. 1 (flow chart) | not attempted | not attempted | A flow chart of the method; there is nothing to recompute. |
| Fig. 2 (the three networks) | not attempted | not attempted | A diagram of the three networks; there is nothing to recompute. |
| Table 2, our methods: test-set accuracy (ALL-AML, lung, prostate) | partly | 1 of 3 fields as printed | Lung comes back (149 of 149). Prostate: 31 of 34 against 33; scaling each array to the same mean intensity, a step the paper does not mention, gives exactly 33 of 34 on all five seeds, so the gap is likely how the test experiment, about 12 times brighter than the training arrays, was handled. ALL-AML: 33 of 34 against 34; the same test sample (31st in the file) is wrong in every seed and every hypothesis test (only the AdaBoost control gets it right, missing another). |
| Table 2, LOOCV on the training samples | partly | 1 of 3 fields as printed | Lung comes back (32 of 32). ALL-AML 37 of 38 against 38 (training sample 29 is wrong in both runs we made), prostate 95 of 102 against 98. Weight decay 0.1 gains one prostate sample (96); no other setting we tried moves either. |
| Table 2, bagged decision trees and the best methods (quoted) | not attempted | not attempted | Accuracies quoted from Tan and Gilbert (2003) and other papers, not results of this paper. They stay as published in Fig. 3. |
| Fig. 3, 'Our method' bars (test sets) | partly | 1 of 3 fields as printed | The 'Our method' bars are Table 2's test accuracies (see table2.test): lung comes back; prostate is two samples short as found and back to 33 of 34 with per-array scaling; ALL-AML is one sample short. The published bars are drawn at their labels (within 0.25 points). |
| Table 3, LOOCV (DLBCL, ovarian, colon) | partly | 1 of 3 fields as printed | DLBCL comes back (46 of 47). Ovarian 252 of 253 against 251, one sample better. Colon 54 of 62 against 57; none of eight variants moves colon above 54. |
| Table 3, 10-fold CV (DLBCL, ovarian, colon) | partly | 1 of 3 fields as printed | DLBCL comes back (45 of 47). Ovarian 251 of 253 against the printed 98.82%, which is not a whole count of 253 (250/253 = 98.81%, our third fold assignment). Colon 54 of 62 against 56 (53 to 54 over three fold assignments). |
| Table 3, other methods (quoted) | not attempted | not attempted | Accuracies quoted from Dettling and Buhlmann (colon, 85.48%) and Liu, Li and Wong (ovarian, 100%), not results of this paper. |
| Fig. 4, 'OurMethod' bars (DLBCL 22/25 split, ovarian 10-fold, colon LOOCV) | differs | 0 of 3 fields as printed | DLBCL on 22/25 splits: 89.6% over 20 random splits (72% to 100%; one split gives 25 of 25), against 98%; Cho and Won's samples are not listed, and 98% is not a whole count of 25. Ovarian and colon bars as in Table 3. The published ovarian bar is drawn at 99.25%, 0.43 above its label 98.82% and close to the LOOCV 99.21% (the other bars of this figure sit up to 0.36 off their labels). |
| Text: MLL, 15 of 15 test samples correct | exact | 1 of 1 fields as printed |  |
| Text: 75 features in all | exact | 1 of 1 fields as printed |  |
| Claims recomputed from the paper's own tables | agrees | 7 of 7 claims come back from the paper's own tables. 11 of 12 printed accuracies are whole counts of samples; not a whole count: Ovarian 98.82% of 253. Fig. 4's 98% on 25 test samples is not a whole count either (24/25 = 96, 25/25 = 100). |  |
| Text and Fig. 3: better than bagged decision trees on all three test sets | exact | 3 of 3 fields as printed |  |
| Text: better than the best cited method on all three test sets | partly | 2 of 3 fields as printed | Our ALL-AML test accuracy (33 of 34) equals the best cited method's 97.06% instead of beating it; lung and prostate hold. Follows table2.test. |
| Text: prostate LOOCV a little lower than its test accuracy | differs | 0 of 1 fields as printed | Our prostate LOOCV (93.14%) is above our test accuracy as found (91.18%). With per-array scaling the test accuracy is 97.06% on all five seeds, above our LOOCV, the order the paper reports: the claim turns on the test-set scaling (see table2.test). |
| Text: colon LOOCV better than Dettling and Buhlmann's boosting (85.48%) | exact | 1 of 1 fields as printed |  |
| Text: DLBCL on the 22/25 split better than Cho and Won's 96% | differs | 0 of 1 fields as printed | Our mean over 20 random 22/25 splits is 89.6%, below Cho and Won's 96%; see fig4. |
| Discussion: random genes in place of the selected features classify worse | exact | 1 of 1 fields as printed |  |
| Discussion: a single network on all the same features classifies worse | exact | 1 of 1 fields as printed |  |
| Discussion and Methods: AdaBoost in place of bagging classifies worse | exact | 1 of 1 fields as printed |  |
| Python package cfsenn and its tutorial | agrees | cfsenn 0.1.0: wheel installed in a fresh environment and imported from it; tests 8 passed; tutorial 5 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |  |
<!--/RESULTS-TABLE-->

Each accuracy is a count of samples, so one sample moves the ALL-AML and prostate test sets by 2.9
points and colon by 1.6. How much a rerun moves (seeds 0 to 4 on the test sets, three fold
assignments for 10-fold CV, 20 random DLBCL splits) is in `output/tables.json` and on the results
page. The hypothesis tests (`hyp.*` in `output/accuracy.json`) each change one setting; they explain
gaps and are never counted as agreement.

<!--CLAIMS-LINE-->
The main claim holds in part: our ensemble beats the bagged trees on all three test sets and each Discussion control classifies worse, but it only ties the best cited method on ALL-AML, its prostate LOOCV is not below its test accuracy, and it falls short of Cho and Won's DLBCL split; the causes are one ALL-AML test sample that every seed and hypothesis test misses, the unscaled prostate test arrays and the unlisted 22/25 split.
<!--/CLAIMS-LINE-->

## What the code does, against the paper

| Paper | Here |
| --- | --- |
| Kent Ridge "transformed" data, used as found | the same files from the University of Granada mirror (Elvira `.dbc`), parsed as found; every count of Table 1 checked (`fetch_inputs.sh`, `cfsenn.read_dbc`) |
| 100 bootstrap resamples (bagging); features selected on each resample | the same; a resample without two samples of every class is drawn again (`cfsenn.Ensemble`) |
| top 30 genes by Wilcoxon rank-sum test | Mann-Whitney z on average ranks; Kruskal-Wallis for MLL (`cfsenn.ranksum_scores`) |
| top 15 principal components of all genes | genes centred, not scaled; test samples projected on the resample's components |
| Jaeger's "masked out clustering" into 50 clusters, then the top 30 genes by t-test | k-means (k = 50, correlation distance) on the 500 genes with the largest Welch t; genes taken in order of t, each masking the rest of its cluster (`cfsenn.masked_cluster_genes`); not stated in the paper |
| three one-hidden-layer networks, 10 hidden units, one output (one per class for MLL) | tanh hidden units, logistic or softmax output, cross-entropy with weight decay 0.01, L-BFGS for at most 200 iterations, features z-scored on the resample (`cfsenn.Net`); training is not stated in the paper |
| the three confidences averaged; the 100 answers combined by soft voting | the same: the mean class probability over the three networks and the 100 resamples |
| test-set accuracy; LOOCV; 10-fold CV | the same; 10-fold folds stratified by class, three seeded assignments (`cfsenn.stratified_folds`) |
| DLBCL on Cho and Won's 22/25 split | the samples are not listed: 20 random splits with 11 training samples of each class; the bar is their mean |
| MLL "after minor adjustments" | no adjustment beyond the three-class tests and outputs |
| random genes, a single network, AdaBoost: "worse" | `feature_sets=["random"]*3`; one network on all 75 features without resampling; AdaBoost.M1 by weighted resampling. Each on the three test sets and on DLBCL and colon LOOCV |

## Layout

```text
figure-reproduction/
├── main.nf, nextflow.config, requirements.txt
├── results_notes.json        labels, assumptions, causes and page text (written by hand)
├── results.json              the repository's results-check file (tools/check_results.py)
├── pipeline/
│   ├── fetch_inputs.sh       the seven datasets, SHA-256 checked
│   ├── experiments.py        every classification (main runs, controls, hypothesis tests), with cfsenn
│   ├── figures.py            Figs 3 and 4: published bar heights read off, our bars drawn on the published images
│   ├── compare.py            every field and claim against the paper; Tables 1 to 3 for the page
│   ├── build_results.py      results_notes.json + comparison.json -> ../results.json
│   ├── build_page.py, page_template.html   the results page
│   ├── check_reproduction.py the check step
│   ├── make_results_check.py results.json for tools/check_results.py
│   ├── update_readmes.py     the results tables of the READMEs, from ../results.json
│   └── check_results.py, compare_runs.py, check_package.py   copied from Paper2Repro v0.5.0
├── published/                the paper's figures (CC BY 2.0), with the licence note
└── output/                   the committed outputs of a full run (runs/ holds every held-out prediction)
```

## Run

From the repository root, with Python 3.13, the packages in `requirements.txt`, uv, Java 21 and
Nextflow 26.04.3:

```bash
nextflow run PMC522806/figure-reproduction/main.nf --outdir results
```

This reruns every classification except the slow ones: ovarian and prostate-training LOOCV and the
LOOCV hypothesis tests rerun every 25th fold and take the rest from `output/runs`, and the check
step fails if a rerun fold differs from the committed one. About 25 minutes on 4 cores. CI runs the
same command (`.github/workflows/reproduce-pmc522806.yml`) on every change to the paper's folder.
To rerun every fold (about 75 minutes on 4 cores; the workflow's `full` input):

```bash
nextflow run PMC522806/figure-reproduction/main.nf --outdir results --full
```

## Pipeline steps

1. `FETCH`: the seven zip files from the UGR mirror, SHA-256 checked, unpacked.
2. `RUN`: `experiments.py`, about 1,800 ensemble fits in parallel (each fit is 100 resamples × 3 networks), seeded per fold.
3. `FIGURES`: the published bar heights of Figs 3 and 4 read off at their top edges (axis calibrated on the gridlines); our "Our method" bars drawn in their place; overlays.
4. `COMPARE`: every field and claim; the arithmetic check of the claims on the paper's own tables.
5. `PACKAGE`: `check_package.py` on `../package` (fresh install, tests, tutorial rerun).
6. `RESULTS`: `../results.json`, verdicts computed by `check_results.py`.
7. `PAGE`: the results page and `report.md`.
8. `CHECK`: `check_results.py` passes, no verdict changed against the committed `../results.json`, and `compare_runs.py` finds the fresh outputs equal to `output/` (predicted classes exactly, confidences within 2e-6).

## Limits

- The authors' Matlab code is lost, and the paper does not say how the networks were trained or how the genes were clustered. Our choices are in the table above and in `results.json`; none was tuned to the paper's numbers.
- The paper gives no seeds or fold assignments. Single runs are compared; the spread over seeds and folds is reported next to them.
- The samples of Cho and Won's DLBCL split are not listed, and the paper's 98% is not a whole count of 25 test samples.
- The bagged-tree, best-method and other-method rows of Tables 2 and 3 are quoted from other papers and are not rerun.
- The prostate test set comes from a different experiment from its training set: its arrays average about 12 times the training arrays' intensity (median array mean 307.5 against 26.2). Used as found, as the paper says, it costs us two samples; scaled per array it does not (see the cause of `table2.test`).

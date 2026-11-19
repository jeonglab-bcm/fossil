# PMC3098087: Class prediction for high-dimensional class-imbalanced data (Blagus and Lusa 2010)

Blagus R, Lusa L. Class prediction for high-dimensional class-imbalanced data. *BMC Bioinformatics*
11:523 (2010). [doi:10.1186/1471-2105-11-523](https://doi.org/10.1186/1471-2105-11-523) ·
[PMC3098087](https://pmc.ncbi.nlm.nih.gov/articles/PMC3098087/) · issue #69

The paper is © 2010 Blagus and Lusa, licensee BioMed Central, under
[CC BY 2.0](https://creativecommons.org/licenses/by/2.0/). This folder does not contain the paper, its
full text or its supplements (Additional files 1-14). `figure-reproduction/published/` holds the
paper's figures and the supplement figures we compare against, rasterized from the published PDFs and
redistributed under CC BY 2.0 with the attribution above. The plotted values and printed table cells
are in `figure-reproduction/output/published_values.json`, read from the PDFs by
`pipeline/extract_published.py`. The breast cancer data (Sotiriou et al. 2003, NCI BRB data archive)
are downloaded by the pipeline and not kept here.

The paper studies classifiers trained on class-imbalanced, high-dimensional data: nine classifiers
(1-, 3- and 5-NN, DLDA, DQDA, random forest, linear SVM, PAM, penalized logistic regression), t-test
selection of 40 variables, and three corrections (over-sampling, down-sizing and multiple
down-sizing, MultDS), on simulated data (1,000 replicates per setting) and on the Sotiriou breast
cancer data (ER status, 500 random splits per design). It ran in R 2.8.1 and released no code. We
rebuilt the classifiers, corrections, measures and simulation design from the text as the R package
[`package/`](package/) (`multds`), reran 462 simulation settings and 60 breast cancer designs, and
compared the plotted points of Figs 1-6 and of Additional files 4-12 and every printed cell of
Additional files 1, 3, 13 and 14. MultDS was not run for RF, SVM and PAM (nor, with centred
variables, for six classifiers of Additional file 12), to fit the compute budget; those points are
not compared.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | The Nextflow pipeline: the downloads, the published values read from the vector figures and tables, the simulation and the breast cancer analysis, the comparison, our figures on the published frames, the claims, the checks. |
| [`package/`](package/) | `multds`, the method as an installable R package, with example data, tests and a [rendered tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every figure, table and claim of the paper, with our values and computed verdicts. |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

Results page: <https://jeonglab-bcm.github.io/fossil/PMC3098087/>

## Results

<!-- summary from results.json (check_results.py); the full table, with the causes: figure-reproduction/README.md -->

<!--RESULTS-SUMMARY-->
16 exact, 9 agrees, 21 partly, 1 differs, 3 not attempted; 18 open causes.

| Item | Verdict | Measure |
| --- | --- | --- |
| Fig. 1: null case, p = 40, no selection; PA, PA1, PA2 against k1train (nine classifiers) | partly | 473 of 513 fields as printed |
| Fig. 2: null case, G = 40 of p = 40, 1000, 10000; PA1 (nine classifiers) | partly | 469 of 513 fields as printed |
| Fig. 3: alternative case, pDE = 20 or p, G = 40; PA1 (1-NN, DLDA, PLR) | partly | 121 of 270 fields as printed |
| Fig. 4: overall PA against mu2, k1train 0.5-0.9, centred samples or variables (1-NN, DLDA, PLR) | partly | 659 of 660 fields as printed |
| Fig. 5: no correction, over-sampling, down-sizing, MultDS; PA, PA1, PA2 (3-NN, DLDA, PLR) | partly | 625 of 684 fields as printed |
| Fig. 6: ER status, class-specific PA, no correction and MultDS (3-NN, DLDA, PLR), means | agrees | 192 of 192 fields as printed |
| Fig. 6: 95% prediction intervals of the class-specific PA | partly | 377 of 382 fields as printed |
| Additional file 1: null case, p = 40, balanced test sets of 20 and 500; PA, PA1, PA2, PV1, PV2, AUC | exact | 419 of 419 fields as printed, 121 paper errors |
| Additional file 2: eight variable-selection methods under the null and alternative | not attempted | not attempted |
| Additional file 3: alternative case, p = 1000, pDE = 20, mu2 = 1, test sets of 20 and 500; all measures | partly | 500 of 540 fields as printed |
| Additional file 4: Fig. 3 left for all nine classifiers | partly | 241 of 513 fields as printed |
| Additional file 5: Fig. 3 right (pDE = p) for all nine classifiers | partly | 27 of 297 fields as printed |
| Additional file 6: no variable selection (G = p = 1000), Fig. 5 first column; PA, PA1, PA2 (nine classifiers) | partly | 440 of 513 fields as printed |
| Additional file 7: Fig. 4 for all nine classifiers | partly | 1894 of 1980 fields as printed |
| Additional file 8: Fig. 5 for all nine classifiers (MultDS for six) | partly | 1655 of 1881 fields as printed |
| Additional file 9: over-sampling with centred variables, balanced test set; PA, PA1, PA2 (nine classifiers) | partly | 510 of 684 fields as printed |
| Additional file 10: 95% prediction intervals of the overall PA, four corrections (3-NN, DLDA, RF, PLR; MultDS not run for RF) | exact | 554 of 554 fields as printed |
| Additional file 11: RF-THR and PLR-THR; PA, PA1, PA2 | exact | 114 of 114 fields as printed |
| Additional file 12: Fig. 6 for all nine classifiers, 95% prediction intervals (MultDS with centred variables run for 3-NN, DLDA and PLR only) | partly | 930 of 976 fields as printed |
| Additional file 13: ER status, no correction; all measures, nine classifiers | partly | 440 of 486 fields as printed |
| Additional file 14: ER status, MultDS; all measures, nine classifiers | partly | 374 of 378 fields as printed |
| Text: null case, PA = 0.5 and AUC = 0.5 with balanced test sets | exact | 2 of 2 fields as printed |
| Text: 1-NN, k1train 0.1, G = 40: PA1 0.02 / 0.00, PA2 0.98 / 1.00 (p = 1000 / 10000) | exact | 4 of 4 fields as printed |
| Text: variable selection biases most classifiers further towards the majority class | exact | 1 of 1 fields as printed |
| Text: RF, SVM and PAM most sensitive to imbalance without selection | differs | 0 of 1 fields as printed |
| Text: DLDA shows the smallest decrease in minority-class PA | exact | 3 of 3 fields as printed |
| Text: balanced training set, PA reaches 1 at mu2 between 1 and 1.5 | exact | 8 of 8 fields as printed, 1 paper errors |
| Text: highly imbalanced training set needs mu2 >= 2 | exact | 2 of 2 fields as printed, 1 paper errors |
| Text: all non-null variables selected in almost all runs when mu2 >= 1.5 | partly | 4 of 5 fields as printed |
| Text: centring the variables worsens PA on imbalanced data | exact | 3 of 3 fields as printed |
| Text: over-sampling changes little; only 3-NN and 5-NN benefit, 1-NN not at all | partly | 8 of 9 fields as printed |
| Text: down-sizing at k1train 0.1 gives PA about 0.70 in both classes; full data PA1 = 0 | exact | 27 of 27 fields as printed |
| Text: PAM, k1train 0.2, PA1 0.5 to 0.8 with down-sizing | exact | 2 of 2 fields as printed |
| Text: down-sizing prediction intervals 0.8-1.0 (k1train 0.5) and 0.50-0.90 (0.10) | exact | 16 of 16 fields as printed |
| Text: MultDS PA flat for k1train 0.20-0.80 | exact | 5 of 5 fields as printed, 1 paper errors |
| Text: MultDS at k1train 0.1, PA about 0.85, interval 0.7-1.0 | exact | 11 of 11 fields as printed, 1 paper errors |
| Text: MultDS consistently better than down-sizing | exact | 6 of 6 fields as printed |
| Text: RF-THR and PLR-THR reduce but do not remove the dependence on imbalance (null case) | partly | 1 of 2 fields as printed |
| Text: 99 tumours, 7650 probes, ER- 34 / ER+ 65, grade 54 / 45 | agrees | 6 of 6 fields as printed |
| Text: ER, 20 ER+ / 5 ER-: PA ER+ > 0.90, PA ER- 0.2-0.6, PV and AUC ranges | partly | 1 of 3 fields as printed, 3 paper errors |
| Text: ER down-sizing, class-specific PA about 0.75 (5 per class) and 0.85 (10 per class) | agrees | 2 of 2 fields as printed |
| Text: ER over-sampling, gap of 0.22 between class-specific PA (DQDA, 20 ER+ / 10 ER-) | agrees | 1 of 1 fields as printed |
| Text: ER, MultDS lower interval limits above 0.60 for most classifiers; down-sized intervals include 0.50 | partly | 1 of 2 fields as printed, 1 paper errors |
| Text: ER, PAM benefits the most from MultDS | agrees | 1 of 1 fields as printed |
| Text: ER, centring the variables increases the bias | agrees | 3 of 3 fields as printed |
| Text: grade 1-2 against 3: overall PA about 0.60 and 0.70, minority PA 0.10-0.20 | not attempted | not attempted |
| Equations 1-6: classification rules and measures | not attempted | not attempted |
| Claims in the text recomputed from the paper's own figures and tables | agrees | 106 of 114 statements follow from the paper's own figures and tables. Not: text.fig4_balanced: PAM: smallest mu2 with PA >= 0.98 at k1train 0.5 lies in [1, 1.5] (paper says yes, its own values give no); text.fig4_imbalanced: DLDA: smallest mu2 with PA >= 0.98 at k1train 0.9 is at least 2 (paper says yes, its own values give no); text.multds_flat: DQDA: MultDS PA varies by 0.03 or less over k1train 0.20-0.80 (0.5 left out) (paper says yes, its own values give no); text.multds_k01: DQDA: MultDS, k1train 0.1, mean PA (paper says 0.85, its own values give 0.7992); text.er_20_5: PA ER-, smallest of the nine (paper says 0.2, its own values give 0.3); text.er_20_5: PV ER- between 0.7 and 0.8 for all nine (within 0.005) (paper says yes, its own values give no); text.er_20_5: AUC between 0.8 and 0.9 for all nine (within 0.005) (paper says yes, its own values give no); text.er_multds_pi: MultDS, 45 ER+ / 5 ER-: lower limit of the ER- prediction interval above 0.60 for most (5 or more) of the nine (paper says yes, its own values give no). |
| DLDA and DQDA against sma::stat.diag.da (the code the paper used); AUC against Hmisc | agrees | DLDA 18000 and DQDA 18000 of 18000 test-sample predictions identical to sma::stat.diag.da (sma 0.5.15) on 900 simulated training sets; AUC equal to Hmisc::somers2 in 500 tries (largest difference 6e-16); t statistics equal to t.test (largest difference 4e-16) |
| R package multds and its tutorial | agrees | R CMD check: OK; tests [ FAIL 0 |
<!--/RESULTS-SUMMARY-->

<!--CLAIMS-LINE-->
The main conclusions hold in our run: the classifiers are biased towards the majority class,
variable selection adds to the bias, over-sampling helps little for most classifiers, and
down-sizing and above all multiple down-sizing remove most of the bias, on the simulations and the
breast cancer data. The gaps: the SVM (no cost given; no cost and class weighting we tried fits all
its results), PAM (near balance, without selection, and after over-sampling, where the paper's PAM
fits keeping the original class prior), DQDA's AUC (another score), the p = 40 and pDE = p panels of
Fig. 3 and Additional files 4 and 5 (fitted far better without the stated sample centring), RF-THR in
the null case (flat in our run), selection at k1train 0.9, and a few prediction-interval tails. Each
has a cause in [`figure-reproduction/README.md`](figure-reproduction/README.md).
<!--/CLAIMS-LINE-->

## Install the package

```r
remotes::install_github("jeonglab-bcm/fossil/PMC3098087/package")
```

## Run

From the repository root, with R 4.3 and the packages of `package/DESCRIPTION` (Ubuntu 24.04:
`bash PMC3098087/figure-reproduction/pipeline/install_r_deps.sh`), Python 3.12, Java 21 and
Nextflow:

```bash
R CMD INSTALL PMC3098087/package
pip install -r PMC3098087/figure-reproduction/requirements.txt
nextflow run PMC3098087/figure-reproduction/main.nf --outdir results
```

The default run reruns the first 3 replicates of every setting and design from their seeds and
builds everything else from the committed summary of all replicates (about 15 minutes); `--full`
reruns every replicate (about 6 hours on 4 cores). See
[`figure-reproduction/README.md`](figure-reproduction/README.md).

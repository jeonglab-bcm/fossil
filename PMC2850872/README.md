# PMC2850872 — SVM prediction of diabetes and pre-diabetes (Yu et al. 2010)

Yu W, Liu T, Valdez R, Gwinn M, Khoury MJ. Application of support vector machine modeling for prediction
of common diseases: the case of diabetes and pre-diabetes. *BMC Medical Informatics and Decision Making*
10:16 (2010). [doi:10.1186/1472-6947-10-16](https://doi.org/10.1186/1472-6947-10-16) ·
[PMC2850872](https://pmc.ncbi.nlm.nih.gov/articles/PMC2850872/)

The paper is © 2010 Yu et al., licensee BioMed Central Ltd., published under
[CC BY 2.0](https://creativecommons.org/licenses/by/2.0/). In keeping with the rest of this repository,
this folder does not contain the paper or its full text. `figure-reproduction/published/figure-2.jpg` is
the paper's Figure 2, redistributed under CC BY 2.0 with the attribution above.

The NHANES 1999–2004 public-use files (US National Center for Health Statistics, public domain) are
downloaded by the pipeline and checked against SHA-256 sums. `figure-reproduction/output/analytic.csv` is
the analytic data set built from them.

**What was lost:** the "Diabetes Classifier" web tool (hugenavigator.net, gone, no Wayback capture) and
its Java code, which was never released; the paper's random split.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | Table 1 from NHANES; Tables 2 and 3, Figure 2 and the claims in the text over 10 random splits. Nextflow pipeline. |
| [`package/`](package/) | `diabclass`, the method as a Python package, with an executed [tutorial](package/tutorial/TUTORIAL.md): `pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC2850872/package"`. |
| [`results.json`](results.json) | Every figure, table and claim of the paper, with its computed verdict. |

Results page: <https://jeonglab-bcm.github.io/fossil/PMC2850872/>

## Results

<!--RESULTS-->
| Item | Verdict | Measure | Why |
| --- | --- | --- | --- |
| Table 1, people per diabetes category | partly | 1 of 8 fields as printed | Diagnosed diabetes comes back exactly (1,266). The fasting groups are 1, 5 and 5 people off (196, 1,571, 3,272 against 195, 1,576, 3,277), so the scheme I non-cases are 10 off and the scheme II totals 8 and 4 off. No fasting, borderline or missing-value rule we tried closes the gap. The glucose files we used carry revision dates of September 2009 (1999-2000) and March 2007 (2001-2002); whether the authors' copy differed could not be tested. |
| Table 2, test AUC of the four kernels | partly | 6 of 8 fields as printed | Six of the eight AUCs lie within two standard deviations of our median over 10 splits; the paper's scheme I linear, RBF and sigmoid AUCs sit in the upper part of our range. Both polynomial kernels differ: with grid.py's search ours are 0.05 higher (0.8175 and 0.7158 against 0.7655 and 0.6673), and none of our 20 polynomial fits comes as low. Run at LIBSVM's defaults with no search (C = 1, gamma = 1/8 or 1/10), the polynomial kernel gives 0.782 and 0.690, and both published values fall within two standard deviations: the paper's polynomial model was most likely not tuned. |
| Table 3, scheme I (RBF kernel): test, training and 10-fold CV | partly | 9 of 15 fields as printed | 9 of 15 values agree. The training row agrees in full, and four of five test values. The paper's test PPV is higher than any of our splits give (0.4926 against our median 0.4522 and highest 0.4811). Its 10-fold CV values are all below ours, and all but specificity lie outside our split range (AUC 0.8242 against our median 0.8347 and lowest 0.8247), although its test and training AUCs do not. |
| Table 3, scheme II (linear kernel): test, training and 10-fold CV | exact | 14 of 14 fields as printed, 1 paper errors |  |
| Fig. 1 | not attempted | not attempted | A schematic of a separating hyperplane in a higher-dimensional space; there is nothing to recompute. |
| Fig. 2a, ROC curves of scheme I (pixels, split 0) | inconclusive | 28.06% within 2.0 px (pass 90.0%, best control 31.8%) | The paper's curve comes from one unpublished random split. Two random splits differ by about as much as a curve moved 0.03 in sensitivity (12 px here): the near-miss control at +0.03 scores as well as our split 0, so a 2 px score cannot tell them apart. Fig. 2a in data units (fig2.a.values) compares the published curve with the spread of ours over 10 splits instead. |
| Fig. 2b, ROC curves of scheme II (pixels, split 0) | partly | 21.42% within 2.0 px (pass 90.0%, best control 14.5%) | As for Fig. 2a: one unpublished split, and a different split moves the curve by more than the 2 px tolerance; ours beats the controls but reaches only 21%. Fig. 2b in data units (fig2.b.values) compares the published curve with the spread of ours. |
| Fig. 2a, sensitivity at nine false-positive rates (SVM and logistic regression) | partly | 14 of 17 fields as printed | 14 of 17 points agree (the published SVM curve ends before 0.9). The published SVM curve runs above every one of our 10 splits between 1 - specificity 0.3 and 0.5 (sensitivity 0.843, 0.908, 0.951 against our highest 0.829, 0.901, 0.935), as its AUC 0.8347 sits near the top of our range; the logistic curve agrees at all nine points. The paper's split is unpublished. |
| Fig. 2b, sensitivity at nine false-positive rates (SVM and logistic regression) | partly | 16 of 18 fields as printed | 16 of 18 points agree. The published logistic curve starts lower than all of our splits (sensitivity 0.231 at 1 - specificity 0.1 against our lowest 0.257), and the published SVM curve runs just above all of them at 0.8 (0.983 against our highest 0.980). The paper's split is unpublished. |
| Text: logistic regression AUCs 0.8319 and 0.7335 | exact | 2 of 2 fields as printed |  |
| Text: SVM and logistic regression do not differ (DeLong P 0.3672 and 0.6718) | exact | 4 of 4 fields as printed |  |
| Text and Table 2: best and worst kernel per scheme | exact | 4 of 4 fields as printed |  |
| The paper's own numbers: Table 1 sums and the prevalences Table 3 implies | exact | 14 of 14 fields as printed, 1 paper errors |  |
| Our method against R (survey::svyglm, pROC, e1071) on split 0 | agrees | On split 0: logistic coefficients equal to survey::svyglm within 6.9e-12; DeLong P equal to pROC::roc.test within 1.4e-07; SVM test AUC from e1071 (LIBSVM in R) with the same C and gamma 0.8187 against 0.8187, 0.7481 against 0.7481 |  |
| Python package diabclass and its tutorial | agrees | diabclass 0.1.0: wheel installed in a fresh environment and imported from it; tests 6 passed; tutorial 6 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |  |

5 exact, 2 agrees, 6 partly, 1 inconclusive, 1 not attempted; 4 open causes.

For values that depend on the random split (Tables 2 and 3, Fig. 2 values, the logistic AUCs, the DeLong P) "exact" and "fields as printed" mean every value lies within two standard deviations of our median over 10 splits, not equal at printed precision: the paper's split is unpublished.
<!--/RESULTS-->

## Claims

<!--CLAIMS-->
The main claim holds: on both schemes the median AUCs of the SVM and the logistic regression differ by 0.0018 or less, and the DeLong test finds no difference in 8 and 8 of 10 splits. Table 2 agrees for 6 of 8 kernels: the polynomial kernels come back better than published, as an untuned polynomial model explains (item table2); the scheme I 10-fold CV and test PPV of Table 3 differ, cause open (item table3.schemeI).
<!--/CLAIMS-->

Kept local and gitignored: `sources/` (the paper's text, PDF and figures; the NHANES downloads), `work/`
(scratch runs) and `.rlib/` (the local R library).

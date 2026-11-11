# Figure and table reproduction (PMC2850872)

Yu W, Liu T, Valdez R, Gwinn M, Khoury MJ. Application of support vector machine modeling for prediction
of common diseases: the case of diabetes and pre-diabetes. *BMC Medical Informatics and Decision Making*
10:16 (2010). [doi:10.1186/1472-6947-10-16](https://doi.org/10.1186/1472-6947-10-16)

Table 1 rebuilt from the NHANES 1999–2004 public-use files; Tables 2 and 3, Figure 2 and the claims in
the text rerun over 10 random 80/20 splits with the method rebuilt from the paper's text (package
[`diabclass`](../package/)). Every verdict below is computed by `tools/paper2repro/check_results.py`
from [`../results.json`](../results.json). Seven of them were set to agrees in [review](https://github.com/jeonglab-bcm/fossil/pull/37#pullrequestreview-5866132056): their
`review` block in `results_notes.json` keeps the computed verdict, and the check fails if the numbers
later give another one.

## Results

<!--RESULTS-->
| Item | Verdict | Measure | Why |
| --- | --- | --- | --- |
| Table 1, people per diabetes category | agrees | 1 of 8 fields as printed; computed partly, reviewer agrees | Diagnosed diabetes comes back exactly (1,266). The fasting groups are 1, 5 and 5 people off (196, 1,571, 3,272 against 195, 1,576, 3,277), so the scheme I non-cases are 10 off and the scheme II totals 8 and 4 off. No fasting, borderline or missing-value rule we tried closes the gap. The glucose files we used carry revision dates of September 2009 (1999-2000) and March 2007 (2001-2002); whether the authors' copy differed could not be tested. |
| Table 2, test AUC of the four kernels | agrees | 6 of 8 fields as printed; computed partly, reviewer agrees | Six of the eight AUCs lie within two standard deviations of our median over 10 splits; the paper's scheme I linear, RBF and sigmoid AUCs sit in the upper part of our range. Both polynomial kernels differ: with grid.py's search ours are 0.05 higher (0.8175 and 0.7158 against 0.7655 and 0.6673), and none of our 20 polynomial fits comes as low. Run at LIBSVM's defaults with no search (C = 1, gamma = 1/8 or 1/10), the polynomial kernel gives 0.782 and 0.690, and both published values fall within two standard deviations: the paper's polynomial model was most likely not tuned. |
| Table 3, scheme I (RBF kernel): test, training and 10-fold CV | agrees | 9 of 15 fields as printed; computed partly, reviewer agrees | 9 of 15 values agree. The training row agrees in full, and four of five test values. The paper's test PPV is higher than any of our splits give (0.4926 against our median 0.4522 and highest 0.4811). Its 10-fold CV values are all below ours, and all but specificity lie outside our split range (AUC 0.8242 against our median 0.8347 and lowest 0.8247), although its test and training AUCs do not. |
| Table 3, scheme II (linear kernel): test, training and 10-fold CV | exact | 14 of 14 fields as printed, 1 paper errors |  |
| Fig. 1 | not attempted | not attempted | A schematic of a separating hyperplane in a higher-dimensional space; there is nothing to recompute. |
| Fig. 2a, ROC curves of scheme I (pixels, split 0) | agrees | 28.06% within 2.0 px (pass 90.0%, best control 31.8%); computed inconclusive, reviewer agrees | The paper's curve comes from one unpublished random split. Two random splits differ by about as much as a curve moved 0.03 in sensitivity (12 px here): the near-miss control at +0.03 scores as well as our split 0, so a 2 px score cannot tell them apart. Fig. 2a in data units (fig2.a.values) compares the published curve with the spread of ours over 10 splits instead. |
| Fig. 2b, ROC curves of scheme II (pixels, split 0) | agrees | 21.42% within 2.0 px (pass 90.0%, best control 14.5%); computed partly, reviewer agrees | As for Fig. 2a: one unpublished split, and a different split moves the curve by more than the 2 px tolerance; ours beats the controls but reaches only 21%. Fig. 2b in data units (fig2.b.values) compares the published curve with the spread of ours. |
| Fig. 2a, sensitivity at nine false-positive rates (SVM and logistic regression) | agrees | 14 of 17 fields as printed; computed partly, reviewer agrees | 14 of 17 points agree (the published SVM curve ends before 0.9). The published SVM curve runs above every one of our 10 splits between 1 - specificity 0.3 and 0.5 (sensitivity 0.843, 0.908, 0.951 against our highest 0.829, 0.901, 0.935), as its AUC 0.8347 sits near the top of our range; the logistic curve agrees at all nine points. The paper's split is unpublished. |
| Fig. 2b, sensitivity at nine false-positive rates (SVM and logistic regression) | agrees | 16 of 18 fields as printed; computed partly, reviewer agrees | 16 of 18 points agree. The published logistic curve starts lower than all of our splits (sensitivity 0.231 at 1 - specificity 0.1 against our lowest 0.257), and the published SVM curve runs just above all of them at 0.8 (0.983 against our highest 0.980). The paper's split is unpublished. |
| Text: logistic regression AUCs 0.8319 and 0.7335 | exact | 2 of 2 fields as printed |  |
| Text: SVM and logistic regression do not differ (DeLong P 0.3672 and 0.6718) | exact | 4 of 4 fields as printed |  |
| Text and Table 2: best and worst kernel per scheme | exact | 4 of 4 fields as printed |  |
| The paper's own numbers: Table 1 sums and the prevalences Table 3 implies | exact | 14 of 14 fields as printed, 1 paper errors |  |
| Our method against R (survey::svyglm, pROC, e1071) on split 0 | agrees | On split 0: logistic coefficients equal to survey::svyglm within 7e-12; DeLong P equal to pROC::roc.test within 1.4e-07; SVM test AUC from e1071 (LIBSVM in R) with the same C and gamma 0.8187 against 0.8187, 0.7481 against 0.7481 |  |
| Python package diabclass and its tutorial | agrees | diabclass 0.1.0: wheel installed in a fresh environment and imported from it; tests 6 passed; tutorial 6 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |  |

5 exact, 9 agrees, 1 not attempted; 4 open causes; 7 verdicts set by a reviewer.

For values that depend on the random split (Tables 2 and 3, Fig. 2 values, the logistic AUCs, the DeLong P) "exact" and "fields as printed" mean every value lies within two standard deviations of our median over 10 splits, not equal at printed precision: the paper's split is unpublished.
<!--/RESULTS-->

## What the code does, against the paper

| Step | Paper | Here |
| --- | --- | --- |
| Population | NHANES 1999–2004, non-pregnant, aged 20 or over. | `RIDAGEYR >= 20`, `RIDEXPRG != 1`. |
| Diagnosed diabetes | "Yes" to "ever told … diabetes". | `DIQ010 = 1`. Borderline (`3`) counts as not diagnosed. |
| Fasting groups | Fasting plasma glucose ≥ 126, 100–125, < 100 mg/dl. | `LBXGLU`, people who fasted at least 8 hours (`PHAFSTHR`). |
| Missing values | Not stated; Table 1's scheme I totals equal the category sums. | Complete cases on the scheme I variables; scheme II also drops missing physical activity. |
| Variables | Family history, age, race and ethnicity, weight, height, waist, BMI, hypertension; scheme II adds sex and physical activity. | `MCQ250A`, `RIDAGEYR`, `RIDRETH1`, `BMXWT`, `BMXHT`, `BMXWAIST`, `BMXBMI`, `BPQ020`, `RIAGENDR`, `PAD320`. "Don't know" counts as no. |
| Coding | Race −1, −0.5, 0, 0.5, 1; age / 100; others divided "by an appropriate number". | Weight, height, waist / 200; BMI / 100; yes 1, no −1. |
| Split | 80% of each group to training, 20% to test; one random split. | 10 random splits (seeds 0 to 9). |
| Training sample | All cases and as many random non-cases. | Same. |
| C and gamma | LIBSVM `grid.py`, 5-fold CV. | grid.py's default grid and accuracy, through scikit-learn's LIBSVM; fits inside the search stop at 1,000,000 iterations. |
| Kernels | Linear, polynomial, sigmoid, RBF; degree and coef0 not given. | LIBSVM defaults (degree 3, coef0 0). |
| Table 3 | Test, training and 10-fold CV; cutoff 0. | Training row: the whole training set (scheme I) or the balanced sample (scheme II), the set each row's PPV implies. 10-fold CV reuses the split's C and gamma. |
| Logistic regression | SUDAAN 9 on the training set, survey design. | Weighted maximum likelihood with the six-year examination weights, fitted to the whole training set; equal to `survey::svyglm` (checked). |
| Comparison | DeLong test. | `delong_test`, equal to `pROC::roc.test` (checked). |
| Figure 2 | ROC curves of SVM and logistic regression on the test set. | Split 0, drawn on the published pixel grid. |

## Layout

| Path | Content |
| --- | --- |
| `main.nf`, `nextflow.config` | The pipeline. |
| `requirements.txt` | Pinned Python packages. |
| `results_notes.json` | Labels, sources, assumptions and causes, written by hand; merged with the run into `../results.json`. |
| `results.json` | The values CI checks against each run (`tools/check_results.py`). |
| `pipeline/fetch_inputs.sh`, `pipeline/inputs/nhanes_files.tsv` | Download the 33 NHANES files and check their SHA-256. |
| `pipeline/cohort.py` | The analytic data set and Table 1, with the definition variants tried. |
| `pipeline/run_models.py` | Splits, grid search, SVMs, Table 3 rows, logistic regression, DeLong tests, ROC curves. |
| `pipeline/r_check.R` | Our logistic regression, DeLong test and SVM against `survey`, `pROC` and `e1071`. |
| `pipeline/compare_fig2.py` | Figure 2 on the published grid, scores, controls, sensitivities read off the figure. |
| `pipeline/make_tables.py`, `pipeline/make_results.py` | Summaries against the paper; `results.json`. |
| `pipeline/check_reproduction.py` | The check step. |
| `pipeline/build_page.py`, `pipeline/page_template.html` | The results page. |
| `published/figure-2.jpg` | The paper's Figure 2 (CC BY 2.0, see the paper's README). |
| `output/` | What the pipeline writes: `analytic.csv`, `table1.json`, `grid.csv`, `table2_reps.csv`, `table3_reps.csv`, `mlr_reps.csv`, `roc_rep0.csv`, `roc_at_fpr_reps.csv`, `r_check.json`, `fig2_*`, `tables.json`, `package.json`, `report.md`. |

## Run

From the repository root, with Python 3.13.18 (`pip install -r PMC2850872/figure-reproduction/requirements.txt ./PMC2850872/package`),
R with `survey`, `pROC`, `e1071` and `jsonlite`, uv, Java 21 and Nextflow 26.04.3:

```sh
nextflow run PMC2850872/figure-reproduction/main.nf --outdir results            # about 10 minutes
nextflow run PMC2850872/figure-reproduction/main.nf --outdir results --search   # with grid.py's search, about 80 minutes on 4 cores
```

The first run uses the C and gamma of the committed search (`output/grid.csv`) and recomputes everything
else. `.github/workflows/reproduce-pmc2850872.yml` runs it on every pull request that touches this folder;
the search runs only when the workflow is started by hand with `search = true`.

## Pipeline steps

1. `FETCH`: the 33 NHANES files from wwwn.cdc.gov, SHA-256 checked.
2. `COHORT`: `analytic.csv` and `table1.json`.
3. `MODELS`: for each scheme and split, the four kernels (Table 2), the Table 3 rows of the paper's best kernel, the logistic regression and the DeLong test.
4. `R_CHECK`: split 0 against R.
5. `FIG2`: render, overlay, scores and controls; published sensitivities at nine false-positive rates.
6. `TABLES`, `PACKAGE`, `RESULTS`: summaries, `check_package.py`, `results.json` with computed verdicts.
7. `CHECK`: `check_results.py` passes, the run equals the committed outputs (`compare_runs.py`, numbers to 2e-6) and `results.json`; `report.md`.
8. `BUILD_PAGE`: `site/index.html`, copied to `site/PMC2850872/`.

`package.json` holds timings and temporary paths and is checked by its `passed` flag only. `output/hypotheses.json` is not written by the pipeline: it records the hypothesis tests behind the Table 2 cause (`pipeline/hypotheses.py`, about 30 minutes on 4 cores).

## Limits

<!--LIMITS-->
- **One split against ten.** The paper reports one random split; ours are the median and spread of ten. A value
  agrees when the paper's lies within two standard deviations of our median, the range one split lands in
  about 95% of the time. The DeLong P varies so much between splits (0.006 to 0.97 for scheme I) that its
  field agrees trivially; the call that matters is whether P falls below 0.05, which it does in 2 of 10
  splits for each scheme.
- **Choices the paper does not make.** The NHANES items for family history (`MCQ250A`), hypertension
  (`BPQ020`) and physical activity (`PAD320`, chosen by the scheme II totals), the divisors for weight,
  height, waist and BMI, the polynomial kernel's degree and coef0, and the survey weight are ours. Each is an
  assumption in `../results.json`.
- **Grid search.** Fits inside the search stop at 1,000,000 iterations; LIBSVM 2.89 had no limit. On
  split 0 of scheme I the linear kernel's search with a 10,000,000 limit chose the same C.
- **LIBSVM version.** scikit-learn 1.5.2 wraps a modified LIBSVM 3.x; the paper used a LIBSVM release of
  2009. `r_check.R` shows that `e1071`'s LIBSVM gives the same test AUC with the same C and gamma.
- **SUDAAN.** Not available. Its point estimates equal a weighted maximum-likelihood fit, which we check
  against `survey::svyglm`; the AUC and the DeLong test use only the point estimates.
- **Figure 2 pixels.** At 473 × 841 px a 2 px tolerance is 0.005 in sensitivity, smaller than the
  difference between two random splits, so the pixel items cannot single out the paper's split. The
  data-unit items `fig2.a.values` and `fig2.b.values` carry the comparison.
- **Nextflow.** The session that built this ran the pipeline's steps by hand with the same commands;
  the workflow runs `main.nf` itself.
<!--/LIMITS-->

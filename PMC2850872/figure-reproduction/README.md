# Figure and table reproduction (PMC2850872)

Yu W, Liu T, Valdez R, Gwinn M, Khoury MJ. Application of support vector machine modeling for prediction
of common diseases: the case of diabetes and pre-diabetes. *BMC Medical Informatics and Decision Making*
10:16 (2010). [doi:10.1186/1472-6947-10-16](https://doi.org/10.1186/1472-6947-10-16)

Table 1 rebuilt from the NHANES 1999–2004 public-use files; Tables 2 and 3, Figure 2 and the claims in
the text rerun over 10 random 80/20 splits with the method rebuilt from the paper's text (package
[`diabclass`](../package/)). Every verdict below is computed by `tools/paper2repro/check_results.py`
from [`../results.json`](../results.json).

## Results

<!--RESULTS-->

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

From the repository root, with Python 3.12 (`pip install -r PMC2850872/figure-reproduction/requirements.txt ./PMC2850872/package`),
R with `survey`, `pROC`, `e1071` and `jsonlite`, uv, Java 21 and Nextflow 26.04.3:

```sh
nextflow run PMC2850872/figure-reproduction/main.nf --outdir results            # about 10 minutes
nextflow run PMC2850872/figure-reproduction/main.nf --outdir results --search   # with grid.py's search, about 3 hours on 4 cores
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

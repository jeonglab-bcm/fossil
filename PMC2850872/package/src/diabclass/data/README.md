# Example data

| File | What it is |
| --- | --- |
| `nhanes_example.csv` | Example input: 440 adults from NHANES 1999-2004, scheme I. Columns `id`, `set` (train/test), `case` (1 diabetes, diagnosed or undiagnosed; 0 otherwise), `family_history`, `age`, `race`, `weight`, `height`, `waist`, `bmi`, `hypertension`, `weight_mec6`. The training rows are balanced (100 cases, 100 non-cases); the test rows hold 60 cases and 180 non-cases. |
| `nhanes_example_expected_svm.csv` | Expected SVM decision value of each test row (RBF kernel, C = 2, gamma = 2, stopping tolerance 1e-5). |
| `nhanes_example_expected.json` | Expected weighted logistic regression coefficients (intercept first), the test AUCs of the SVM and the logistic regression, and the DeLong p-value comparing them. |

## Where it comes from

- Input: drawn at random (seed 2010) by `scripts/make_example_data.py` from the analytic data set the reproduction builds (`PMC2850872/figure-reproduction/pipeline/cohort.py`) from the NHANES public-use files of the US National Center for Health Statistics. NHANES public-use data are in the public domain. Weights are rounded to 0.1.
- Expected output: computed in R by `scripts/expected_from_r.R`, independently of this package: the SVM with `e1071` 1.7-17 (LIBSVM's C++ code), the logistic regression with `survey` 4.5 (`svyglm`, quasibinomial), and the AUCs and DeLong test with `pROC` 1.19.1, under R 4.3.3.
- Licence: public domain (NHANES); the derived files are released with the package under its licence.

Compare SVM decision values within 1e-4 (two LIBSVM builds, each stopping at tolerance 1e-5), logistic coefficients within 1e-8, AUCs within 1e-12 and the DeLong p within 1e-9.

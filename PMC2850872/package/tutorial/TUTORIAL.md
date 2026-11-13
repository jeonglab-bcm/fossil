<!-- Generated from tutorial.ipynb by check_package.py --write. Do not edit by hand. -->

# diabclass tutorial

`diabclass` classifies people as likely to have diabetes (or pre-diabetes) from simple variables that need no laboratory test: family history, age, race and ethnicity, weight, height, waist, BMI and hypertension (plus sex and physical activity for pre-diabetes). It trains a support vector machine (LIBSVM, through scikit-learn) on all cases and an equal number of randomly drawn non-cases, chooses C and gamma by LIBSVM's `grid.py` search, and scores people by the SVM decision value. It also fits the survey-weighted logistic regression the paper compares against, and the DeLong test of the two AUCs.

The method is from Yu W, Liu T, Valdez R, Gwinn M, Khoury MJ. Application of support vector machine modeling for prediction of common diseases: the case of diabetes and pre-diabetes. *BMC Medical Informatics and Decision Making* 10:16 (2010). [doi:10.1186/1472-6947-10-16](https://doi.org/10.1186/1472-6947-10-16). The authors' web tool, "Diabetes Classifier", is gone; this package is rebuilt from the paper's text.

## 1. Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC2850872/package"
```

```python
import diabclass as dc

print("diabclass", dc.__version__)
```

```text
diabclass 0.1.0
```

## 2. The example input

The package ships 440 adults from NHANES 1999-2004 (public domain), coded for classification scheme I (diabetes, diagnosed or undiagnosed, against everyone else). The 200 training rows are already balanced (100 cases, 100 non-cases); the 240 test rows hold 60 cases and 180 non-cases. `weight_mec6` is the six-year NHANES examination weight.

```python
path = dc.example_path("nhanes_example.csv")
rows = dc.read_records(path)
train = [r for r in rows if r["set"] == "train"]
test = [r for r in rows if r["set"] == "test"]
print(len(rows), "rows; columns:", ", ".join(rows[0]))
for r in rows[:3]:
    print(r)
```

```text
440 rows; columns: id, set, case, family_history, age, race, weight, height, waist, bmi, hypertension, weight_mec6
{'id': '1', 'set': 'train', 'case': '1', 'family_history': '1', 'age': '65', 'race': 'mexican_american', 'weight': '88.5', 'height': '176.9', 'waist': '104.2', 'bmi': '28.28', 'hypertension': '0', 'weight_mec6': '1296.6'}
{'id': '2', 'set': 'train', 'case': '1', 'family_history': '1', 'age': '46', 'race': 'mexican_american', 'weight': '69.4', 'height': '148.6', 'waist': '94.5', 'bmi': '31.43', 'hypertension': '1', 'weight_mec6': '2443.1'}
{'id': '3', 'set': 'train', 'case': '1', 'family_history': '0', 'age': '68', 'race': 'mexican_american', 'weight': '67.2', 'height': '149.1', 'waist': '99.3', 'bmi': '30.23', 'hypertension': '1', 'weight_mec6': '845.9'}
```

## 3. Run the method

`encode` codes the variables into [-1, 1] as the paper does (race as -1, -0.5, 0, 0.5, 1; age / 100; the other measurements divided by a fixed number). `SVMClassifier` balances the training set and fits the SVM. Here C and gamma are given (C = 2, gamma = 2, an RBF kernel) so that the result can be compared with an independent run; leave them out and the classifier runs `grid.py`'s search instead.

```python
X_train, y_train = dc.encode(train, "I"), dc.labels(train)
X_test, y_test = dc.encode(test, "I"), dc.labels(test)

svm = dc.SVMClassifier("rbf", C=2, gamma=2, tol=1e-5).fit(X_train, y_train)
score = svm.decision_function(X_test)
m = dc.classification_metrics(y_test, score, cutoff=0)
print(f"SVM test AUC {m['auc']:.4f}; at cutoff 0: sensitivity {m['sensitivity']:.4f}, "
      f"specificity {m['specificity']:.4f}, PPV {m['ppv']:.4f}, NPV {m['npv']:.4f}")

w = [float(r["weight_mec6"]) for r in train]
beta = dc.weighted_logistic(X_train, y_train, w)
p = dc.logistic_probability(X_test, beta)
d = dc.delong_test(y_test, score, p)
print(f"logistic regression test AUC {d['auc2']:.4f}; DeLong p = {d['p']:.4f}")
```

```text
SVM test AUC 0.7907; at cutoff 0: sensitivity 0.6833, specificity 0.7167, PPV 0.4457, NPV 0.8716
logistic regression test AUC 0.8026; DeLong p = 0.6446
```

A search over a small grid (the full `grid.py` grid, 11 x 10 points with 5-fold cross-validation, takes about a minute on this example):

```python
g = dc.grid_search(X_train, y_train, "rbf", log2c=[-1, 1, 3], log2g=[1, -1, -3], seed=0)
print(f"best C = {g.C:g}, gamma = {g.gamma:g}, 5-fold CV accuracy {g.cv_accuracy:.3f}")
```

```text
best C = 0.5, gamma = 0.5, 5-fold CV accuracy 0.675
```

## 4. Compare with the expected output

The expected output was computed in R by `scripts/expected_from_r.R`, independently of this package: the SVM with `e1071` (LIBSVM's C++ code), the logistic regression with `survey::svyglm`, and the AUCs and DeLong test with `pROC`.

```python
import json

import numpy as np

with open(dc.example_path("nhanes_example_expected.json")) as f:
    e = json.load(f)
dv = np.array([float(r["decision_value"]) for r in dc.read_records(dc.example_path("nhanes_example_expected_svm.csv"))])

checks = {
    "SVM decision values (240, within 1e-4)": np.allclose(score, dv, atol=1e-4, rtol=0),
    "logistic coefficients (9, within 1e-8)": np.allclose(beta, e["beta"], atol=1e-8, rtol=0),
    "SVM AUC": abs(m["auc"] - e["auc_svm"]) < 1e-12,
    "logistic AUC": abs(d["auc2"] - e["auc_logistic"]) < 1e-12,
    "DeLong p (within 1e-9)": abs(d["p"] - e["delong_p"]) < 1e-9,
}
for k, v in checks.items():
    print("match" if v else "DIFFERS", k)
print(f"{sum(checks.values())} of {len(checks)} checks match the expected output")
assert all(checks.values())
```

```text
match SVM decision values (240, within 1e-4)
match logistic coefficients (9, within 1e-8)
match SVM AUC
match logistic AUC
match DeLong p (within 1e-9)
5 of 5 checks match the expected output
```

## 5. From the command line

`diabclass` trains on the rows with `set` = train and writes the decision value of each test row. It prints the kernel, C, gamma and the test AUC to standard error.

```python
!diabclass "{path}" --C 2 --gamma 2 -o decision_values.csv
print(open("decision_values.csv").read().splitlines()[:4])
```

```text
kernel rbf, C 2, gamma 2, test AUC 0.7905
['id,decision_value,case', '201,1.05168354,1', '202,1.073647995,1', '203,-0.7757049716,1']
```

## 6. Your own data

- **Input:** a CSV with one person per row and the columns `family_history` (1/0), `age` (years), `race` (`nh_white`, `nh_black`, `mexican_american`, `other`, `other_hispanic`), `weight` (kg), `height` (cm), `waist` (cm), `bmi` (kg/m²) and `hypertension` (1/0, ever told of high blood pressure). Scheme II adds `sex` (male/female) and `physical_activity` (1/0). Add `set` (train/test) and, for training rows, `case` (1/0) for the command line.
- **Options:** `kernel` (the paper found RBF best for scheme I and linear for scheme II); `C` and `gamma` (leave out to search); `seed` for the balanced sample and the folds; `cutoff` for `classification_metrics` (0 by default, as in the paper).
- **Output:** the decision value: positive means classified as a case. Higher values mean more likely a case; move the cutoff to trade sensitivity for specificity.
- The divisors for weight, height, waist and BMI (200, 200, 200, 100) are our choice; the paper gives only age / 100.

## 7. The reproduction

The paper's full analysis (Tables 1 to 3 and Figure 2, from the NHANES files) is rerun by the pipeline in [`PMC2850872/figure-reproduction`](https://github.com/jeonglab-bcm/fossil/tree/main/PMC2850872/figure-reproduction); the results page is at <https://jeonglab-bcm.github.io/fossil/PMC2850872/>.

# diabclass

Support vector machine classifiers of diabetes and pre-diabetes from simple variables that need no laboratory test, with the survey-weighted logistic regression and DeLong test the paper compares them by. Rebuilt from the text of:

> Yu W, Liu T, Valdez R, Gwinn M, Khoury MJ. Application of support vector machine modeling for prediction of common diseases: the case of diabetes and pre-diabetes. *BMC Medical Informatics and Decision Making* 10:16 (2010). [doi:10.1186/1472-6947-10-16](https://doi.org/10.1186/1472-6947-10-16)

The authors' web tool ("Diabetes Classifier") and code were never released, and the tool is gone. Its reproduction (pipeline, results and comparison with the published tables and figure) is in [`PMC2850872`](https://github.com/jeonglab-bcm/fossil/tree/main/PMC2850872).

## Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC2850872/package"
```

Python 3.10 or later, with NumPy, SciPy, scikit-learn and joblib.

**Language: Python.** No code of the authors exists to port. The method rests on LIBSVM, which scikit-learn wraps, and on a weighted logistic regression and the DeLong test, which take a few lines of NumPy and SciPy. By the default rule (R only when the method relies on R packages), that is Python.

## Use

```python
import diabclass as dc

rows = dc.read_records(dc.example_path())               # the bundled example input
train = [r for r in rows if r["set"] == "train"]
test = [r for r in rows if r["set"] == "test"]
svm = dc.SVMClassifier("rbf").fit(dc.encode(train, "I"), dc.labels(train))   # grid.py search
score = svm.decision_function(dc.encode(test, "I"))     # > 0: classified as a case
print(dc.classification_metrics(dc.labels(test), score))
```

From the command line:

```bash
diabclass "$(diabclass --example-path)" --kernel rbf -o decision_values.csv
```

The [tutorial](tutorial/TUTORIAL.md) installs the package, runs it on the example, compares the result with an independent R run (LIBSVM through `e1071`, `survey::svyglm`, `pROC`) and explains the input and output.

## What the paper gives and what we chose

| Step | Paper | Here |
| --- | --- | --- |
| Variables | Scheme I: family history, age, race and ethnicity, weight, height, waist, BMI, hypertension. Scheme II adds sex and physical activity. | Same (`SCHEME_FEATURES`). |
| Coding | Race -1, -0.5, 0, 0.5, 1 (non-Hispanic white, non-Hispanic black, Mexican American, other, other Hispanic); age / 100; others "divided by an appropriate number". | Weight / 200, height / 200, waist / 200, BMI / 100 (our choice); yes = 1, no = -1. |
| Training sample | All cases and as many random non-cases. | `undersample`. |
| C and gamma | `grid.py`, 5-fold CV. | `grid_search`: log2 C from -5 to 15, log2 gamma from 3 to -15, step 2 (grid.py defaults); accuracy; ties to the smaller C. |
| Kernels | Linear, polynomial, sigmoid, RBF. | LIBSVM defaults: degree 3, coef0 0. |
| Score | SVM decision value, cutoff 0. | `decision_function`, `classification_metrics`. |
| Logistic regression | SUDAAN 9, survey design. | `weighted_logistic`: the same point estimates as a design-based fit (checked against `survey::svyglm`). |
| Comparison | DeLong test. | `delong_test` (checked against `pROC::roc.test`). |

## Licence

MIT. See [LICENSE](LICENSE). The example data (public domain, NHANES) are described in [data/README.md](src/diabclass/data/README.md).

"""RPISeq's two classifiers in scikit-learn, set up from the paper's Methods ("Machine Learning
Algorithms"): cross-validation with per-row predictions, and train-and-predict.

RPISeq-SVM. The paper: SMO in Weka 3.7, "the normalized polykernel function of order 2 with
epsilon = 1.0E-12", C = 1.0, tolerance T = 0.0010, and "the option to fit a logistic model to
the output of the resulting SVM classifier to obtain the posterior probability of class".
  - kernel: the polynomial kernel of degree 2 normalized to unit self-similarity,
    K(x, y) = k(x, y) / sqrt(k(x, x) k(y, y)), with k scikit-learn's polynomial_kernel
    (degree 2, its default coef0 = 0);
  - SVC with C = 1.0 and tol = 0.001;
  - the logistic model: an unregularized LogisticRegression fitted to the decision values of
    "the resulting SVM classifier" on its own training data, the literal reading of the
    sentence above. (scikit-learn's CalibratedClassifierCV instead fits it on held-out folds
    of five other SVMs; that lowers RPI2241 SVM accuracy from 86.8% to 84.8%.);
  - epsilon = 1.0E-12 is the round-off threshold of Weka's SMO solver; libsvm, which SVC runs,
    has no such setting.
  Features enter as encoded; the paper describes no further scaling.

RPISeq-RF. The paper: 20 trees, "10 features were evaluated at each node", each tree trained
on examples "randomly sampled from the given training set", and "the majority vote of all the
classifiers is returned as the RF prediction".
  - RandomForestClassifier(n_estimators=20, max_features=10, bootstrap=True, random_state=1);
  - P(interact) is the fraction of the 20 trees that vote "interact".

A pair is predicted to interact when P >= 0.5, the threshold the paper states for Tables 2
and 3 and Fig. 2C. Cross-validation is StratifiedKFold, 10 folds, shuffled with SEED; the paper
says only "standard 10-fold cross-validation".

Usage:
  python rpi_sklearn.py cv    rf|svm DATA.arff FOLDS SEED OUT_PREFIX
      writes OUT_PREFIX.predictions.csv (row,fold,actual,p_interact) and OUT_PREFIX.summary.json
  python rpi_sklearn.py train rf|svm TRAIN.arff TEST.arff OUT.csv
      writes OUT.csv (row,p_interact)
"""

import json
import sys

import numpy as np
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support, roc_auc_score
from sklearn.metrics.pairwise import polynomial_kernel
from sklearn.model_selection import StratifiedKFold
from sklearn.svm import SVC


def load(path):
    """Read an ARFF file written by encode.py: 599 numeric attributes, then class {0,1} (or ?),
    each row in sparse form, {index value,...}; absent indices are 0."""
    nattr = 0
    rows, y = [], []
    with open(path) as fh:
        for line in fh:
            if line.lower().startswith("@attribute"):
                nattr += 1
            if line.strip().lower() == "@data":
                break
        for line in fh:
            line = line.strip()
            if not line or line.startswith("%"):
                continue
            v = ["0"] * nattr
            for item in line.strip("{}").split(","):
                i, val = item.strip().split(" ", 1)
                v[int(i)] = val
            rows.append([float(x) for x in v[:-1]])
            y.append(-1 if v[-1] == "?" else int(v[-1]))
    return np.array(rows), np.array(y)


def normalized_poly2(a, b):
    """Polynomial kernel of order 2, normalized: k(x, y) / sqrt(k(x, x) k(y, y))."""
    k = polynomial_kernel(a, b, degree=2, gamma=1.0, coef0=0.0)
    ka = np.einsum("ij,ij->i", a, a) ** 2  # k(x, x) for each row, without the full matrix
    kb = np.einsum("ij,ij->i", b, b) ** 2
    return k / np.sqrt(np.outer(ka, kb))


class RpiSvm:
    def fit(self, x, y):
        self.svm = SVC(C=1.0, kernel=normalized_poly2, tol=0.001).fit(x, y)
        out = self.svm.decision_function(x).reshape(-1, 1)
        self.logistic = LogisticRegression(C=np.inf, max_iter=10000).fit(out, y)
        return self

    def p_interact(self, x):
        out = self.svm.decision_function(x).reshape(-1, 1)
        return self.logistic.predict_proba(out)[:, 1]


class RpiRf:
    def fit(self, x, y):
        self.rf = RandomForestClassifier(n_estimators=20, max_features=10, bootstrap=True,
                                         random_state=1).fit(x, y)
        return self

    def p_interact(self, x):
        # Fraction of trees voting "interact" (class 1).
        one = list(self.rf.classes_).index(1)
        votes = np.array([t.predict(x) == one for t in self.rf.estimators_])
        return votes.mean(axis=0)


def make(which):
    return {"rf": RpiRf, "svm": RpiSvm}[which]()


def cv(which, path, folds, seed, out):
    x, y = load(path)
    p = np.empty(len(y))
    fold_of = np.empty(len(y), dtype=int)
    for f, (tr, te) in enumerate(StratifiedKFold(folds, shuffle=True, random_state=seed).split(x, y)):
        p[te] = make(which).fit(x[tr], y[tr]).p_interact(x[te])
        fold_of[te] = f
    with open(out + ".predictions.csv", "w") as fh:
        fh.write("row,fold,actual,p_interact\n")
        for i in np.argsort(fold_of, kind="stable"):
            fh.write(f"{i},{fold_of[i]},{y[i]},{p[i]:.17g}\n")
    pred = (p >= 0.5).astype(int)
    tn, fp, fn, tp = (int(v) for v in confusion_matrix(y, pred, labels=[0, 1]).ravel())
    pr, rc, fm, _ = precision_recall_fscore_support(y, pred, labels=[1], zero_division=0)
    wp, wr, wf, _ = precision_recall_fscore_support(y, pred, average="weighted", zero_division=0)
    s = {"tool": f"scikit-learn {sklearn.__version__}", "n": int(len(y)),
         "tp": tp, "fn": fn, "fp": fp, "tn": tn, "accuracy": 100.0 * (tp + tn) / len(y),
         "precision": float(pr[0]), "recall": float(rc[0]), "f_measure": float(fm[0]),
         "weighted_precision": float(wp), "weighted_recall": float(wr), "weighted_f_measure": float(wf),
         "auc": float(roc_auc_score(y, p))}
    with open(out + ".summary.json", "w") as fh:
        json.dump(s, fh, indent=2)
        fh.write("\n")


def train(which, train_path, test_path, out):
    x, y = load(train_path)
    xt, _ = load(test_path)
    p = make(which).fit(x, y).p_interact(xt)
    with open(out, "w") as fh:
        fh.write("row,p_interact\n")
        for i, v in enumerate(p):
            fh.write(f"{i},{v:.17g}\n")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "cv":
        cv(a[1], a[2], int(a[3]), int(a[4]), a[5])
    elif a[0] == "train":
        train(a[1], a[2], a[3], a[4])
    else:
        raise SystemExit(f"unknown command {a[0]}")

"""RPISeq's classifiers in scikit-learn: cross-validation with per-row predictions, and
train-and-predict. Replaces the paper's Weka 3.7 with settings carried over from its Methods.

  RPISeq-RF:  RandomForestClassifier, 20 trees, 10 features per split, random_state 1.
  RPISeq-SVM: SVC on a normalized polynomial kernel of exponent 2, C = 1.0, tolerance 0.001,
              attributes scaled to [0, 1] on the training data, and a logistic model fitted to
              the SVM outputs on the training data, as Weka's SMO does with -N 0 -M -V -1.

Folds are scikit-learn's StratifiedKFold (shuffled, random_state SEED), not Weka's, so
per-fold results are not Weka's.

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
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support, roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import MinMaxScaler
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


def norm_poly(a, b):
    """Weka's NormalizedPolyKernel with exponent 2 and no lower-order terms."""
    k = (a @ b.T) ** 2
    da = np.einsum("ij,ij->i", a, a) ** 2
    db = np.einsum("ij,ij->i", b, b) ** 2
    return k / np.sqrt(np.outer(da, db))


class RpiSvm:
    def fit(self, x, y):
        self.scale = MinMaxScaler().fit(x)
        self.x = self.scale.transform(x)
        self.svm = SVC(C=1.0, kernel="precomputed", tol=0.001).fit(norm_poly(self.x, self.x), y)
        out = self.svm.decision_function(norm_poly(self.x, self.x)).reshape(-1, 1)
        self.logit = LogisticRegression(C=1e8, max_iter=10000).fit(out, y)
        return self

    def p_interact(self, x):
        out = self.svm.decision_function(norm_poly(self.scale.transform(x), self.x)).reshape(-1, 1)
        return self.logit.predict_proba(out)[:, 1]


class RpiRf:
    def fit(self, x, y):
        self.rf = RandomForestClassifier(n_estimators=20, max_features=10, random_state=1).fit(x, y)
        return self

    def p_interact(self, x):
        return self.rf.predict_proba(x)[:, 1]


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

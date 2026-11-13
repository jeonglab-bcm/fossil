"""Tables 2 and 3, Figure 2 and the DeLong tests of Yu et al. (2010), over repeated random splits.

Usage: run_models.py ANALYTIC.csv OUTDIR [--reps N] [--jobs J] [--grid FILE]

For each scheme and each split r = 0 .. N-1 (seed r):
  1. 80% of each Table 1 category to training, 20% to test.
  2. All training cases and as many randomly drawn training non-cases (the balanced sample).
  3. For each kernel, grid.py's search (5-fold CV accuracy) on the balanced sample, then the SVM
     fitted to it and scored on the test set (Table 2).
  4. For the paper's best kernel (I: RBF, II: linear), sensitivity, specificity, PPV, NPV and AUC
     on the test set, on the training set (balanced, and all of it) and by the paper's 10-fold
     cross-validation in the training set (Table 3).
  5. Survey-weighted logistic regression on the training set; its test AUC and the DeLong test
     against the SVM (Figure 2 and the text).

--grid FILE reuses the C and gamma of an earlier run (grid.csv) instead of searching: the search
is most of the run time, and CI checks the rest against the committed outputs.

The method (coding, sampling, grid search, SVM, logistic regression, DeLong) comes from the
diabclass package in PMC2850872/package.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

import diabclass as dc

BEST = {"I": "rbf", "II": "linear"}  # the paper's best kernel per scheme (Table 2)


def scheme_data(d: pd.DataFrame, scheme: str):
    col = f"scheme_{scheme}_case"
    s = d[d[col].notna()].reset_index(drop=True)
    X = dc.encode(s.to_dict("records"), scheme)
    y = np.where(s[col] == 1, 1, -1)
    return s, X, y


def ten_fold(X, y, kernel, C, gamma, seed):
    """The paper's 10-fold CV in the training set: each fold is scored by an SVM trained on all
    cases and an equal number of random non-cases from the other nine folds. Mean of the folds."""
    rng = np.random.default_rng(10_000 + seed)
    fold = rng.permutation(np.arange(len(y)) % 10)
    rows = []
    for k in range(10):
        tr, te = np.flatnonzero(fold != k), np.flatnonzero(fold == k)
        m = dc.SVMClassifier(kernel, C, gamma, seed=10_000 + 10 * seed + k).fit(X[tr], y[tr])
        rows.append(dc.classification_metrics(y[te], m.decision_function(X[te])))
    keys = ["sensitivity", "specificity", "ppv", "npv", "auc"]
    return {k: float(np.mean([r[k] for r in rows])) for k in keys}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("analytic")
    ap.add_argument("outdir")
    ap.add_argument("--reps", type=int, default=20)
    ap.add_argument("--jobs", type=int, default=-1)
    ap.add_argument("--grid", help="grid.csv of an earlier run: reuse its C and gamma")
    a = ap.parse_args()
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(a.analytic)
    given = None
    if a.grid:
        g = pd.read_csv(a.grid)
        given = {(r.scheme, int(r.rep), r.kernel): (r.C, r.gamma, r.cv_accuracy) for r in g.itertuples()}
    # Searches finished by an interrupted run are kept in grid_partial.csv and reused.
    partial = out / "grid_partial.csv"
    done = {}
    if given is None and partial.exists():
        g = pd.read_csv(partial)
        done = {(r.scheme, int(r.rep), r.kernel): (r.C, r.gamma, r.cv_accuracy) for r in g.itertuples()}

    grid_rows, auc_rows, t3_rows, mlr_rows, roc_rows, band_rows = [], [], [], [], [], []
    fgrid = np.round(np.arange(0.1, 0.95, 0.1), 1)
    for scheme in ["I", "II"]:
        s, X, y = scheme_data(d, scheme)
        for rep in range(a.reps):
            tr, te = dc.split_train_test(y, s.category, 0.2, seed=rep)
            bal = tr[dc.undersample(y[tr], seed=rep)]
            scores = {}
            for kernel in dc.KERNELS:
                if given is not None:
                    C, gamma, acc = given[(scheme, rep, kernel)]
                elif (scheme, rep, kernel) in done:
                    C, gamma, acc = done[(scheme, rep, kernel)]
                else:
                    gr = dc.grid_search(X[bal], y[bal], kernel, seed=rep, n_jobs=a.jobs)
                    C, gamma, acc = gr.C, gr.gamma, gr.cv_accuracy
                    new = not partial.exists()
                    with open(partial, "a") as f:
                        if new:
                            f.write("scheme,rep,kernel,C,gamma,cv_accuracy\n")
                        f.write(f"{scheme},{rep},{kernel},{C!r},{gamma!r},{acc!r}\n")
                m = dc.SVMClassifier(kernel, C, gamma, seed=rep).fit(X[bal], y[bal], balance=False)
                sc = m.decision_function(X[te])
                scores[kernel] = (m, sc)
                grid_rows.append({"scheme": scheme, "rep": rep, "kernel": kernel, "C": C,
                                  "gamma": gamma, "cv_accuracy": acc})
                auc_rows.append({"scheme": scheme, "rep": rep, "kernel": kernel,
                                 "test_auc": dc.auc(y[te], sc)})
                print(f"scheme {scheme} rep {rep} {kernel}: C=2^{np.log2(C):.0f} "
                      f"gamma=2^{np.log2(gamma):.0f} cv={acc:.4f} auc={auc_rows[-1]['test_auc']:.4f}",
                      flush=True)
            kernel = BEST[scheme]
            m, sc = scores[kernel]
            C, gamma = m.C, m.gamma
            sets = {
                "test": dc.classification_metrics(y[te], sc),
                "training_balanced": dc.classification_metrics(y[bal], m.decision_function(X[bal])),
                "training_all": dc.classification_metrics(y[tr], m.decision_function(X[tr])),
                "cv10": ten_fold(X[tr], y[tr], kernel, C, gamma, rep),
            }
            for name, met in sets.items():
                t3_rows.append({"scheme": scheme, "rep": rep, "kernel": kernel, "set": name,
                                **{k: met[k] for k in ["sensitivity", "specificity", "ppv", "npv", "auc"]}})
            # Survey-weighted logistic regression on the whole training set (MEC 6-year weights).
            beta = dc.weighted_logistic(X[tr], y[tr], s.weight_mec6.values[tr])
            p = dc.logistic_probability(X[te], beta)
            beta_u = dc.weighted_logistic(X[tr], y[tr])
            p_u = dc.logistic_probability(X[te], beta_u)
            dl = dc.delong_test(y[te], sc, p)
            mlr_rows.append({"scheme": scheme, "rep": rep, "svm_kernel": kernel,
                             "svm_auc": dl["auc1"], "mlr_auc": dl["auc2"], "delong_z": dl["z"],
                             "delong_p": dl["p"], "mlr_unweighted_auc": dc.auc(y[te], p_u),
                             "delong_p_unweighted": dc.delong_test(y[te], sc, p_u)["p"],
                             "n_test_cases": int((y[te] == 1).sum()),
                             "n_test_noncases": int((y[te] != 1).sum()),
                             "n_train_cases": int((y[tr] == 1).sum()),
                             "n_train_noncases": int((y[tr] != 1).sum())})
            # Sensitivity at fixed false-positive rates, for Figure 2's comparison in data units.
            for model, score in [("svm", sc), ("mlr", p)]:
                fpr, tpr = dc.roc_curve(y[te], score)
                for f in fgrid:
                    band_rows.append({"scheme": scheme, "rep": rep, "model": model, "fpr": f,
                                      "tpr": float(np.interp(f, fpr, tpr))})
            if rep == 0:
                # Negative control for Figure 2: age alone as the score.
                age = s.age.values[te]
                for model, score in [("svm", sc), ("mlr", p), ("age", age)]:
                    fpr, tpr = dc.roc_curve(y[te], score)
                    roc_rows += [{"scheme": scheme, "model": model, "fpr": f, "tpr": t}
                                 for f, t in zip(fpr, tpr)]
                # Input for the R check (survey::svyglm, pROC, e1071).
                feats = dc.SCHEME_FEATURES[scheme]
                r = pd.DataFrame(X, columns=[f"f_{f}" for f in feats])
                r.insert(0, "set", "none")
                r.loc[tr, "set"] = "train"
                r.loc[te, "set"] = "test"
                r.insert(1, "balanced", 0)
                r.loc[bal, "balanced"] = 1
                r.insert(2, "case", (y == 1).astype(int))
                for c in ["sdmvstra", "sdmvpsu", "weight_mec6"]:
                    r[c] = s[c].values
                r["svm_score"] = np.nan
                r.loc[te, "svm_score"] = sc
                r.to_csv(out / f"r_input_{scheme}.csv", index=False, float_format="%.10g")
                (out / f"r_params_{scheme}.json").write_text(json.dumps(
                    {"kernel": kernel, "C": C, "gamma": gamma, "beta": beta.tolist()}, indent=1))

    pd.DataFrame(grid_rows).to_csv(out / "grid.csv", index=False, float_format="%.10g")
    pd.DataFrame(auc_rows).to_csv(out / "table2_reps.csv", index=False, float_format="%.6f")
    pd.DataFrame(t3_rows).to_csv(out / "table3_reps.csv", index=False, float_format="%.6f")
    pd.DataFrame(mlr_rows).to_csv(out / "mlr_reps.csv", index=False, float_format="%.6f")
    pd.DataFrame(roc_rows).to_csv(out / "roc_rep0.csv", index=False, float_format="%.6f")
    pd.DataFrame(band_rows).to_csv(out / "roc_at_fpr_reps.csv", index=False, float_format="%.6f")


if __name__ == "__main__":
    main()

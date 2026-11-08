"""Summaries of the model runs next to the paper's values: tables.json.

Usage: make_tables.py RUNDIR OUT.json

RUNDIR holds table1.json, table2_reps.csv, table3_reps.csv, mlr_reps.csv and grid.csv.

For values that depend on the random split (Tables 2 and 3, the logistic AUCs, the DeLong p),
"ours" is the median over our splits and the tolerance is twice the standard deviation over
them: the range a single split, like the paper's, falls in about 95% of the time.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PAPER_T2 = {"I": {"linear": "0.8332", "poly": "0.7655", "rbf": "0.8347", "sigmoid": "0.8341"},
            "II": {"linear": "0.7318", "poly": "0.6673", "rbf": "0.7259", "sigmoid": "0.7273"}}
PAPER_T3 = {
    "I": {"test": ["0.7715", "0.7503", "0.4926", "0.9127", "0.8347"],
          "training": ["0.7938", "0.7169", "0.4550", "0.9211", "0.8383"],
          "cv10": ["0.7765", "0.7027", "0.4388", "0.9130", "0.8242"]},
    "II": {"test": ["0.7359", "0.6254", "0.5061", "0.8195", "0.7318"],
           "training": ["0.7092", "0.6590", "0.6729", "0.8087", "0.7393"],
           "cv10": ["0.7059", "0.6589", "0.5293", "0.8054", "0.7357"]},
}
METRICS = ["sensitivity", "specificity", "ppv", "npv", "auc"]
PAPER_MLR = {"I": {"auc": "0.8319", "p": "0.3672"}, "II": {"auc": "0.7335", "p": "0.6718"}}


def implied_prevalence(sens, spec, ppv, npv):
    """Prevalence implied by a row's PPV, and by its NPV (Bayes' rule solved for p)."""
    s, c, v, n = (float(x) for x in (sens, spec, ppv, npv))
    p_ppv = v * (1 - c) / (s * (1 - v) + v * (1 - c))
    p_npv = (1 - n) * c / ((1 - n) * c + n * (1 - s))
    return p_ppv, p_npv


def stat(x):
    x = np.asarray(x, dtype=float)
    return {"median": float(np.median(x)), "sd": float(np.std(x, ddof=1)) if len(x) > 1 else 0.0,
            "min": float(x.min()), "max": float(x.max()), "rep0": float(x[0]), "n": int(len(x))}


def main(rundir, out):
    r = Path(rundir)
    t1 = json.loads((r / "table1.json").read_text())
    t2 = pd.read_csv(r / "table2_reps.csv").sort_values(["scheme", "kernel", "rep"])
    t3 = pd.read_csv(r / "table3_reps.csv").sort_values(["scheme", "set", "rep"])
    mlr = pd.read_csv(r / "mlr_reps.csv").sort_values(["scheme", "rep"])
    grid = pd.read_csv(r / "grid.csv")
    res = {"table1": {"paper": t1["paper"], "ours": t1["ours"]}, "table2": {}, "table3": {},
           "mlr": {}, "grid": {}, "paper_arithmetic": {}}

    for s in ["I", "II"]:
        res["table2"][s] = {}
        meds = {}
        for k in ["linear", "poly", "rbf", "sigmoid"]:
            st = stat(t2[(t2.scheme == s) & (t2.kernel == k)].test_auc)
            st["paper"] = PAPER_T2[s][k]
            res["table2"][s][k] = st
            meds[k] = st["median"]
        res["table2"][s]["best_kernel_ours"] = max(meds, key=meds.get)
        res["table2"][s]["worst_kernel_ours"] = min(meds, key=meds.get)
        per_rep = t2[t2.scheme == s].pivot(index="rep", columns="kernel", values="test_auc")
        res["table2"][s]["reps_best_kernel_counts"] = per_rep.idxmax(axis=1).value_counts().to_dict()

        # Which training set does each published row describe? Its PPV and NPV imply a prevalence.
        n = mlr[mlr.scheme == s].iloc[0]
        prev = {"test": n.n_test_cases / (n.n_test_cases + n.n_test_noncases),
                "training_all": n.n_train_cases / (n.n_train_cases + n.n_train_noncases),
                "training_balanced": 0.5}
        res["table3"][s] = {"set_prevalence": prev, "rows": {}}
        for row, vals in PAPER_T3[s].items():
            pp, pn = implied_prevalence(*vals[:4])
            res["paper_arithmetic"][f"table3_{s}_{row}_implied_prevalence"] = {"from_ppv": pp, "from_npv": pn}
            sets = {"test": ["test"], "cv10": ["cv10"], "training": ["training_all", "training_balanced"]}[row]
            for name in sets:
                d = t3[(t3.scheme == s) & (t3.set == name)]
                res["table3"][s]["rows"][name] = {
                    m: {**stat(d[m]), "paper": vals[i] if name.startswith(row) or name == row else vals[i]}
                    for i, m in enumerate(METRICS)}
        # The training row of the paper: the set whose prevalence its PPV implies.
        pp, _ = implied_prevalence(*PAPER_T3[s]["training"][:4])
        pick = min(["training_all", "training_balanced"], key=lambda k: abs(prev[k] - pp))
        res["table3"][s]["paper_training_row_is"] = pick

        m = mlr[mlr.scheme == s]
        res["mlr"][s] = {
            "auc": {**stat(m.mlr_auc), "paper": PAPER_MLR[s]["auc"]},
            "svm_auc": stat(m.svm_auc),
            "delong_p": {**stat(m.delong_p), "paper": PAPER_MLR[s]["p"]},
            "reps_significant_0_05": int((m.delong_p < 0.05).sum()),
            "auc_unweighted": stat(m.mlr_unweighted_auc),
            "svm_minus_mlr_auc": stat(m.svm_auc - m.mlr_auc),
            "n_test_cases": int(n.n_test_cases), "n_test_noncases": int(n.n_test_noncases),
        }
        g = grid[grid.scheme == s]
        res["grid"][s] = {k: {"log2C": np.log2(g[g.kernel == k].C).round().astype(int).tolist(),
                              "log2gamma": np.log2(g[g.kernel == k].gamma).round().astype(int).tolist()}
                          for k in ["linear", "poly", "rbf", "sigmoid"]}

    # Arithmetic on the paper's own numbers.
    p = t1["paper"]
    res["paper_arithmetic"]["table1_scheme_I_cases_sum"] = p["diagnosed"] + p["undiagnosed"] == p["scheme_I_cases"]
    res["paper_arithmetic"]["table1_scheme_I_noncases_sum"] = p["prediabetes"] + p["none"] == p["scheme_I_noncases"]
    res["paper_arithmetic"]["table1_scheme_II_drop"] = {
        "cases": p["undiagnosed"] + p["prediabetes"] - p["scheme_II_cases"],
        "noncases": p["none"] - p["scheme_II_noncases"]}
    res["paper_arithmetic"]["table3_test_auc_equals_table2"] = (
        PAPER_T3["I"]["test"][4] == PAPER_T2["I"]["rbf"] and PAPER_T3["II"]["test"][4] == PAPER_T2["II"]["linear"])
    Path(out).write_text(json.dumps(res, indent=1, default=float) + "\n")


if __name__ == "__main__":
    main(*sys.argv[1:3])

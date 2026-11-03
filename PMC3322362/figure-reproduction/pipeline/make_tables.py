"""Collect the cross-validation summaries and hub predictions into tables.json.

Table 1's precision, recall and F-measure are those of the interacting class: with them the
SVM row on RPI2241 equals the paper's at its printed precision, and Weka's weighted averages
do not (recall 0.87 against the paper's 0.88).

Usage: python make_tables.py CV_DIR HUBS.tsv HUB_DIR FIG1_ROC.json FIG1_CURVES.json OUT.json
CV_DIR holds <dataset>_<rf|svm>.summary.json; HUB_DIR holds hubs_<2241|369>_<rf|svm>.csv.
"""

import csv
import glob
import json
import os
import sys

PAPER = {
    "table1": {
        "RPI2241": {"rf": [89.6, 0.89, 0.90, 0.90], "svm": [87.1, 0.87, 0.88, 0.87]},
        "RPI369": {"rf": [76.2, 0.75, 0.78, 0.77], "svm": [72.8, 0.73, 0.73, 0.73]},
    },
    "fig1_auc": {"RF RPI2241": 0.97, "SVM RPI2241": 0.92, "RF RPI369": 0.85, "SVM RPI369": 0.81},
    # Results text on Fig. 2: known partners predicted at P >= 0.5.
    "fig2_hubs": {
        "2241": {"rf": {"SEN1": "8 of 8", "U6": "7 of 8"}, "svm": {"SEN1": "8 of 8", "U6": "7 of 8"}},
        "369": {"rf": {"SEN1": "4 of 8", "U6": "6 of 8"}, "svm": {"SEN1": "6 of 8", "U6": "8 of 8"}},
    },
    # Tables 2 and 3: organism, total pairs, (RF, RF %), (SVM, SVM %).
    "table2": [["H. sapiens", 1189, 888, 74.7, 681, 57.3], ["S. cerevisiae", 254, 249, 98.0, 252, 99.2],
               ["M. musculus", 120, 98, 81.7, 85, 70.8], ["D. melanogaster", 81, 80, 98.8, 72, 88.9],
               ["E. coli", 37, 34, 91.9, 25, 67.6], ["Total", 1681, 1349, 80.2, 1115, 66.3]],
    "table3": [["H. sapiens", 1189, 808, 68.0, 988, 83.1], ["S. cerevisiae", 254, 168, 66.1, 226, 89.0],
               ["M. musculus", 120, 81, 67.5, 111, 92.5], ["D. melanogaster", 81, 38, 46.9, 53, 65.4],
               ["E. coli", 37, 20, 54.0, 24, 64.9], ["Total", 1681, 1115, 66.3, 1402, 83.4]],
    # Fig. 2C edge labels, models trained on RPI369, in no particular order (the figure does not name the RNAs).
    "fig2c_labels": {
        "rf": {"SEN1": [0.50, 0.60, 0.50, 0.40, 0.40, 0.40, 0.50, 0.35], "U6": [0.70, 0.40, 0.40, 0.60, 0.50, 0.60, 0.55, 0.55]},
        "svm": {"SEN1": [0.37, 0.89, 0.38, 0.79, 0.79, 0.74, 0.64, 0.66], "U6": [0.84, 0.62, 0.88, 0.91, 0.84, 0.76, 0.75, 0.64]},
    },
}


def row(s):
    return [round(s["accuracy"], 1), round(s["precision"], 2), round(s["recall"], 2), round(s["f_measure"], 2)]


def full(s):
    keys = ["tp", "fn", "fp", "tn", "accuracy", "precision", "recall", "f_measure",
            "weighted_precision", "weighted_recall", "weighted_f_measure", "auc"]
    return {k: s[k] for k in keys}


def main(cv_dir, hubs_tsv, hub_dir, roc_json, curves_json, out):
    S = {os.path.basename(p)[: -len(".summary.json")]: json.load(open(p))
         for p in glob.glob(os.path.join(cv_dir, "*.summary.json"))}
    t = {"paper": PAPER, "weka": S["rpi2241_rf"]["weka"], "table1": {}}
    for clf in ("rf", "svm"):
        s = S[f"rpi2241_{clf}"]
        t["table1"].setdefault("RPI2241", {})[clf] = {"ours": row(s), "full": full(s),
                                                      "matches_paper": row(s) == PAPER["table1"]["RPI2241"][clf]}
        seeds = sorted((k for k in S if k.startswith("rpi369_s") and k.endswith("_" + clf)),
                       key=lambda k: int(k.split("_")[1][1:]))
        rows = [row(S[k]) for k in seeds]
        t["table1"].setdefault("RPI369", {})[clf] = {
            "ours": row(S[f"rpi369_s1_{clf}"]),
            "full": full(S[f"rpi369_s1_{clf}"]),
            "seeds": len(rows),
            "range": [[min(r[i] for r in rows), max(r[i] for r in rows)] for i in range(4)],
            "auc_range": [round(min(S[k]["auc"] for k in seeds), 3), round(max(S[k]["auc"] for k in seeds), 3)],
            "ipminer_negatives": row(S[f"rpi369_ipminer_{clf}"]) + [round(S[f"rpi369_ipminer_{clf}"]["auc"], 3)],
        }
    t["fig1"] = {"roc": json.load(open(roc_json)), "curves": json.load(open(curves_json))}

    names = [line.split("\t") for line in open(hubs_tsv) if line.strip() and not line.startswith("#")]
    hubs = {}
    for train in ("2241", "369"):
        for clf in ("rf", "svm"):
            probs = [float(r["p_interact"]) for r in csv.DictReader(open(os.path.join(hub_dir, f"hubs_{train}_{clf}.csv")))]
            pairs = [{"pair": n[0], "protein": n[3], "rna": n[4], "p": round(p, 4)} for n, p in zip(names, probs)]
            sen1 = [p for p in pairs if p["pair"].startswith("SEN1-")]
            u6 = [p for p in pairs if p["pair"].endswith("-SNR6")]
            hubs.setdefault(train, {})[clf] = {
                "pairs": pairs,
                "SEN1": f"{sum(p['p'] >= 0.5 for p in sen1)} of {len(sen1)}",
                "U6": f"{sum(p['p'] >= 0.5 for p in u6)} of {len(u6)}",
            }
    t["fig2_hubs"] = hubs
    # The arithmetic of Tables 2 and 3: column sums and percentages at the printed precision.
    t["tables23_arithmetic"] = {}
    for name in ("table2", "table3"):
        rows, issues = PAPER[name], []
        for col, label in ((1, "total"), (2, "RF"), (4, "SVM")):
            if sum(r[col] for r in rows[:-1]) != rows[-1][col]:
                issues.append(f"{label} column does not sum to {rows[-1][col]}")
        for r in rows:
            for col in (2, 4):
                if round(100 * r[col] / r[1], 1) != r[col + 1]:
                    issues.append(f"{r[0]}: {r[col]}/{r[1]} = {100 * r[col] / r[1]:.2f}%, printed {r[col + 1]}")
        t["tables23_arithmetic"][name] = issues
    json.dump(t, open(out, "w"), indent=2)


if __name__ == "__main__":
    main(*sys.argv[1:7])

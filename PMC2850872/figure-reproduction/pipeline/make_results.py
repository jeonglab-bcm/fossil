"""Merge the pipeline's numbers with the hand-written notes into results.json (paper2repro/results/v1).

Usage: make_results.py NOTES.json RUNDIR OUT.json

RUNDIR holds tables.json, table1.json, fig2_comparison.json, r_check.json and package.json.
Every field value comes from those files; the notes give labels, sources, assumptions, causes
and the run metadata. Verdicts and the summary are added afterwards by check_results.py --write.
"""

import json
import math
import sys
from pathlib import Path

KERNEL_NAME = {"linear": "linear", "poly": "polynomial", "rbf": "RBF", "sigmoid": "sigmoid"}
METRICS = ["sensitivity", "specificity", "ppv", "npv", "auc"]
METRIC_NAME = {"sensitivity": "sensitivity", "specificity": "specificity", "ppv": "PPV", "npv": "NPV", "auc": "AUC"}


def r4(x):
    return f"{x:.4f}"


def spread_field(name, st):
    """A split-dependent value: ours is the median over splits; tolerance two SDs over them."""
    return {"name": name, "expected": st["paper"], "observed": r4(st["median"]),
            "tolerance": {"abs": round(2 * st["sd"], 4)},
            "our_range": [r4(st["min"]), r4(st["max"])], "our_sd": round(st["sd"], 4)}


def main(notes_path, rundir, out):
    notes = json.loads(Path(notes_path).read_text())
    r = Path(rundir)
    tb = json.loads((r / "tables.json").read_text())
    t1 = json.loads((r / "table1.json").read_text())
    fig = json.loads((r / "fig2_comparison.json").read_text())
    rc = json.loads((r / "r_check.json").read_text())
    pkg = json.loads((r / "package.json").read_text())
    items = []

    def add(iid, **kw):
        it = {"id": iid, **notes["items"].get(iid, {}), **kw}
        items.append(it)

    # Table 1: counts, compared exactly.
    names = {"diagnosed": "Diagnosed diabetes", "undiagnosed": "Undiagnosed diabetes",
             "prediabetes": "Pre-diabetes", "none": "No diabetes",
             "scheme_I_cases": "Scheme I cases", "scheme_I_noncases": "Scheme I non-cases",
             "scheme_II_cases": "Scheme II cases", "scheme_II_noncases": "Scheme II non-cases"}
    add("table1", method="values", values={
        "tolerance": {"printed": True},
        "fields": [{"name": v, "expected": f"{t1['paper'][k]}", "observed": f"{t1['ours'][k]}"}
                   for k, v in names.items()]})

    # Table 2: test AUC per kernel.
    add("table2", method="values", values={"fields": [
        spread_field(f"Scheme {s}, {KERNEL_NAME[k]}", tb["table2"][s][k])
        for s in ["I", "II"] for k in ["linear", "poly", "rbf", "sigmoid"]]})

    # Table 3: the paper's best kernel per scheme, test, training and 10-fold CV.
    for s in ["I", "II"]:
        t3 = tb["table3"][s]
        train_set = t3["paper_training_row_is"]
        fields = []
        for row, key in [("test", "test"), ("training", train_set), ("10-fold CV", "cv10")]:
            for m in METRICS:
                st = t3["rows"][key][m]
                fields.append(spread_field(f"{row} {METRIC_NAME[m]}", st))
        add(f"table3.scheme{s}", method="values", values={"fields": fields})

    # Figure 1: schematic.
    add("fig1", method="none")

    # Figure 2: ROC curves, pixels (SVM and logistic traces pooled per panel).
    for s, panel in [("I", "a"), ("II", "b")]:
        P = fig["panels"][s]["models"]
        pub = sum(P[m]["published_px"] for m in P)
        pn = sum(P[m]["published_near_ours"] * P[m]["published_px"] for m in P) / pub
        on = min(P[m]["ours_near_published"] for m in P)
        ctrls = []
        for i, c in enumerate(P["svm"]["controls"]):
            c2 = P["mlr"]["controls"][i]
            ctrls.append({"name": c["name"], "kind": c["kind"], "score": round(min(c["score"], c2["score"]), 4)})
        add(f"fig2.{panel}", method="pixels", pixels={
            "tolerance_px": fig["tolerance_px"], "dpi": None,
            "published_near_ours": round(pn, 4), "ours_near_published": round(on, 4),
            "threshold": notes["fig2_threshold"], "controls": ctrls,
            "per_trace": {m: {k: P[m][k] for k in ["published_near_ours", "ours_near_published"]} for m in P}},
            outputs=["figure-reproduction/output/fig2_ours.png", "figure-reproduction/output/fig2_overlay.png"])

    # Figure 2 in data units: the published sensitivity at fixed false-positive rates, read off the
    # figure, against the median and spread of ours over the splits.
    import pandas as pd
    band = pd.read_csv(r / "roc_at_fpr_reps.csv")
    for s, panel in [("I", "a"), ("II", "b")]:
        fields = []
        for m, mname in [("svm", "SVM"), ("mlr", "logistic regression")]:
            pub = fig["panels"][s]["models"][m]["published_tpr_at_fpr"]
            for f, v in pub.items():
                if v is None:
                    continue
                x = band[(band.scheme == s) & (band.model == m) & (band.fpr.round(1) == float(f))].tpr
                st = {"paper": f"{min(v, 1.0):.3f}", "median": float(x.median()), "sd": float(x.std(ddof=1)),
                      "min": float(x.min()), "max": float(x.max())}
                fields.append(spread_field(f"{mname}, sensitivity at 1 - specificity {f}", st))
        add(f"fig2.{panel}.values", method="values", values={"fields": fields})

    # Claims in the text.
    mlr = tb["mlr"]
    add("text.mlr_auc", method="values", values={"fields": [
        spread_field(f"Scheme {s}, logistic regression AUC", mlr[s]["auc"]) for s in ["I", "II"]]})
    fields = []
    for s in ["I", "II"]:
        fields.append(spread_field(f"Scheme {s}, DeLong P", mlr[s]["delong_p"]))
        fields.append({"name": f"Scheme {s}, SVM and logistic AUCs differ at P < 0.05",
                       "expected": "no", "observed": "yes" if mlr[s]["delong_p"]["median"] < 0.05 else "no",
                       "our_splits_significant": f"{mlr[s]['reps_significant_0_05']} of {mlr[s]['delong_p']['n']}"})
    add("text.delong", method="values", values={"fields": fields})
    add("text.best_kernel", method="values", values={"fields": [
        {"name": "Scheme I, best kernel by test AUC", "expected": "RBF",
         "observed": KERNEL_NAME[tb["table2"]["I"]["best_kernel_ours"]]},
        {"name": "Scheme II, best kernel by test AUC", "expected": "linear",
         "observed": KERNEL_NAME[tb["table2"]["II"]["best_kernel_ours"]]},
        {"name": "Scheme I, worst kernel (polynomial)", "expected": "polynomial",
         "observed": KERNEL_NAME[tb["table2"]["I"]["worst_kernel_ours"]]},
        {"name": "Scheme II, worst kernel (polynomial)", "expected": "polynomial",
         "observed": KERNEL_NAME[tb["table2"]["II"]["worst_kernel_ours"]]}]})

    # Arithmetic on the paper's own numbers (no run of ours involved).
    ar = tb["paper_arithmetic"]
    p1 = t1["paper"]
    fields = [
        {"name": "Table 1, scheme I cases = diagnosed + undiagnosed", "expected": f"{p1['scheme_I_cases']}",
         "observed": f"{p1['diagnosed'] + p1['undiagnosed']}"},
        {"name": "Table 1, scheme I non-cases = pre-diabetes + no diabetes", "expected": f"{p1['scheme_I_noncases']}",
         "observed": f"{p1['prediabetes'] + p1['none']}"},
        {"name": "Table 3 test AUC = Table 2 best kernel (both schemes)", "expected": "yes",
         "observed": "yes" if ar["table3_test_auc_equals_table2"] else "no"},
    ]
    # Prevalence each Table 3 row implies (Bayes' rule on its sensitivity, specificity, PPV and NPV)
    # against the prevalence of the set it describes, from Table 1 (80/20 split within each group).
    prev = {"I": p1["scheme_I_cases"] / (p1["scheme_I_cases"] + p1["scheme_I_noncases"]),
            "II": p1["scheme_II_cases"] / (p1["scheme_II_cases"] + p1["scheme_II_noncases"])}
    exceptions = []
    for s in ["I", "II"]:
        bal = tb["table3"][s]["paper_training_row_is"] == "training_balanced"
        for row, target, what in [("test", prev[s], "test set"),
                                  ("training", 0.5 if bal else prev[s], "balanced sample" if bal else "training set"),
                                  ("cv10", prev[s], "training folds")]:
            ip = ar[f"table3_{s}_{row}_implied_prevalence"]
            for k, lab in [("from_ppv", "PPV"), ("from_npv", "NPV")]:
                name = f"Table 3 scheme {s} {row}: prevalence implied by {lab} ({what})"
                fields.append({"name": name, "expected": f"{target:.4f}", "observed": f"{ip[k]:.4f}",
                               "tolerance": {"abs": 0.01}})
                if abs(ip[k] - target) > 0.01:
                    exceptions.append({"field": name, "category": "paper_error", "evidence": [
                        "figure-reproduction/output/tables.json (paper_arithmetic)",
                        f"PPV implies {ip['from_ppv']:.4f} and NPV implies {ip['from_npv']:.4f}: no one set gives both"]})
    add("text.arithmetic", method="values", values={"fields": fields, "exceptions": exceptions})
    t3ex = [e for e in exceptions if "scheme II training" in e["field"]]
    for it in items:
        if it["id"] == "table3.schemeII" and t3ex:
            f = next(x for x in it["values"]["fields"] if x["name"] == "training NPV")
            if abs(float(f["observed"]) - float(f["expected"])) > f["tolerance"]["abs"] + 1e-12:
                it["values"]["exceptions"] = [{"field": "training NPV", "category": "paper_error",
                                               "evidence": t3ex[0]["evidence"]}]

    # Python against R.
    ok = all(rc[s]["beta_max_abs_diff"] < 1e-6 and abs(rc[s]["delong_p_r"] - mlr_rep0(tb, s, "delong_p")) < 1e-6
             and abs(rc[s]["e1071_auc"] - rc[s]["auc_svm_r"]) < 0.002 for s in ["I", "II"])
    # The gaps are rounding noise that moves between machines (R's own numbers vary too), and
    # results.json must come out identical on every run: print a bound, the smallest power of ten at
    # least three times the gap, not the gap. r_check.json keeps the exact values.
    def bound(x):
        return f"{10.0 ** math.ceil(math.log10(max(3 * x, 1e-300))):.0e}"

    add("r_check", method="check", check={"passed": ok, "detail": (
        "On split 0: logistic coefficients equal to survey::svyglm within "
        f"{bound(max(rc[s]['beta_max_abs_diff'] for s in ['I', 'II']))}; DeLong P equal to pROC::roc.test within "
        f"{bound(max(abs(rc[s]['delong_p_r'] - mlr_rep0(tb, s, 'delong_p')) for s in ['I', 'II']))}; "
        "SVM test AUC from e1071 (LIBSVM in R) with the same C and gamma "
        + ", ".join(f"{rc[s]['e1071_auc']:.4f} against {rc[s]['auc_svm_r']:.4f}" for s in ["I", "II"]))})

    add("package", method="check", check={"passed": bool(pkg.get("passed")), "detail": pkg.get("detail", "")},
        outputs=["package/tutorial/TUTORIAL.md"])

    run = dict(notes["run"])
    base = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public"
    tsv = Path(__file__).resolve().parent / "inputs" / "nhanes_files.tsv"
    run["inputs"] = [{"name": f, "url": f"{base}/{y}/DataFiles/{f}", "sha256": h}
                     for y, f, h in (l.split() for l in tsv.read_text().splitlines() if l and not l.startswith("#"))]
    run.pop("inputs_list", None)
    res = {"schema": "paper2repro/results/v1", "paper": notes["paper"], "run": run,
           "session": notes["session"],
           **({"skill": notes["skill"]} if "skill" in notes else {}), "items": items}
    res["run"]["environment"] = {**res["run"].get("environment", {}), **{f"R {k}": v for k, v in rc["versions"].items()}}
    Path(out).write_text(json.dumps(res, indent=1) + "\n")


def mlr_rep0(tb, s, key):
    return tb["mlr"][s][key]["rep0"]


if __name__ == "__main__":
    main(*sys.argv[1:4])

"""Compare our run with the paper: the fields of every item in results.json, and the tables.

  compare.py RUN_DIR OUT_DIR

Reads accuracy.json and datasets.json (experiments.py) and figures.json (figures.py) from RUN_DIR.
Writes OUT_DIR/comparison.json ({"items": {id: {"method", "values" | "check", "outputs"}}}) and
OUT_DIR/tables.json (Tables 1 to 3, published next to ours, with the spread over seeds and folds).
Printed values are strings, so check_results.py compares them at printed precision.

Three kinds of number are kept apart (text-claims.md): "arithmetic" recomputes the paper's claims
from its own tables; "ours" is our run and the only kind that sets a verdict; hypothesis-test
variants (hyp.* experiments) appear only in the causes, never as agreement.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import cfsenn

RUN, OUT = Path(sys.argv[1]), Path(sys.argv[2])
acc = json.loads((RUN / "accuracy.json").read_text())
ds = json.loads((RUN / "datasets.json").read_text())
figs = json.loads((RUN / "figures.json").read_text())

NAMES = {"allaml": "ALL-AML", "lung": "Lung", "prostate": "Prostate", "dlbcl": "DLBCL", "ovarian": "Ovarian",
         "colon": "Colon", "mll": "MLL"}

# Table 1 as printed: genes, training (classes), test (classes); class order as printed.
TABLE1 = {
    "allaml": ("7129", "38", "27:11", "34", "20:14", ("AMLALL_Train", "AMLALL_Test"), ["ALL", "AML"]),
    "lung": ("12533", "32", "16:16", "149", "15:134", ("lungCancer_Train", "lungCancer_Test"), ["Mesothelioma", "ADCA"]),
    "prostate": ("12600", "102", "52:50", "34", "25:9", ("prostate_TumorVSNormal_Train", "prostate_TumorVSNormal_Test"), ["Tumor", "Normal"]),
    "dlbcl": ("4026", "47", "24:23", "0", None, ("DLBCL-Stanford", None), ["germinal", "activated"]),
    "ovarian": ("15154", "253", "91:162", "0", None, ("ovarian_61902", None), ["Normal", "Cancer"]),
    "colon": ("2000", "62", "40:22", "0", None, ("colonTumor", None), ["negative", "positive"]),
    "mll": ("12582", "57", "20:17:20", "15", "4:3:8", ("MLL_Train", "MLL_Test"), ["ALL", "MLL", "AML"]),
}
TABLE2 = {"test": {"allaml": "100", "lung": "100", "prostate": "97.06"},
          "loocv": {"allaml": "100", "lung": "100", "prostate": "96.08"}}
TABLE2_CITED = {"bagged": {"allaml": "91.18", "lung": "93.29", "prostate": "73.53"},
                "best": {"allaml": "97.06", "lung": "97.99", "prostate": "73.53"}}
TABLE3 = {"loocv": {"dlbcl": "97.87", "ovarian": "99.21", "colon": "91.94"},
          "cv10": {"dlbcl": "95.74", "ovarian": "98.82", "colon": "90.32"}}
TABLE3_CITED = {"colon_loocv_dettling": "85.48", "ovarian_cv10_liu": "100", "dlbcl_cho": "96"}
FIG4 = {"dlbcl": "98", "ovarian": "98.82", "colon": "91.94"}


def pct(c, t):
    return 100.0 * c / t


def p2(v):
    """As the paper prints: whole 100, otherwise two decimals."""
    return "100" if abs(v - 100) < 1e-9 else f"{v:.2f}"


def cho():
    runs = [v for k, v in acc.items() if k.startswith("cho.dlbcl.r")]
    c, t = sum(r["correct"] for r in runs), sum(r["total"] for r in runs)
    per = sorted(r["correct"] for r in runs)
    return pct(c, t), per, len(runs)


items = {}

# Table 1 ---------------------------------------------------------------------------------------
fields = []
for d, (genes, ntr, ctr, nte, cte, (ftr, fte), order) in TABLE1.items():
    tr = ds[ftr]
    fields += [
        {"name": f"{NAMES[d]}: genes", "expected": genes, "observed": str(tr["genes"])},
        {"name": f"{NAMES[d]}: training samples", "expected": ntr, "observed": str(tr["samples"])},
        {"name": f"{NAMES[d]}: training classes ({':'.join(order)})", "expected": ctr,
         "observed": ":".join(str(tr["per_class"][c]) for c in order)},
        {"name": f"{NAMES[d]}: test samples", "expected": nte, "observed": str(ds[fte]["samples"]) if fte else "0"},
    ]
    if cte:
        fields.append({"name": f"{NAMES[d]}: test classes ({':'.join(order)})", "expected": cte,
                       "observed": ":".join(str(ds[fte]["per_class"][c]) for c in order)})
items["table1"] = {"method": "values", "values": {"fields": fields, "tolerance": {"printed": True}}}


def acc_field(name, expected, key):
    a = acc[key]
    return {"name": f"{name} ({a['correct']} of {a['total']} correct)", "expected": expected,
            "observed": p2(pct(a["correct"], a["total"]))}


# Table 2 and Fig. 3 ----------------------------------------------------------------------------
items["table2.test"] = {"method": "values", "values": {"tolerance": {"printed": True}, "fields": [
    acc_field(f"{NAMES[d]} test accuracy, %", v, f"test.{d}.s0") for d, v in TABLE2["test"].items()]}}
items["table2.loocv"] = {"method": "values", "values": {"tolerance": {"printed": True}, "fields": [
    acc_field(f"{NAMES[d]} LOOCV on the training samples, %", v, f"loocv.{d}") for d, v in TABLE2["loocv"].items()]}}
f3 = {o["group"]: o for o in figs["fig3"]["ours"]}
items["fig3"] = {"method": "values", "outputs": figs["fig3"]["outputs"], "values": {"tolerance": {"printed": True}, "fields": [
    {"name": f"{g} 'Our method' bar, %", "expected": lab, "observed": f3[g]["printed"]}
    for g, lab in (("ALL-AML", "100"), ("Lung", "100"), ("Prostate", "97.06"))]}}

# Table 3 and Fig. 4 ----------------------------------------------------------------------------
items["table3.loocv"] = {"method": "values", "values": {"tolerance": {"printed": True}, "fields": [
    acc_field(f"{NAMES[d]} LOOCV, %", v, f"loocv.{d}") for d, v in TABLE3["loocv"].items()]}}
items["table3.cv10"] = {"method": "values", "values": {"tolerance": {"printed": True}, "fields": [
    acc_field(f"{NAMES[d]} 10-fold CV, %", v, f"cv10.{d}.f0") for d, v in TABLE3["cv10"].items()]}}
cho_mean, cho_per, cho_n = cho()
f4 = {o["group"]: o for o in figs["fig4"]["ours"]}
items["fig4"] = {"method": "values", "outputs": figs["fig4"]["outputs"], "values": {"tolerance": {"printed": True}, "fields": [
    {"name": f"DLBCL 'OurMethod' bar, Cho and Won's 22/25 split, % (mean of {cho_n} random splits)",
     "expected": "98", "observed": f"{cho_mean:.0f}"},
    {"name": "Ovarian 'OurMethod' bar (10-fold CV), %", "expected": "98.82", "observed": f4["Ovarian"]["printed"]},
    {"name": "Colon 'OurMethod' bar (LOOCV), %", "expected": "91.94", "observed": f4["Colon"]["printed"]},
]}}

# MLL -------------------------------------------------------------------------------------------
m = acc["test.mll.s0"]
items["text.mll"] = {"method": "values", "values": {"tolerance": {"printed": True}, "fields": [
    {"name": "MLL test samples classified correctly (of 15)", "expected": "15", "observed": str(m["correct"])}]}}

# Claims in the text: our run -------------------------------------------------------------------
CONTROL_RUNS = ["test.allaml", "test.lung", "test.prostate", "loocv.dlbcl", "loocv.colon"]


def main_key(r):
    return f"{r}.s0" if r.startswith("test.") else r


def total(keys):
    return sum(acc[k]["correct"] for k in keys)


ours_total = total([main_key(r) for r in CONTROL_RUNS])
n_total = sum(acc[main_key(r)]["total"] for r in CONTROL_RUNS)
controls = {}
for name, label in (("random", "random genes in place of the selected features"),
                    ("single", "one network on all 75 features, no ensemble"),
                    ("adaboost", "AdaBoost in place of bagging")):
    keys = [f"ctl.{name}.{r}" for r in CONTROL_RUNS]
    c = total(keys)
    per = {r: (acc[f"ctl.{name}.{r}"]["correct"], acc[main_key(r)]["correct"], acc[main_key(r)]["total"]) for r in CONTROL_RUNS}
    controls[name] = {"correct": c, "ours": ours_total, "total": n_total, "per_run": per}
    worse_runs = sum(1 for a, b, _ in per.values() if a < b)
    items[f"text.control_{name}"] = {"method": "values", "values": {"tolerance": {"printed": True}, "fields": [
        {"name": f"{label}: fewer correct than ours over the five runs ({c} against {ours_total} of {n_total})",
         "expected": "yes", "observed": "yes" if c < ours_total else "no"},
    ]}, "detail": {"worse_in_runs": worse_runs, "per_run": per}}

bag = TABLE2_CITED["bagged"]
items["text.vs_bagging"] = {"method": "values", "values": {"tolerance": {"printed": True}, "fields": [
    {"name": f"{NAMES[d]}: our test accuracy above Tan and Gilbert's bagged trees ({bag[d]}%)", "expected": "yes",
     "observed": "yes" if pct(acc[f'test.{d}.s0']['correct'], acc[f'test.{d}.s0']['total']) > float(bag[d]) else "no"}
    for d in ("allaml", "lung", "prostate")]}}
best = TABLE2_CITED["best"]
items["text.vs_best"] = {"method": "values", "values": {"tolerance": {"printed": True}, "fields": [
    {"name": f"{NAMES[d]}: our test accuracy above the best cited method ({best[d]}%)", "expected": "yes",
     "observed": "yes" if pct(acc[f'test.{d}.s0']['correct'], acc[f'test.{d}.s0']['total']) > float(best[d]) else "no"}
    for d in ("allaml", "lung", "prostate")]}}
p_loo = pct(acc["loocv.prostate"]["correct"], acc["loocv.prostate"]["total"])
p_test = pct(acc["test.prostate.s0"]["correct"], acc["test.prostate.s0"]["total"])
items["text.prostate_loocv_lower"] = {"method": "values", "values": {"tolerance": {"printed": True}, "fields": [
    {"name": "Prostate: LOOCV on the training samples a little lower than the test accuracy", "expected": "yes",
     "observed": "yes" if p_loo < p_test else "no"}]}}
colon = pct(acc["loocv.colon"]["correct"], acc["loocv.colon"]["total"])
items["text.colon_vs_dettling"] = {"method": "values", "values": {"tolerance": {"printed": True}, "fields": [
    {"name": "Colon: our LOOCV above Dettling and Buhlmann's 85.48%", "expected": "yes",
     "observed": "yes" if colon > 85.48 else "no"}]}}
items["text.dlbcl_vs_cho"] = {"method": "values", "values": {"tolerance": {"printed": True}, "fields": [
    {"name": "DLBCL: our accuracy on 22/25 splits above Cho and Won's 96%", "expected": "yes",
     "observed": "yes" if cho_mean > 96 else "no"}]}}

# Claims recomputed from the paper's own tables (arithmetic, not our run) -----------------------
N = {("test", "allaml"): 34, ("test", "lung"): 149, ("test", "prostate"): 34, ("loocv", "allaml"): 38,
     ("loocv", "lung"): 32, ("loocv", "prostate"): 102, ("loocv3", "dlbcl"): 47, ("loocv3", "ovarian"): 253,
     ("loocv3", "colon"): 62, ("cv10", "dlbcl"): 47, ("cv10", "ovarian"): 253, ("cv10", "colon"): 62}
printed = {("test", d): v for d, v in TABLE2["test"].items()}
printed.update({("loocv", d): v for d, v in TABLE2["loocv"].items()})
printed.update({("loocv3", d): v for d, v in TABLE3["loocv"].items()})
printed.update({("cv10", d): v for d, v in TABLE3["cv10"].items()})
whole, not_whole = [], []
for k, v in printed.items():
    n = N[k]
    ok = [c for c in range(n + 1) if abs(100.0 * c / n - float(v)) <= (0.5 if "." not in v else 0.005) + 1e-9]
    (whole if ok else not_whole).append(f"{NAMES[k[1]]} {v}% of {n}" + (f" = {ok[0]}/{n}" if ok else ""))
claims = {
    "Prostate LOOCV 96.08 below its test accuracy 97.06": 96.08 < 97.06,
    "ours above the bagged trees on all three test sets": all(float(TABLE2["test"][d]) > float(bag[d]) for d in bag),
    "ours above the best cited method on all three test sets": all(float(TABLE2["test"][d]) > float(best[d]) for d in best),
    "Colon LOOCV 91.94 above Dettling's 85.48": 91.94 > 85.48,
    "DLBCL 98 above Cho's 96": 98 > 96,
    "75 features: 30 + 15 + 30": 30 + 15 + 30 == 75,
    "ALL-AML and lung LOOCV equal their test accuracy": TABLE2["loocv"]["allaml"] == TABLE2["test"]["allaml"]
    and TABLE2["loocv"]["lung"] == TABLE2["test"]["lung"],
}
held = sum(claims.values())
items["text.arithmetic"] = {"method": "check", "check": {
    "passed": held == len(claims),
    "detail": f"{held} of {len(claims)} claims come back from the paper's own tables. "
              f"{len(whole)} of {len(printed)} printed accuracies are whole counts of samples; "
              f"not a whole count: {'; '.join(not_whole) or 'none'}. Fig. 4's 98% on 25 test samples is not a whole count either (24/25 = 96, 25/25 = 100).",
}, "detail": {"claims": claims, "whole_counts": whole, "not_whole": not_whole}}

items["text.features75"] = {"method": "values", "values": {"tolerance": {"printed": True}, "fields": [
    {"name": "features per ensemble member (30 rank-sum genes + 15 PCs + 30 clustered genes)", "expected": "75",
     "observed": str(cfsenn.DEFAULTS["n_rank"] + cfsenn.DEFAULTS["n_pc"] + cfsenn.DEFAULTS["n_cluster_genes"])}]}}

# Tables for the page ---------------------------------------------------------------------------
def spread(prefix):
    ks = sorted(k for k in acc if k.startswith(prefix))
    return [{"run": k, "correct": acc[k]["correct"], "total": acc[k]["total"], "percent": acc[k]["percent"]} for k in ks]


tables = {
    "table1": [{"dataset": NAMES[d], "published": {"genes": t[0], "train": f"{t[1]} ({t[2]})", "test": t[3] + (f" ({t[4]})" if t[4] else "")},
                "ours": {"genes": next(f["observed"] for f in items["table1"]["values"]["fields"] if f["name"] == f"{NAMES[d]}: genes")}}
               for d, t in TABLE1.items()],
    "table2": {r: {d: {"published": v, "ours": acc[(f"test.{d}.s0" if r == "test" else f"loocv.{d}")]} for d, v in row.items()}
               for r, row in TABLE2.items()},
    "table2_cited": TABLE2_CITED,
    "table3": {r: {d: {"published": v, "ours": acc[(f"loocv.{d}" if r == "loocv" else f"cv10.{d}.f0")]} for d, v in row.items()}
               for r, row in TABLE3.items()},
    "table3_cited": TABLE3_CITED,
    "seeds": {d: spread(f"test.{d}.s") for d in ("allaml", "lung", "prostate", "mll")},
    "folds": {d: spread(f"cv10.{d}.f") for d in ("dlbcl", "ovarian", "colon")},
    "cho": {"mean_percent": round(cho_mean, 2), "correct_per_split": cho_per, "splits": cho_n},
    "controls": controls,
    "hypotheses": {k: {"correct": v["correct"], "total": v["total"], "percent": v["percent"]}
                   for k, v in acc.items() if k.startswith("hyp.")},
    "figures": {k: {"published_bars": v["published_bars"], "calibration": v["calibration"]} for k, v in figs.items()},
}

OUT.mkdir(parents=True, exist_ok=True)
# item_list: the same items as a list keyed without dots, for tools/check_results.py paths
item_list = [{"key": k.replace(".", "_"), **v} for k, v in items.items()]
(OUT / "comparison.json").write_text(json.dumps({"items": items, "item_list": item_list}, indent=1) + "\n")
(OUT / "tables.json").write_text(json.dumps(tables, indent=1) + "\n")
print(f"{len(items)} items compared")

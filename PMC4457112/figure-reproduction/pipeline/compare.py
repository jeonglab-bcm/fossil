#!/usr/bin/env python3
"""Compare our run with Tables 1-3 and the claims of the text; write comparison.json.

Every table field is the paper's printed string against our number, compared at printed precision.
Every claim is written as fields before our number is filled in; "arithmetic" holds the claim
recomputed from the paper's own tables and numbers (text.arithmetic).

Usage: compare.py OUTPUT_DIR   (reads published_values.json, models.json, selection.json,
       dataset.json, disagreements.json, topic.json, single_feature.json and fraction.json there)
"""
import json
import math
import os
import sys

out_dir = sys.argv[1]


def load(name, default=None):
    p = os.path.join(out_dir, name)
    if not os.path.exists(p):
        if default is not None:
            return default
        raise SystemExit(f"missing {p}")
    return json.load(open(p))


pub = load("published_values.json")
models = load("models.json")["models"]
sel = load("selection.json")
ds = load("dataset.json")
dis = load("disagreements.json")
topic = load("topic.json")
single = load("single_feature.json")
frac = load("fraction.json", {})


def yn(b):
    return "yes" if b else "no"


def printed_ok(expected, observed):
    dec = len(expected.split(".")[1]) if "." in expected else 0
    return abs(float(expected) - observed) <= 0.5 * 10 ** -dec + 1e-12


def table_fields(key, kind):
    m = models[kind]["forward_selection"]
    fields = []
    for name, exp in pub[key].items():
        col, meas = name.split(".", 1)
        obs = m["cv" if col == "cv" else col].get(meas)
        label = {"cv": "1987-2010 cross-validation"}.get(col, col) + ", " + meas.replace("_", " ")
        fields.append({"name": label, "expected": exp, "observed": obs, "within_0.01": abs(float(exp) - obs) <= 0.01})
    return fields


tables = {"table1": {"fields": table_fields("table1", "citation_plus_mesh")},
          "table2": {"fields": table_fields("table2", "citation_only")}}
t3 = []
for name, exp in pub["table3"].items():
    kind, col, meas = name.split(".")
    m = models[kind][col]
    obs = m["n_features"] if meas == "n_features" else m["2011"][meas]
    t3.append({"name": f"{kind.replace('_', ' ')}, {col.replace('_', ' ')}, {meas.replace('_', ' ')}",
               "expected": exp, "observed": obs,
               "within_0.01": (abs(float(exp) - obs) <= 0.01) if meas != "n_features" else None})
tables["table3"] = {"fields": t3}
for t in tables.values():
    t["summary"] = {"fields": len(t["fields"]),
                    "printed": sum(printed_ok(f["expected"], f["observed"]) for f in t["fields"]),
                    "within_0.01": sum(bool(f.get("within_0.01")) for f in t["fields"])}

# ---- claims -------------------------------------------------------------------------------------
P = pub
M, C = models["citation_plus_mesh"]["forward_selection"], models["citation_only"]["forward_selection"]
claims = {}


def claim(cid, fields):
    # keyed text_<name>: the repository's results check reads JSON paths split on dots
    claims[cid.replace(".", "_", 1)] = {"fields": fields}


def f(name, expected, observed, arithmetic=None):
    d = {"name": name, "expected": expected, "observed": observed}
    if arithmetic is not None:
        d["arithmetic"] = arithmetic
    return d


# Results: "for both years, the AUC (>=0.965) is extremely high, as is accuracy (>=0.984) and F-score (>=0.807)"
def floor(measure, models_, published):
    ours = min(m[y][measure] for m in models_ for y in ("2011", "2012"))
    paper = min(float(P[t][f"{y}.{measure}"]) for t in ("table1", "table2") for y in ("2011", "2012"))
    return ours, paper


claim("text.test_floor", [
    f(f"every test {label} at least {bound} (at the printed 3 decimals)", "yes",
      yn(round(floor(meas, (M, C), True)[0], 3) >= float(bound)),
      yn(round(floor(meas, (M, C), True)[1], 3) >= float(bound)))
    for label, meas, bound in (("AUC", "auc", "0.965"), ("accuracy", "accuracy", "0.984"), ("F1", "f1", "0.807"))])

# "Overall performance is very nearly the same as cross-validation across all measures": within 0.02.
# (0.01 fails on the paper's own Table 2, CV F1 0.800 against 0.811 in 2012, so it is not the paper's sense.)
def near_cv(src_cv, src_test):
    return all(abs(src_cv(k) - src_test(y, k)) <= 0.02 for y in ("2011", "2012")
               for k in ("auc", "average_precision", "f1", "accuracy"))


claim("text.cv_predicts_test", [
    f("test within 0.02 of cross-validation, CITATION_PLUS_MESH", "yes",
      yn(near_cv(lambda k: M["cv"][k], lambda y, k: M[y][k])),
      yn(near_cv(lambda k: float(P["table1"][f"cv.{k}"]), lambda y, k: float(P["table1"][f"{y}.{k}"])))),
    f("test within 0.02 of cross-validation, CITATION_ONLY", "yes",
      yn(near_cv(lambda k: C["cv"][k], lambda y, k: C[y][k])),
      yn(near_cv(lambda k: float(P["table2"][f"cv.{k}"]), lambda y, k: float(P["table2"][f"{y}.{k}"])))),
])

# "the CITATION_PLUS_MESH model being slightly better across all measures"
def better_all(a, b):
    ok = all(a[y][k] > b[y][k] for y in ("2011", "2012") for k in ("auc", "average_precision", "f1"))
    ok &= all(a[y]["accuracy"] >= b[y]["accuracy"] and a[y]["mse"] <= b[y]["mse"] for y in ("2011", "2012"))
    return ok


def pub_model(t):
    return {y: {k: float(P[t][f"{y}.{k}"]) for k in ("auc", "average_precision", "f1", "accuracy", "mse")}
            for y in ("2011", "2012")}


claim("text.mesh_better", [
    f("CITATION_PLUS_MESH better on every measure, 2011 and 2012", "yes", yn(better_all(M, C)),
      yn(better_all(pub_model("table1"), pub_model("table2")))),
])

# "The AUC 95% confidence intervals computed using the conservative Hanley/McNeil method do not overlap."
def no_overlap(a, b, y):
    return a[y]["auc_ci_low"] > b[y]["auc_ci_high"] or b[y]["auc_ci_low"] > a[y]["auc_ci_high"]


pci = {t: {y: {"auc_ci_low": float(P[t][f"{y}.auc_ci_low"]), "auc_ci_high": float(P[t][f"{y}.auc_ci_high"])}
           for y in ("2011", "2012")} for t in ("table1", "table2")}
claim("text.ci_no_overlap", [
    f(f"AUC intervals of the two models do not overlap, {y}", "yes", yn(no_overlap(M, C, y)),
      yn(no_overlap(pci["table1"], pci["table2"], y))) for y in ("2011", "2012")])

# "On average, the squared error of the confidence predictions of both models is less than 0.015."
claim("text.mse_below", [
    f("largest test MSE of the confidence, both models", "yes",
      yn(max(m[y]["mse"] for m in (M, C) for y in ("2011", "2012")) < 0.015),
      yn(max(float(P[t][f"{y}.mse"]) for t in ("table1", "table2") for y in ("2011", "2012")) < 0.015))])

# "The enhanced Ruping method is > 3x as accurate than the simple sigmoid method."
ratios = [m[y]["mse_sigmoid"] / m[y]["mse"] for m in (M, C) for y in ("2011", "2012")]
pratios = [float(P[t][f"{y}.mse_sigmoid"]) / float(P[t][f"{y}.mse"]) for t in ("table1", "table2") for y in ("2011", "2012")]
claim("text.calibration_3x", [
    f("sigmoid MSE more than 3 times the calibrated MSE, every model and year", "yes", yn(min(ratios) > 3),
      yn(min(pratios) > 3))])

# Table 3 text: forward selection beats CHISQ on every metric; POSTHOC almost identical with 300-400x
# fewer features; adding publication types raises AUC a little, lowers AP more, worsens F1 and MSE.
def t3v(kind, col, meas, published):
    if published:
        return float(P["table3"][f"{kind}.{col}.{meas}"])
    m = models[kind][col]
    return m["n_features"] if meas == "n_features" else m["2011"][meas]


def fs_beats_chisq(pub_):
    return all(t3v(k, "forward_selection", m, pub_) > t3v(k, "chisq", m, pub_)
               for k in ("citation_only", "citation_plus_mesh") for m in ("auc", "average_precision", "f1")) and \
        all(t3v(k, "forward_selection", "mse", pub_) < t3v(k, "chisq", "mse", pub_) for k in ("citation_only", "citation_plus_mesh"))


def posthoc_same(pub_):
    return all(abs(t3v(k, "forward_selection", m, pub_) - t3v(k, "posthoc", m, pub_)) <= 0.002
               for k in ("citation_only", "citation_plus_mesh") for m in ("auc", "average_precision", "f1", "mse"))


def ratio(k, pub_):
    return t3v(k, "forward_selection", "n_features", pub_) / t3v(k, "posthoc", "n_features", pub_)


def pubtypes_pattern(pub_):
    out = {}
    for k in ("citation_only", "citation_plus_mesh"):
        d = {m: t3v(k, "plus_pubtypes", m, pub_) - t3v(k, "forward_selection", m, pub_)
             for m in ("auc", "average_precision", "f1", "mse")}
        out[k] = d
    return out


claim("text.forward_beats_chisq", [f("forward selection better than CHISQ on AUC, AP, F1 and MSE, both models", "yes",
                                     yn(fs_beats_chisq(False)), yn(fs_beats_chisq(True)))])
claim("text.posthoc", [
    f("POSTHOC within 0.002 of forward selection on AUC, AP, F1 and MSE, both models", "yes",
      yn(posthoc_same(False)), yn(posthoc_same(True))),
    f("forward selection features over POSTHOC features, CITATION_ONLY, between 300 and 400", "yes",
      yn(300 <= ratio("citation_only", False) <= 400), yn(300 <= ratio("citation_only", True) <= 400)),
    f("forward selection features over POSTHOC features, CITATION_PLUS_MESH, between 300 and 400", "yes",
      yn(300 <= ratio("citation_plus_mesh", False) <= 400), yn(300 <= ratio("citation_plus_mesh", True) <= 400)),
])
pp_o, pp_p = pubtypes_pattern(False), pubtypes_pattern(True)
claim("text.pubtypes", [
    f("adding publication types raises AUC, both models", "yes",
      yn(all(pp_o[k]["auc"] > 0 for k in pp_o)), yn(all(pp_p[k]["auc"] > 0 for k in pp_p))),
    f("adding publication types lowers average precision by more than it raises AUC, both models", "yes",
      yn(all(-pp_o[k]["average_precision"] > pp_o[k]["auc"] for k in pp_o)),
      yn(all(-pp_p[k]["average_precision"] > pp_p[k]["auc"] for k in pp_p))),
    f("adding publication types lowers F1, both models", "yes",
      yn(all(pp_o[k]["f1"] < 0 for k in pp_o)), yn(all(pp_p[k]["f1"] < 0 for k in pp_p))),
    f("adding publication types raises MSE, both models", "yes",
      yn(all(pp_o[k]["mse"] > 0 for k in pp_o)), yn(all(pp_p[k]["mse"] > 0 for k in pp_p))),
])

# Methods: seven sets chosen for CITATION_ONLY, ten for CITATION_PLUS_MESH; ~45 million features;
# training years "over 5 million articles"; best single feature "randomized", F1 ~0.72.
claim("text.selected_sets", [
    f("feature sets chosen, CITATION_ONLY", "7", len(sel["citation_only"]["chosen"])),
    f("feature sets chosen, CITATION_PLUS_MESH", "10", len(sel["citation_plus_mesh"]["chosen"])),
])
cand = load("models.json")["candidate_features"]
claim("text.feature_count", [f("unique features of every candidate set, millions (approximately 45)", "45",
                               sum(cand.values()) / 1e6)])
claim("text.training_size", [f("training years 1987-2010 over 5 million citations", "yes",
                               yn(ds["train_years"] > 5_000_000))])
claim("text.randomized", [
    f("F1 of \"randomized\" in the title or abstract (about 0.72)", "0.72",
      single["randomized"]["title_or_abstract"]["f1"]),
    f("\"randomized\" is the best single feature", "yes", yn(single["best_is_randomized"])),
])
if frac:
    claim("text.training_fraction", [f("AUC at 10% within 0.002 of AUC at 5% (flat between 5% and 10%)", "yes",
                                       yn(abs(frac["0.1"]["auc"] - frac["0.05"]["auc"]) <= 0.002))])

# Results: the disagreement counts, and the estimates built on them with Fig. 1's rates.
claim("text.disagreements", [
    f("articles with confidence >= 0.95 without the RCT publication type", "1811", dis["conf_ge_0.95_without_rct_pt"]),
    f("articles with confidence >= 0.50 without the RCT publication type", "19838", dis["conf_ge_0.50_without_rct_pt"]),
    f("articles with the RCT publication type, 1987-2012", "277789", dis["rct_pt"]),
    f("articles with confidence <= 0.05 with the RCT publication type", "20523", dis["conf_le_0.05_with_rct_pt"]),
    f("the ten lowest of these below 0.0005", "yes", yn((dis["lowest10_max_confidence"] or 1) < 0.0005)),
])
# The estimates multiply these counts by Fig. 1's manual-review rates, which cannot be recomputed:
# only their arithmetic is checked (text.arithmetic); "observed" holds the paper's own arithmetic.
claim("text.estimates", [
    f("70% of the >= 0.95 set expected to be RCTs", "1268", None, round(0.70 * 1811)),
    f("40% of the >= 0.50 set expected to be RCTs", "7935", None, round(0.40 * 19838)),
    f("these as a share of the RCT-tagged articles, %", "3", None, 100 * 7935 / 277789),
    f("95% of the <= 0.05 set estimated wrongly tagged", "19497", None, round(0.95 * 20523)),
    f("these as a share of the RCT-tagged articles, % (about 7%)", "7", None, 100 * 19497 / 277789),
    f("possible RCT_PT errors, thousands (approximately 12 900, 5% of the tagged articles)", "12.9", None, 0.05 * 277789 / 1000),
    f("additional RCTs and possible errors combined, thousands (about 20 000)", "20", None, (7900 + 12900) / 1000),
])
claim("text.cholecystitis", [
    f("articles of the topic search in the dataset", "3883", topic["in_dataset"]),
    f("with the RCT publication type", "795", topic["with_rct_pt"]),
    f("share with the RCT publication type, % (about 20%)", "20", 100 * topic["with_rct_pt"] / max(topic["in_dataset"], 1),
      100 * 795 / 3883),
    f("without the RCT publication type", "3088", topic["without_rct_pt"], 3883 - 795),
    f("of these, confidence <= 0.10", "2751", topic["without_rct_pt_le_0.10"]),
    f("share of the unannotated articles skipped, %", "85", 100 * topic["without_rct_pt_le_0.10"] / max(topic["without_rct_pt"], 1),
      100 * 2751 / 3088),
    f("of these, confidence > 0.10", "337", topic["without_rct_pt_gt_0.10"], 3088 - 2751),
])

# arithmetic checks that need no run: the Hanley-McNeil intervals are symmetric about the AUC
for t in ("table1", "table2"):
    for y in ("2011", "2012"):
        a, lo, hi = (float(P[t][f"{y}.{k}"]) for k in ("auc", "auc_ci_low", "auc_ci_high"))
        claims.setdefault("_interval_midpoints", []).append(
            {"table": t, "year": y, "auc": P[t][f"{y}.auc"], "midpoint": round((lo + hi) / 2, 4)})

json.dump({"tables": tables, "claims": claims}, open(os.path.join(out_dir, "comparison.json"), "w"), indent=1)
for t, v in tables.items():
    print(t, v["summary"])
for cid, c in claims.items():
    if cid.startswith("_"):
        continue
    print(cid, [(x["expected"], x["observed"] if not isinstance(x["observed"], float) else round(x["observed"], 4))
                for x in c["fields"]])

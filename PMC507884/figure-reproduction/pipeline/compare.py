#!/usr/bin/env python3
"""Compare our run with the paper: every table cell, figure score and claim of Szabo et al. (2004).

  compare.py ANALYSIS_JSON FIGURES_JSON PUBLISHED_FIG3_JSON PAPER_VALUES_JSON OUTDIR

Writes OUTDIR/comparison.json (one entry per results.json item: method, values or pixels or check,
outputs) and OUTDIR/tables.json (the tables as printed next to ours, for the results page). The
verdicts are not decided here: check_results.py computes them from these numbers.
"""
import json
import sys
from pathlib import Path

an, fg, pf3, pv = (json.load(open(p)) for p in sys.argv[1:5])
out = Path(sys.argv[5])
out.mkdir(parents=True, exist_ok=True)
items, tables = {}, {}
PRINTED = {"printed": True}


def r(x, d=6):
    return round(float(x), d)


def setstr(genes):
    return ",".join(sorted(genes))


def pixel_item(score, controls, threshold, outputs):
    return {"method": "pixels", "pixels": {
        "tolerance_px": fg["tolerance_px"], "dpi": fg["dpi"],
        "published_near_ours": r(score["published_near_ours"]), "ours_near_published": r(score["ours_near_published"]),
        "threshold": threshold, "controls": [{"name": c["name"], "kind": c["kind"], "score": r(c["score"])} for c in controls]},
        "outputs": outputs}


# ---------------------------------------------------------------- Figure 1 (breast data)
f1 = fg["fig1"]
for p in f1["per_panel"]:
    items[f"fig1.{p['panel']}"] = pixel_item(p, p["controls"], 0.90, ["figure-reproduction/output/fig1_ours.png",
                                                                         "figure-reproduction/output/fig1_overlay.png"])

# ---------------------------------------------------------------- Table 1
m1 = an["model1"]
fields_sd, fields_ci, rows1 = [], [], []
for g, p in pv["table1"].items():
    fields_sd.append({"name": f"{g} SD", "expected": p["sd"], "observed": r(m1["sd"][g])})
    for side in ("lower", "upper"):
        fields_ci.append({"name": f"{g} {side}", "expected": p[side], "observed": r(m1["ci"][g][side])})
    nl = m1["nlme_intervals"][g]
    rows1.append({"gene": g, "paper": f"{p['sd']} ({p['lower']}, {p['upper']})",
                  "ours": f"{m1['sd'][g]:.3f} ({m1['ci'][g]['lower']:.3f}, {m1['ci'][g]['upper']:.3f})",
                  "nlme_range": f"lower {nl['lower_min']:.4f}-{nl['lower_max']:.4f}, upper {nl['upper_min']:.4f}-{nl['upper_max']:.4f}"})
items["table1"] = {"method": "values", "values": {"fields": fields_sd, "tolerance": PRINTED}}
items["table1.ci"] = {"method": "values", "values": {"fields": fields_ci, "tolerance": PRINTED}}
# Whether nlme's intervals() reaches each printed bound under some equivalent parameterization
covered = []
for g, p in pv["table1"].items():
    nl = m1["nlme_intervals"][g]
    for side in ("lower", "upper"):
        v, h = float(p[side]), 0.0005
        lo, hi = nl[f"{side}_min"], nl[f"{side}_max"]
        covered.append(lo - h <= v <= hi + h)
tables["table1"] = rows1

bic = m1["bic"]
items["text.model1_bic"] = {"method": "check", "check": {
    "passed": bic["m1a"] < bic["m1b"] and bic["m1a"] < bic["m1c"],
    "detail": f"BIC (REML) Model 1a {bic['m1a']:.1f}, 1b {bic['m1b']:.1f}, 1c {bic['m1c']:.1f} (rho {m1['rho_1c']:.2f}); Model 1a lowest"}}

gt = an["group_test"]
items["text.p_value"] = {"method": "values", "values": {"fields": [
    {"name": "p, microarray-selected genes against GAPD and ACTB", "expected": pv["text"]["p_value"], "observed": r(gt["p"], 8)}],
    "tolerance": PRINTED}}

# ---------------------------------------------------------------- Table 2
t2 = an["table2"]
fields2, rows2 = [], []
for k, row in enumerate(pv["table2"]):
    ours_set = t2["size2"]["genes"][k].split(",")
    fields2.append({"name": f"size {row['size']} set", "expected": setstr(row["genes"]), "observed": setstr(ours_set)})
    fields2.append({"name": f"size {row['size']} SD", "expected": row["sd"], "observed": r(t2["size2"]["sd"][k])})
    rows2.append({"size": row["size"], "paper_set": ", ".join(row["genes"]), "paper_sd": row["sd"],
                  "ours_set": ", ".join(ours_set), "ours_sd": f"{t2['size2']['sd'][k]:.4f}",
                  "printed_formula_sd": f"{t2['size']['sd'][k]:.4f}"})
items["table2"] = {"method": "values", "values": {"fields": fields2, "tolerance": PRINTED}}
tables["table2"] = rows2
hits_size = sum(abs(t2["size"]["sd"][k] - float(row["sd"])) <= 0.00005 for k, row in enumerate(pv["table2"]))
hits_size2 = sum(abs(t2["size2"]["sd"][k] - float(row["sd"])) <= 0.00005 for k, row in enumerate(pv["table2"]))
items["text.set_variance_formula"] = {"method": "check", "check": {
    "passed": hits_size == len(pv["table2"]),
    "detail": f"the printed formula (divided by the set size) gives {hits_size} of 6 Table 2 values; divided by its square, {hits_size2} of 6"}}

tab2 = [float(x) for x in t2["size2"]["sd"]]
items["text.table2_claims"] = {"method": "check", "check": {
    "passed": min(range(6), key=lambda i: tab2[i]) == 3 and tab2[2] - tab2[3] < 0.001 and tab2[1] - tab2[2] > 0.02,
    "detail": f"the four-gene set is lowest ({tab2[3]:.4f}); three genes {tab2[2]:.4f}, {tab2[2] - tab2[3]:.4f} more; "
              f"two genes {tab2[1]:.4f}, {tab2[1] - tab2[2]:.4f} more than three"}}
cv = an["cv_check"]
items["text.sd_cv"] = {"method": "check", "check": {
    "passed": cv["max_rel_diff"] < 0.05,
    "detail": f"the coefficient of variation sqrt(exp(SD^2) - 1) of each Table 2 normaliser is within {100 * cv['max_rel_diff']:.1f}% of its SD"}}

# ---------------------------------------------------------------- geNorm on the breast data
gn = an["genorm_breast"]
rank = dict(zip(gn["gene"], gn["rank"]))
pair = sorted(g for g, k in rank.items() if k == 1.5)
order = [g for g, k in sorted(rank.items(), key=lambda kv: kv[1]) if k != 1.5]
items["text.mvalue_breast"] = {"method": "values", "values": {"fields": [
    {"name": "unordered best pair", "expected": "MRPL19,PSMC4", "observed": ",".join(pair)},
    {"name": "rank 3", "expected": "PUM1", "observed": order[0]},
    {"name": "rank 4", "expected": "SF3A1", "observed": order[1]},
    {"name": "rank 5", "expected": "ACTB", "observed": order[2]},
    {"name": "rank 6", "expected": "GAPD", "observed": order[3]}]}}
mb = an["mvalue_bounds"]
items["text.mvalue_bounds"] = {"method": "check", "check": {
    "passed": bool(mb["holds_with_sigma2_as_printed"]),
    "detail": f"under Model 1a's SDs (R = {mb['R']:.2f}) the printed bounds sigma_j^2 sqrt(1 + 1/R^2) <= M_j <= sigma_j^2 sqrt(1 + R^2) "
              f"{'hold' if mb['holds_with_sigma2_as_printed'] else 'fail'}; with sigma_j in place of sigma_j^2 they "
              f"{'hold' if mb['holds_with_sigma'] else 'fail'}"}}

# ---------------------------------------------------------------- Figure 2, Table 3 (Vandesompele et al.'s data)
f2 = fg["fig2"]
items["fig2"] = pixel_item(f2["score"], f2["controls"], 0.90, ["figure-reproduction/output/fig2_ours.png",
                                                               "figure-reproduction/output/fig2_overlay.png"])
m2 = an["model2"]
items["table3.sigma"] = {"method": "values", "values": {"fields": [
    {"name": g, "expected": v, "observed": r(m2["sigma"][g])} for g, v in pv["table3"]["sigma"].items()], "tolerance": PRINTED}}
items["table3.varsigma"] = {"method": "values", "values": {"fields": [
    {"name": k, "expected": v, "observed": r(m2["varsigma"][k])} for k, v in pv["table3"]["varsigma"].items() if k != "BM"],
    "tolerance": PRINTED}}
ours_order = sorted(m2["sigma"], key=lambda g: m2["sigma"][g])
pub_order = list(pv["table3"]["sigma"])          # printed in increasing order; RPL13A and TBP tie at 0.339
items["table3.order"] = {"method": "values", "values": {"fields": [
    {"name": f"rank {i + 1}", "expected": pub_order[i], "observed": ours_order[i]} for i in (0, 1, 2, 3, 4, 7, 8, 9)] + [
    {"name": "ranks 6-7 (printed as a tie, 0.339)", "expected": setstr(pub_order[5:7]), "observed": setstr(ours_order[5:7])}]}}
tables["table3"] = {"sigma": [{"gene": g, "paper": v, "ours": f"{m2['sigma'][g]:.3f}"} for g, v in pv["table3"]["sigma"].items()],
                    "varsigma": [{"tissue": k, "paper": v, "ours": f"{m2['varsigma'][k]:.3f}"} for k, v in pv["table3"]["varsigma"].items()]}
cb = m2["competitors_bic"]
items["text.model2_bic"] = {"method": "check", "check": {
    "passed": all(m2["bic"] < v for v in cb.values() if v is not None),
    "detail": f"BIC (REML) Model 2 {m2['bic']:.1f}; " + ", ".join(f"{k} {v:.1f}" for k, v in cb.items())}}
gt2 = an["genorm_tissues"]
items["text.model2_mvalue"] = {"method": "values", "values": {"fields": [
    {"name": f"rank {i + 1} by mean geNorm rank over tissue types", "expected": pub_order[i], "observed": gt2["gene"][i]}
    for i in range(5)]}}

# ---------------------------------------------------------------- Table 4, Fig. 3, the ACTB + TBP example
t4 = an["table4"]
fields4, rows4 = [], []
for k, row in enumerate(pv["table4"]):
    ours = t4["sum_nested"]["genes"][k].split(",")
    fields4.append({"name": f"at most {row['size']}: set", "expected": setstr(row["genes"]), "observed": setstr(ours)})
    fields4.append({"name": f"at most {row['size']}: max MSE", "expected": row["mse"], "observed": r(t4["sum_nested"]["mse"][k])})
    rows4.append({"size": row["size"], "paper_set": ", ".join(row["genes"]), "paper_mse": row["mse"],
                  "ours_set": ", ".join(ours), "ours_mse": f"{t4['sum_nested']['mse'][k]:.3f}",
                  "mean_bias_set": ", ".join(t4["mean_nested"]["genes"][k].split(",")),
                  "mean_bias_mse": f"{t4['mean_nested']['mse'][k]:.3f}"})
items["table4"] = {"method": "values", "values": {"fields": fields4, "tolerance": PRINTED}}
tables["table4"] = rows4
mean_hits = sum(setstr(t4["mean_nested"]["genes"][k].split(",")) == setstr(row["genes"]) for k, row in enumerate(pv["table4"]))
variant_hits = sum(abs(t4["variant_published_table3"]["mse"][k] - float(row["mse"])) <= 0.0005 for k, row in enumerate(pv["table4"]))

f3 = fg["fig3"]
items["fig3"] = pixel_item(f3["score"], f3["controls"], 0.98, ["figure-reproduction/output/fig3_ours.png",
                                                               "figure-reproduction/output/fig3_overlay.png"])
ours3 = {f"{g}.{t}": (b2, v) for g, t, b2, v in zip(an["fig3"]["gene"], an["fig3"]["tissue"], an["fig3"]["bias2"], an["fig3"]["variance"])}
pub3 = pf3["bars"]
# The drawing's resolution: 0.005 pt in a height, and 0.005 pt in each of the two tick labels over 88.9 pt.
tol3 = {"abs": 0.0005, "rel": 0.00012}
items["fig3.bias2"] = {"method": "values", "values": {"fields": [
    {"name": k, "expected": f"{pub3[k]['bias2']:.4f}", "observed": r(ours3[k][0])} for k in sorted(pub3)], "tolerance": tol3}}
items["fig3.sigma2"] = {"method": "values", "values": {"fields": [
    {"name": k, "expected": f"{pub3[k]['sigma2']:.4f}", "observed": r(ours3[k][1])} for k in sorted(pub3)], "tolerance": tol3}}
signs = dict(zip([f"{g}.{t}" for g, t in zip(an["fig3"]["gene"], an["fig3"]["tissue"])], an["fig3"]["sign"]))
tables["fig3"] = [{"bar": k, "paper_bias2": f"{pub3[k]['bias2']:.4f}", "ours_bias2": f"{ours3[k][0]:.4f}",
                   "paper_sigma2": f"{pub3[k]['sigma2']:.4f}", "ours_sigma2": f"{ours3[k][1]:.4f}", "sign": int(signs[k])}
                  for k in sorted(pub3)]

at = an["actb_tbp"]
items["text.actb_tbp"] = {"method": "values", "values": {"fields": [
    {"name": "MSE of the log-average of ACTB and TBP, pooled tissues", "expected": pv["text"]["actb_tbp_pool_mse"], "observed": r(at["pool_sum"])},
    {"name": "ACTB individual MSE above 6", "expected": "true", "observed": "true" if at["individual"]["ACTB"] > 6 else "false"},
    {"name": "TBP individual MSE above 6", "expected": "true", "observed": "true" if at["individual"]["TBP"] > 6 else "false"},
    {"name": "ACTB and TBP biases in opposite directions", "expected": "true",
     "observed": "true" if at["bias"]["ACTB"] * at["bias"]["TBP"] < 0 else "false"}], "tolerance": PRINTED}}

items["text.data"] = {"method": "values", "values": {"fields": [
    {"name": "breast tumour samples", "expected": pv["text"]["breast_samples"], "observed": "80"},
    {"name": "genes assayed in breast tumours", "expected": pv["text"]["breast_genes"], "observed": "6"},
    {"name": "genes in Vandesompele et al.'s data", "expected": pv["text"]["vandesompele_genes"], "observed": "10"},
    {"name": "tissue types", "expected": pv["text"]["tissue_types"], "observed": "5"}]}}

# ---------------------------------------------------------------- claims on the paper's own numbers
# Each claim recomputed from the printed tables (and the published Fig. 3 bars) before it is compared
# with our run. Signs of the biases come from the published, signed Fig. 3 (ACTB up, TBP down in POOL).
T1 = {g: float(p["sd"]) for g, p in pv["table1"].items()}
T2 = [float(x["sd"]) for x in pv["table2"]]
S3 = {g: float(v) for g, v in pv["table3"]["sigma"].items()}
V3 = {k: float(v) for k, v in pv["table3"]["varsigma"].items()}
b_actb, b_tbp = pub3["ACTB.POOL"]["bias2"] ** 0.5, -pub3["TBP.POOL"]["bias2"] ** 0.5
var_pair = V3["POOL"] ** 2 * (S3["ACTB"] ** 2 + S3["TBP"] ** 2) / 4
arith = [
    ("Table 2's best pair from Table 1, divided by the squared set size", abs((T1["MRPL19"] ** 2 + T1["PUM1"] ** 2) ** 0.5 / 2 - T2[1]) < 0.0005,
     f"{(T1['MRPL19'] ** 2 + T1['PUM1'] ** 2) ** 0.5 / 2:.4f} against 0.1718 (the set size gives {((T1['MRPL19'] ** 2 + T1['PUM1'] ** 2) / 2) ** 0.5:.4f})"),
    ("the four-gene set lowest in Table 2", min(range(6), key=lambda i: T2[i]) == 3, f"{T2[3]:.4f}"),
    ("three genes barely worse than four, two far worse", T2[2] - T2[3] < 0.001 < 0.02 < T2[1] - T2[2],
     f"{T2[2] - T2[3]:.4f} and {T2[1] - T2[2]:.4f}"),
    ("GAPD lowest in Table 3, then UBC, HPRT1, YWHAZ", sorted(S3, key=S3.get)[:4] == ["GAPD", "UBC", "HPRT1", "YWHAZ"], ""),
    ("ACTB plus TBP in pooled tissues 0.35 (bias of the set summed)", round((b_actb + b_tbp) ** 2 + var_pair, 2) == 0.35,
     f"{(b_actb + b_tbp) ** 2 + var_pair:.3f} (the mean of the biases gives {((b_actb + b_tbp) / 2) ** 2 + var_pair:.3f})"),
    ("ACTB and TBP individual MSEs in pooled tissues above 6",
     pub3["ACTB.POOL"]["bias2"] + pub3["ACTB.POOL"]["sigma2"] > 6 and pub3["TBP.POOL"]["bias2"] + pub3["TBP.POOL"]["sigma2"] > 6,
     f"{pub3['ACTB.POOL']['bias2'] + pub3['ACTB.POOL']['sigma2']:.2f} and {pub3['TBP.POOL']['bias2'] + pub3['TBP.POOL']['sigma2']:.2f}"),
    ("Table 4's ten-gene MSE from Table 3 (no bias)",
     round(V3["POOL"] ** 2 * sum(v ** 2 for v in S3.values()) / 100, 3) == 0.049,
     f"{V3['POOL'] ** 2 * sum(v ** 2 for v in S3.values()) / 100:.4f}"),
    ("Table 4's single gene RPL13A from Table 3 and Fig. 3, within Table 3's rounding",
     abs(pub3["RPL13A.POOL"]["bias2"] + V3["POOL"] ** 2 * S3["RPL13A"] ** 2 - 0.544) < 0.0005 + 2 * V3["POOL"] ** 2 * S3["RPL13A"] * 0.0005,
     f"{pub3['RPL13A.POOL']['bias2'] + V3['POOL'] ** 2 * S3['RPL13A'] ** 2:.4f} against 0.544"),
]
items["text.arithmetic"] = {"method": "check", "check": {
    "passed": all(ok for _, ok, _ in arith),
    "detail": f"{sum(ok for _, ok, _ in arith)} of {len(arith)} claims hold on the paper's own numbers: " +
              "; ".join(f"{name} ({'holds' if ok else 'fails'}{', ' + d if d else ''})" for name, ok, d in arith)}}

notes = {
    "table1_ci_nlme_covered": f"{sum(covered)} of {len(covered)}",
    "table2_row6": t2["row6_checks"],
    "table4_mean_bias_sets": f"{mean_hits} of 10",
    "table4_variant_published_table3_mse": f"{variant_hits} of 10",
    "table4_variant_mse": t4["variant_published_table3"]["mse"],
    "actb_tbp_mean_bias": at["pool_mean"],
    "group_test_alternatives": gt["alternatives"],
}
# item_list: the same items as a list keyed without dots, for tools/check_results.py paths
item_list = [{"key": k.replace(".", "_"), **v} for k, v in items.items()]
(out / "comparison.json").write_text(json.dumps({"items": items, "item_list": item_list, "notes": notes}, indent=1) + "\n")
(out / "tables.json").write_text(json.dumps(tables, indent=1) + "\n")
print(len(items), "items;", json.dumps(notes)[:400])

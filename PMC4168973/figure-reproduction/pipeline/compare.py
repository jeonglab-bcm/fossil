#!/usr/bin/env python3
"""Compare our run with the paper: every printed value and every scored figure panel.

  compare.py PAPER_VALUES OUT_DIR

Reads OUT_DIR/clinical.json, models.json, table3.json and fig/pixel_scores.json and writes
OUT_DIR/comparison.json: one entry per results.json item with its method and its values, pixels
or check, and outputs. Labels, sources, assumptions and causes are in results_notes.json.
Model-dependent p-values (the LASSO models are fitted with random cross-validation folds) are
compared as -log10(p) within 1 (the same order of magnitude); AUCs within 0.03. Values that
depend only on the data are compared at printed precision.
"""
import json
import math
import re
import sys
from pathlib import Path

pv = json.load(open(sys.argv[1]))
out = Path(sys.argv[2])
clin = json.load(open(out / "clinical.json"))
mod = json.load(open(out / "models.json"))
t3 = json.load(open(out / "table3.json"))
px = json.load(open(out / "pixel_scores.json"))
items = {}
P_TOL = {"abs": 1}
AUC_TOL = {"abs": 0.03}


def mlog(p):
    # None: no p-value (a model that keeps no feature has one risk group, R writes "NA")
    return round(-math.log10(float(p)), 4) if p not in (None, 0, "NA") else None


def sig(v, n=6):
    return None if v is None else float(f"{v:.{n}g}")


def field(name, expected, observed, tol=None):
    f = {"name": name, "expected": expected, "observed": observed}
    if tol is not None:
        f["tolerance"] = tol
    return f


def values(fields, tol=None):
    return {"method": "values", "values": {"fields": fields, "tolerance": tol or {"printed": True}}}


# Table 1: counts at printed precision; percentages within 1 point (the paper's rounding is not
# consistent: Ivshina 89 of 249 = 35.7% is printed 35%, Desmedt 64 of 198 = 32.3% is printed 33%)
for s, exp in pv["table1"].items():
    ours = clin["table1"][s]
    fs = []
    for k, e in exp.items():
        o = ours.get(k)
        m = re.match(r"(\d+) \((\d+)%\)", e)
        mo = re.match(r"(\d+) \((\d+)%\)", o) if o else None
        if m:
            n = int(clin["table1"][s]["patients"])
            fs.append(field(f"{k}, count", m.group(1), mo.group(1) if mo else None))
            fs.append(field(f"{k}, %", m.group(2), round(100 * int(mo.group(1)) / n, 2) if mo else None, {"abs": 1}))
        else:
            fs.append(field(k, e, o.split(" ")[0] if o else None))
    items[f"table1.{s}"] = values(fs)

items["fig1.A.chisq"] = values([field(k, v, sig(clin["fig1_chisq"][k])) for k, v in pv["fig1_chisq"].items()])
items["fig3.chisq"] = values([field(k, v, sig(clin["fig1_chisq"][k])) for k, v in pv["fig3_chisq"].items()])
items["fig1.logrank"] = values([field(k, v, sig(clin["fig1_logrank"][k])) for k, v in pv["fig1_logrank"].items()])
items["fig1.A.pam50_groups"] = values([field("chi-square p, PAM50 clusters against relapse (-log10)",
    mlog(pv["fig1_pam50_groups"]), mlog(mod["fig1a"]["chisq_pam50_groups"]), P_TOL)])
items["fig3.values"] = values([
    field("chi-square p, PDS clusters against relapse (-log10)", mlog(pv["fig3"]["chisq_pds_groups"]),
          mlog(mod["fig3"]["chisq_pds_groups"]), P_TOL),
    field("correlation of median PDS with relapse", pv["fig3"]["cor_median_pds"], sig(mod["fig3"]["cor_median_pds"], 4)),
    field("correlation of median PAM50 expression with relapse", pv["fig3"]["cor_median_pam50"], sig(mod["fig3"]["cor_median_pam50"], 4))])
items["table2.clinical_univariate"] = values([field(k, pv["table2_clinical"][kk][2], sig(clin["table2_clinical_univariate"][k]))
    for k, kk in (("LN", "node"), ("size", "size_mm"), ("grade", "grade"), ("p53", "p53"))])

# Table 2, genomic model: is each of the paper's 15 pathways selected, with what coefficient
g = mod["genomic"]
fs = []
for pw, (c, hr, p) in pv["table2_genomic"].items():
    fs.append(field(f"{pw} selected", "yes", "yes" if pw in g["coefficients"] else "no"))
    fs.append(field(f"{pw} coefficient", c, sig(g["coefficients"].get(pw, 0.0))))
items["table2.genomic"] = values(fs)
items["table2.genomic_univariate"] = values([
    field(f"{pw} univariate p (-log10)", mlog(p), mlog(mod["variant_paper_coefficients"]["univariate_p"].get(pw)), P_TOL)
    for pw, (c, hr, p) in pv["table2_genomic"].items()])
cm = mod["clinical"]
fs = []
for k, (c, hr, p) in pv["table2_clinical"].items():
    fs.append(field(f"{k} selected", "yes", "yes" if k in cm["coefficients"] else "no"))
    fs.append(field(f"{k} coefficient", c, sig(cm["coefficients"].get(k, 0.0))))
fs.append(field("other features selected", "none", ", ".join(sorted(set(cm["coefficients"]) - set(pv["table2_clinical"]))) or "none"))
items["table2.clinical"] = values(fs)
bm = mod["combined"]
items["table2.combined"] = values([
    field("genomic-model pathways kept", "10", str(bm["genomic_pathways_kept"])),
    field("lymph node selected", "yes", "yes" if "node" in bm["coefficients"] else "no"),
    field("tumour size selected", "yes", "yes" if "size_mm" in bm["coefficients"] else "no"),
    field("grade selected", "no", "yes" if "grade" in bm["coefficients"] else "no"),
    field("p53 selected", "no", "yes" if "p53" in bm["coefficients"] else "no")])

def pa(prefix, ps, aucs, get):
    fs = []
    for k, v in ps.items():
        fs.append(field(f"{k} log-rank p {v} (-log10)", mlog(v), mlog(get(k)["p"]), P_TOL))
    for k, v in aucs.items():
        fs.append(field(f"{k} AUC", v, sig(get(k)["auc"], 4), AUC_TOL))
    return values(fs)

items["fig4.values"] = pa("fig4", pv["fig4"]["p"], pv["fig4"]["auc"], lambda k: g["sets"][k])
items["fig5.values"] = pa("fig5", pv["fig5"]["p"], pv["fig5"]["auc"],
                          lambda k: mod["fig5"][k.split("_")[0]][k.split("_")[1]])
items["fig6.values"] = pa("fig6", pv["fig6"]["p"], pv["fig6"]["auc"], lambda k: mod["fig6"].get(k, {"p": None, "auc": None}))

if "nki70" in mod:
    items["figS3.nki70"] = values([field("NKI70 log-rank p 2.58e-3 (-log10)", mlog(pv["nki70"]["p"]), mlog(mod["nki70"]["p"]), P_TOL),
                                   field("NKI70 AUC", pv["nki70"]["auc"], sig(mod["nki70"]["auc"], 4), AUC_TOL)])

# Claims about orderings and LOOCV t-tests
f5 = mod["fig5"]
# a model without a p-value (no feature kept) is not better than anything
lt = lambda a, b: a is not None and b is not None and a < b
better = [s for s in f5 if f5[s]["pathway"]["auc"] > f5[s]["gene"]["auc"] and lt(f5[s]["pathway"]["p"], f5[s]["gene"]["p"])]
items["text.fig5_claim"] = {"method": "check", "check": {"passed": len(better) == 4,
    "detail": f"pathway-based better than gene-based (lower p and higher AUC) in {len(better)} of 4 sets: {', '.join(better) or 'none'}"}}
loo = mod["loo"]
s2 = [s for s in ("miller", "pawitan", "ivshina", "desmedt")
      if lt(loo[f"S2_{s}"]["t_p_auc"], 0.001) and lt(loo[f"S2_{s}"]["t_p_mlog10p"], 0.001)
      and loo[f"S2_{s}"]["pathway_median_auc"] > loo[f"S2_{s}"]["gene_median_auc"]]
items["figS2.claim"] = {"method": "check", "check": {"passed": len(s2) == 4,
    "detail": f"LOOCV: pathway-based above gene-based with t-test p < 0.001 for both p and AUC in {len(s2)} of 4 sets"}}
f6 = mod["fig6"]
order = []
for s in ("miller", "ivshina"):
    if all(f"{m}_{s}" in f6 for m in ("combined", "genomic", "clinical")):
        ok = (f6[f"combined_{s}"]["auc"] > f6[f"genomic_{s}"]["auc"] > f6[f"clinical_{s}"]["auc"]
              and f6[f"combined_{s}"]["p"] < f6[f"genomic_{s}"]["p"])
        order.append(f"{s} {'yes' if ok else 'no'}")
items["text.fig6_claim"] = {"method": "check", "check": {"passed": all(o.endswith("yes") for o in order) and len(order) == 2,
    "detail": "combined > genomic > clinical by AUC, combined below genomic by p: " + ", ".join(order)}}
s4 = []
for s in ("miller", "ivshina"):
    k = f"S4_{s}"
    if k in loo:
        L = loo[k]
        ok = (L["t_p_combined_vs_pathway_auc"] < 0.001 and L["t_p_pathway_vs_clinic_auc"] < 0.001
              and L["combined"]["median_auc"] > L["pathway"]["median_auc"] > L["clinic"]["median_auc"])
        s4.append(f"{s} {'yes' if ok else 'no'}")
items["figS4.claim"] = {"method": "check", "check": {"passed": len(s4) == 2 and all(x.endswith("yes") for x in s4),
    "detail": "LOOCV: combined > pathway > clinical by AUC with t-test p < 0.001: " + (", ".join(s4) or "Ivshina not evaluable")}}
s1 = mod["s1"]
med = s1["median_auc"]
ordered = med["1/2"] > med["1/4"] > med["1/8"] > med["1/16"]
inrange = s1["auc_range"][0] >= 0.69 - 0.005 and s1["auc_range"][1] <= 0.81 + 0.005
items["figS1.claim"] = {"method": "check", "check": {"passed": bool(ordered and s1["t_p_half_vs_quarter"] < 0.05 and inrange),
    "detail": (f"median AUC 1/2 {med['1/2']:.3f}, 1/4 {med['1/4']:.3f}, 1/8 {med['1/8']:.3f}, 1/16 {med['1/16']:.3f}; "
               f"1/2 against 1/4 t-test p {s1['t_p_half_vs_quarter']:.3g}; AUC range {s1['auc_range'][0]:.3f} to {s1['auc_range'][1]:.3f} "
               "(paper: decreasing, p < 0.05, 0.69 to 0.81)")}}


# Claims in the text, recomputed first from the paper's own numbers (an arithmetic check that says
# nothing about our run), then from our run.
t1 = pv["table1"]
f4p, f4a, f5p, f5a, f6p, f6a = (pv["fig4"]["p"], pv["fig4"]["auc"], pv["fig5"]["p"], pv["fig5"]["auc"],
                                pv["fig6"]["p"], pv["fig6"]["auc"])
F = float
claims = [
    ("three test sets hold 606 patients, about 2.5 times the 236 of the training set",
     int(t1["pawitan"]["patients"]) + int(t1["ivshina"]["patients"]) + int(t1["desmedt"]["patients"]) == 606
     and round(606 / int(t1["miller"]["patients"]), 1) in (2.5, 2.6)),
    ("every test set log-rank p < 0.0005 (Fig. 4)", all(F(f4p[k]) < 5e-4 for k in ("pawitan", "ivshina", "desmedt"))),
    ("average test AUC 0.68 (Fig. 4E)", round(sum(F(f4a[k]) for k in ("pawitan", "ivshina", "desmedt")) / 3, 2) == 0.68),
    ("pathway-based better than gene-based on all four sets, by p and AUC (Fig. 5)",
     all(F(f5p[f"{s}_pathway"]) < F(f5p[f"{s}_gene"]) and F(f5a[f"{s}_pathway"]) > F(f5a[f"{s}_gene"])
         for s in ("miller", "pawitan", "ivshina", "desmedt"))),
    ("combined p at least 3 orders of magnitude below genomic and clinical, on both sets (Fig. 6)",
     all(math.log10(F(f6p[f"{m}_{s}"])) - math.log10(F(f6p[f"combined_{s}"])) >= 3
         for s in ("miller", "ivshina") for m in ("genomic", "clinical"))),
    ("AUC combined > genomic > clinical on both sets (Fig. 6G)",
     all(F(f6a[f"combined_{s}"]) > F(f6a[f"genomic_{s}"]) > F(f6a[f"clinical_{s}"]) for s in ("miller", "ivshina"))),
    ("Table 2 hazard ratio = exp(coefficient), all 19 rows",
     all(abs(math.exp(F(c)) - F(h)) <= 5e-6 * max(1, F(h)) for c, h, _ in list(pv["table2_genomic"].values()) + list(pv["table2_clinical"].values()))),
    ("the combined model keeps ten of the fifteen pathways (Table 2 stars)", len(pv["table2_combined_starred"]) == 10),
    ("about 1/3 of the expressed genes are covered (3200 of 10,000)", round(3200 / 10000, 1) == 0.3),
]
back = [c for c, ok in claims if ok]
items["text.arithmetic"] = {"method": "check", "check": {"passed": len(back) == len(claims),
    "detail": f"{len(back)} of {len(claims)} claims come back from the paper's own tables and figure titles"
              + ("" if len(back) == len(claims) else "; not: " + "; ".join(c for c, ok in claims if not ok))}}

# The same claims on our run
g4 = mod["genomic"]["sets"]
ours_claims = [
    field("every test set log-rank p < 0.0005 (Fig. 4)", "yes",
          "yes" if all(g4[k]["p"] < 5e-4 for k in ("pawitan", "ivshina", "desmedt")) else "no"),
    field("average test AUC (Fig. 4E)", "0.68", round(sum(g4[k]["auc"] for k in ("pawitan", "ivshina", "desmedt")) / 3, 4), AUC_TOL),
    field("combined p at least 3 orders of magnitude below genomic and clinical, both sets (Fig. 6)", "yes",
          "yes" if all(f"{m}_{s}" in f6 and f"combined_{s}" in f6
                       and math.log10(f6[f"{m}_{s}"]["p"]) - math.log10(f6[f"combined_{s}"]["p"]) >= 3
                       for s in ("miller", "ivshina") for m in ("genomic", "clinical")) else "no"),
]
items["text.main_claims"] = values(ours_claims)

# Table 3, genomic model columns
fs = []
for gname, (cg, cc, wg, wc) in pv["table3"].items():
    ours = t3["genes"].get(gname, {"count": 0, "weighted": 0.0})
    fs.append(field(f"{gname} count", str(cg), str(ours["count"])))
    fs.append(field(f"{gname} weighted", wg, round(ours["weighted"], 9), {"abs": 1e-5}))
items["table3.genomic"] = values(fs)

cov = t3["coverage"]
ok = [cov["pathways"] == 403, cov["genes_in_pathways"] > 4500, cov["genes_in_pathways_expressed"] > 3200,
      cov["genes_on_array"] > 14000, cov["genes_on_array_expressed"] > 10000]
items["text.coverage"] = {"method": "check", "check": {"passed": all(ok),
    "detail": (f"403 pathways: {cov['pathways']}; over 4500 genes in them: {cov['genes_in_pathways']}; over 3200 expressed "
               f"(mean log2 > 7): {cov['genes_in_pathways_expressed']}; U133A over 14,000 genes: {cov['genes_on_array']}; "
               f"over 10,000 expressed: {cov['genes_on_array_expressed']}")}}

# Pixel-scored panels
for pid, r in px.items():
    items[pid] = {"method": "pixels", "pixels": r["pixels"],
                  "outputs": [f"figure-reproduction/output/fig{r['figure']}_ours.png",
                              f"figure-reproduction/output/fig{r['figure']}_overlay.png"]}

item_list = [dict(key=k.replace(".", "_"), **v) for k, v in items.items()]
(out / "comparison.json").write_text(json.dumps({"items": items, "item_list": item_list}, indent=1) + "\n")
print(f"{len(items)} items")

"""The claims of the text, each as fields: the paper's printed value, ours, and the same statement
recomputed from the paper's own tables ("arithmetic"), where it can be.

Usage: claims.py PUBLISHED_VALUES.json METRICS.json COMPARISON.json TABLE4.json OUT.json

"Ours" always comes from our run. The arithmetic column applies our formula to the paper's printed
tables: it checks that we compute each statement the way the paper did, and says nothing about our run.
Fields marked "about" (the text says "~3%") are compared at +-1 unit, fixed before our values were read.
"""
import json
import math
import sys

ABOUT = {"abs": 1.0}


def yn(b):
    return "yes" if b else "no"


def main():
    pubf, metf, compf, t4f, out = sys.argv[1:6]
    P = json.load(open(pubf))
    M = json.load(open(metf))
    C = json.load(open(compf))
    T4 = json.load(open(t4f))
    t2, t3, txt, cnt = P["table2"], P["table3"], P["text"], C["counts"]
    f = lambda x: float(x)  # noqa: E731

    def ours(model, part, k):
        return M[model][part][k]

    def svm(fs, part, k):
        return ours(f"svm:{fs}", part, k)

    def pt2(fs, part, k):
        return f(t2[fs][part][k])

    claims = {}

    def claim(cid, label, fields):
        claims[cid] = {"label": label, "fields": fields}

    claim("text_sider", "SIDER: 888 drugs, 1385 side-effect terms, 61 102 associations, 68.8 side effects per drug", [
        {"name": "drugs", "expected": txt["sider_drugs"]["value"], "observed": cnt["sider_drugs"]},
        {"name": "side-effect terms", "expected": txt["sider_terms"]["value"], "observed": cnt["sider_terms"]},
        {"name": "associations", "expected": txt["sider_associations"]["value"], "observed": cnt["sider_associations"]},
        {"name": "side effects per drug", "expected": txt["sider_mean_per_drug"]["value"], "observed": round(cnt["sider_mean_per_drug"], 6),
         "arithmetic": round(61102 / 888, 6)},
    ])
    claim("text_dataset", "832 drugs (56 of SIDER's 888 unmapped) with 1385 ADRs; 4276 = 881 + 1142 + 2253 features", [
        {"name": "drugs", "expected": txt["drugs"]["value"], "observed": cnt["drugs"], "arithmetic": 888 - 56},
        {"name": "ADRs", "expected": "1385", "observed": cnt["adrs"]},
        {"name": "features", "expected": txt["feature_dimension"]["value"], "observed": cnt["feature_dimension"],
         "arithmetic": sum(int(v) for v in P["table1"].values())},
        {"name": "biological features", "expected": txt["bio_dimension"]["value"], "observed": cnt["bio_dimension"],
         "arithmetic": sum(int(P["table1"][k]) for k in ("Targets", "Transporters", "Enzymes", "Pathways"))},
        {"name": "phenotypic features", "expected": txt["pheno_dimension"]["value"], "observed": cnt["pheno_dimension"],
         "arithmetic": int(P["table1"]["Treatment indications"]) + int(P["table1"]["Other side effects"])},
    ])
    claim("text_headline", "Main claim: adding biological and phenotypic features to chemical structures raises AUC from 0.9054 to 0.9524, precision from 43.37% to 66.17% and recall from 49.25% to 63.06%", [
        {"name": f"{k} {fs}", "expected": v, "observed": round(100 * svm(fs, "all", k) if pct else svm(fs, "all", k), 10),
         "arithmetic": round(100 * pt2(fs, "all", k) if pct else pt2(fs, "all", k), 10)}
        for fs, k, v, pct in (("chem", "auc", "0.9054", False), ("chem+bio+pheno", "auc", "0.9524", False),
                              ("chem", "precision", "43.37", True), ("chem+bio+pheno", "precision", "66.17", True),
                              ("chem", "recall", "49.25", True), ("chem+bio+pheno", "recall", "63.06", True))
    ])
    singles = ("chem", "bio", "pheno")
    best = lambda g: max(singles, key=lambda s: g(s, "all", "auc"))  # noqa: E731
    claim("text_feature_gains", "Feature assessment: pheno has the highest AUC alone; adding bio raises AUC by 0.004 (0.02 for ADR_50+), precision by ~3% and recall by ~1%; adding pheno raises precision by ~21% and recall by ~15%", [
        {"name": "pheno has the highest AUC of the single feature sets", "expected": "yes", "observed": yn(best(svm) == "pheno"), "arithmetic": yn(best(pt2) == "pheno")},
        {"name": "AUC gain of bio, all ADRs", "expected": txt["bio_gain_all"]["value"], "observed": round(svm("chem+bio", "all", "auc") - svm("chem", "all", "auc"), 10),
         "arithmetic": round(pt2("chem+bio", "all", "auc") - pt2("chem", "all", "auc"), 10)},
        {"name": "AUC gain of bio, ADR_50+", "expected": txt["bio_gain_50"]["value"], "observed": round(svm("chem+bio", "50+", "auc") - svm("chem", "50+", "auc"), 10),
         "arithmetic": round(pt2("chem+bio", "50+", "auc") - pt2("chem", "50+", "auc"), 10)},
    ] + [
        {"name": f"{nm} (about, points)", "expected": txt[key]["value"], "tolerance": ABOUT,
         "observed": round(100 * (svm(fs, "all", k) - svm("chem", "all", k)), 10),
         "arithmetic": round(100 * (pt2(fs, "all", k) - pt2("chem", "all", k)), 10)}
        for nm, key, fs, k in (("precision gain of bio", "bio_precision_gain", "chem+bio", "precision"),
                               ("recall gain of bio", "bio_recall_gain", "chem+bio", "recall"),
                               ("precision gain of pheno", "pheno_precision_gain", "chem+pheno", "precision"),
                               ("recall gain of pheno", "pheno_recall_gain", "chem+pheno", "recall"))
    ])
    ks = C["ks"]
    claim("text_ks", "KS tests on per-ADR AUCs (Bonferroni-corrected): chem to chem+bio p = 1.45E-07 and chem to chem+bio+pheno p = 1.10E-15, both significant; the drop from pheno to chem+bio+pheno is not (p = 0.177)", [
        {"name": f"{nm}, log10 p", "expected": f"{math.log10(float(txt[key]['value'])):.2f}",
         "observed": round(math.log10(ks[key]["bonferroni3"]), 6)}
        for nm, key in (("chem to chem+bio", "ks_chem_vs_chembio"), ("chem to chem+bio+pheno", "ks_chem_vs_chembiopheno"),
                        ("pheno to chem+bio+pheno", "ks_pheno_vs_chembiopheno"))
    ] + [
        {"name": "chem to chem+bio significant", "expected": "yes", "observed": yn(ks["ks_chem_vs_chembio"]["bonferroni3"] < 0.05), "arithmetic": yn(f(txt["ks_chem_vs_chembio"]["value"]) < 0.05)},
        {"name": "chem to chem+bio+pheno significant", "expected": "yes", "observed": yn(ks["ks_chem_vs_chembiopheno"]["bonferroni3"] < 0.05), "arithmetic": yn(f(txt["ks_chem_vs_chembiopheno"]["value"]) < 0.05)},
        {"name": "pheno to chem+bio+pheno significant", "expected": "no", "observed": yn(ks["ks_pheno_vs_chembiopheno"]["bonferroni3"] < 0.05), "arithmetic": yn(f(txt["ks_pheno_vs_chembiopheno"]["value"]) < 0.05)},
    ])
    claim("text_combination", "chem+bio+pheno has a lower global AUC than pheno alone, and its ROC curve almost overlaps that of chem+pheno", [
        {"name": "chem+bio+pheno below pheno", "expected": "yes", "observed": yn(svm("chem+bio+pheno", "all", "auc") < svm("pheno", "all", "auc")),
         "arithmetic": yn(pt2("chem+bio+pheno", "all", "auc") < pt2("pheno", "all", "auc"))},
        {"name": "chem+bio+pheno within 0.001 AUC of chem+pheno", "expected": "yes",
         "observed": yn(abs(svm("chem+bio+pheno", "all", "auc") - svm("chem+pheno", "all", "auc")) < 0.001),
         "arithmetic": yn(abs(pt2("chem+bio+pheno", "all", "auc") - pt2("chem+pheno", "all", "auc")) < 0.001)},
    ])
    claim("text_common_adrs", "Over the common ADRs (ADR_50+) AUC and accuracy fall for every feature set, and the curves separate more", [
        {"name": f"{fs}: AUC and ACC lower over ADR_50+", "expected": "yes",
         "observed": yn(svm(fs, "50+", "auc") < svm(fs, "all", "auc") and svm(fs, "50+", "acc") < svm(fs, "all", "acc")),
         "arithmetic": yn(pt2(fs, "50+", "auc") < pt2(fs, "all", "auc") and pt2(fs, "50+", "acc") < pt2(fs, "all", "acc"))}
        for fs in ("chem", "bio", "pheno", "chem+bio", "chem+pheno", "chem+bio+pheno")
    ] + [{"name": "AUC range of the six sets wider over ADR_50+", "expected": "yes",
          "observed": yn(max(svm(s, '50+', 'auc') for s in t2) - min(svm(s, '50+', 'auc') for s in t2) >
                         max(svm(s, 'all', 'auc') for s in t2) - min(svm(s, 'all', 'auc') for s in t2)),
          "arithmetic": yn(max(pt2(s, '50+', 'auc') for s in t2) - min(pt2(s, '50+', 'auc') for s in t2) >
                           max(pt2(s, 'all', 'auc') for s in t2) - min(pt2(s, 'all', 'auc') for s in t2))}])
    algs = ["svm", "rf", "knn", "nb", "lr"]
    a3 = lambda a, part="all", k="auc": ours(f"{a}:chem+bio+pheno", part, k)  # noqa: E731
    p3 = lambda a, part="all", k="auc": f(t3[a][part][k])  # noqa: E731
    order = lambda g: ">".join(sorted(algs, key=lambda a: -g(a))).upper()  # noqa: E731
    claim("text_methods", "Method comparison: SVM performs best, followed by RF, KNN, NB and LR; SVM's precision (66.17%) and recall (63.06%) beat RF's (63.10%, 62.50%)", [
        {"name": "order by AUC over all ADRs", "expected": "SVM>RF>KNN>NB>LR", "observed": order(a3), "arithmetic": order(p3)},
        {"name": "SVM has the highest AUC", "expected": "yes", "observed": yn(order(a3).startswith("SVM")), "arithmetic": yn(order(p3).startswith("SVM"))},
        {"name": "SVM precision above RF's", "expected": "yes", "observed": yn(a3("svm", "all", "precision") > a3("rf", "all", "precision")),
         "arithmetic": yn(p3("svm", "all", "precision") > p3("rf", "all", "precision"))},
        {"name": "SVM recall above RF's", "expected": "yes", "observed": yn(a3("svm", "all", "recall") > a3("rf", "all", "recall")),
         "arithmetic": yn(p3("svm", "all", "recall") > p3("rf", "all", "recall"))},
    ])
    claim("text_indication", "Discussion: indications alone added to chemical structures raise AUC from 0.9054 to 0.9110", [
        {"name": "AUC of chem+indication", "expected": txt["chem_indication_auc"]["value"], "observed": svm("chem+indication", "all", "auc")},
    ])
    claim("text_class_weights", "Discussion: class weights (1 - class share) raise RF's AUC from 0.9491 to 0.9524; SVM does not improve", [
        {"name": "AUC of weighted RF", "expected": txt["rf_weighted_auc"]["value"], "observed": ours("rf:chem+bio+pheno:paper", "all", "auc")},
        {"name": "weights raise RF's AUC", "expected": "yes", "observed": yn(ours("rf:chem+bio+pheno:paper", "all", "auc") > a3("rf"))},
        {"name": "weights do not raise SVM's AUC", "expected": "yes", "observed": yn(ours("svm:chem+bio+pheno:paper", "all", "auc") <= a3("svm"))},
    ])
    claim("text_data_facts", "Discussion: nausea and headache co-occur in 596 drugs; 49 pairs of ADRs co-occur in more than 400 drugs; 554 ADRs have fewer than five drugs (about 1:166 positives to negatives)", [
        {"name": "drugs with nausea and headache", "expected": txt["nausea_headache_drugs"]["value"], "observed": cnt["nausea_headache_drugs"]},
        {"name": "ADR pairs in more than 400 drugs", "expected": txt["pairs_over_400"]["value"], "observed": cnt["pairs_over_400"]},
        {"name": "ADRs with fewer than five drugs", "expected": txt["rare_adrs"]["value"], "observed": cnt["adrs_fewer_than_5"]},
        {"name": "negatives per positive at five drugs", "expected": txt["rare_ratio"]["value"], "observed": round(cnt["drugs"] / 5, 6), "arithmetic": 832 / 5},
    ])
    rows = T4["rows"]

    def count(drug, fs, key):
        rs = [r for r in rows if r["drug"].startswith(drug) and r["cui"] != "group"]
        return sum(r[fs][key] == "Yes" for r in rs)

    def groups(key):
        return yn(all(r[fs][key] == "Yes" for r in rows if r["cui"] == "group" for fs in ("chem", "chem+bio", "chem+bio+pheno")))

    claim("text_clinical", "Clinical validation: chem detects 1 of 7 rhabdomyolysis ADRs and 0 of 4 heart-attack ADRs, chem+bio 5 and 0, chem+bio+pheno 5 and 2; every classifier detects both grouped ADRs", [
        {"name": f"{drug} detected by {fs}", "expected": str(v), "observed": count(drug, fs, "call"), "arithmetic": count(drug, fs, "published")}
        for drug, fs, v in (("Cerivastatin", "chem", 1), ("Rofecoxib", "chem", 0), ("Cerivastatin", "chem+bio", 5),
                            ("Rofecoxib", "chem+bio", 0), ("Cerivastatin", "chem+bio+pheno", 5), ("Rofecoxib", "chem+bio+pheno", 2))
    ] + [{"name": "both groups detected by every feature set", "expected": "yes", "observed": groups("call"), "arithmetic": groups("published")}])
    v = C["tables"]["fig5"]["fields"]
    o = {x["name"]: x["observed"] for x in v}
    e = {x["name"]: int(x["expected"]) for x in v}
    claim("text_fig5", "Discussion and Fig. 5: 5072 true positives come from chem or bio but not pheno, 10 581 from pheno alone", [
        {"name": "chem or bio, not pheno", "expected": txt["fig5_chem_or_bio_not_pheno"]["value"], "observed": o["chem"] + o["chem&bio"] + o["bio"],
         "arithmetic": e["chem"] + e["chem&bio"] + e["bio"]},
        {"name": "pheno only", "expected": txt["fig5_pheno_only"]["value"], "observed": o["pheno"], "arithmetic": e["pheno"]},
    ])
    # The positives implied by Fig. 5's true-positive totals and Table 2's recalls: a check that the recovered
    # data are the paper's (59,205 positives in the recovered file).
    tot = {"chem": ("chem", "chem&bio", "chem&pheno", "chem&bio&pheno"), "bio": ("bio", "chem&bio", "bio&pheno", "chem&bio&pheno"),
           "pheno": ("pheno", "chem&pheno", "bio&pheno", "chem&bio&pheno")}
    implied = {k: sum(e[x] for x in v) / pt2(k, "all", "recall") for k, v in tot.items()}
    claims["_data_identity"] = {"positives": cnt["positives"], "implied_by_fig5_and_table2": {k: round(x, 1) for k, x in implied.items()}}
    json.dump(claims, open(out, "w"), indent=1)
    print(f"{len([k for k in claims if not k.startswith('_')])} claims", file=sys.stderr)


if __name__ == "__main__":
    main()

"""The quantitative statements of the paper's text, each recomputed twice: from the paper's own tables
(the arithmetic check: does our formula give the printed number?) and from our run (ours, which sets the
verdict).

Usage: claims.py PUBLISHED.json PUBLISHED_COMBINATIONS.json.gz ANALYSIS.json FIGURES.json COMBINATIONS.npz OUT.json

Every field: name, expected (as printed), observed (ours), arithmetic (from the paper's tables, or null
when no table of the paper holds the inputs).
"""
import gzip
import json
import math
import statistics
import sys

import numpy as np

from compare import mc_spread, ptol
from data import META, PRED, SINGLE

STATS = ["accuracy", "sensitivity", "specificity", "ppv", "npv", "composite"]
CLUSTER1 = ["CHASM (breast)", "CHASM (lung)", "CHASM (melanoma)", "FATHMM (cancer)", "FATHMM (missense)",
            "CanDrA (lung)", "CanDrA (melanoma)", "Condel"]
CLUSTER2 = ["Mutation Assessor", "MutationTaster", "PolyPhen-2", "PROVEAN", "SIFT", "VEST"]
ONC = ["BRAF", "EGFR", "ERBB2", "KIT", "KRAS", "PIK3CA"]
NEW = ["DICER1", "ESR1", "IDH1", "IDH2", "MYOD1", "SF3B1"]
TSG = ["BRCA1", "BRCA2", "TP53"]
BEST = "At least 1 of CHASM (breast), MutationTaster"


def num(s):
    s = str(s).replace(",", "").strip().rstrip("%")
    return math.nan if s in ("NA", "") else float(s)


def f2(v, d):
    return None if v is None else f"{v:.{d}f}"


def F(name, expected, observed, arithmetic=None):
    return {"name": name, "expected": expected, "observed": observed, "arithmetic": arithmetic}


def pairs(names_a, names_b=None):
    if names_b is None:
        return [(a, b) for i, a in enumerate(names_a) for b in names_a[i + 1:]]
    return [(a, b) for a in names_a for b in names_b]


def kstats(K, prs, value=lambda v: v):
    vals = [value(K[a][b][0]) for a, b in prs]
    return statistics.median(vals), min(vals), max(vals)


def sig_better(ci_a, ci_b):
    """CI rule: A is significantly higher than B when A's low end reaches B's high end."""
    return ci_a[0] >= ci_b[1]


def main():
    pub_p, comb_p, ours_p, figs_p, npz_p, out = sys.argv[1:7]
    arr = dict(np.load(npz_p))
    pub = json.load(open(pub_p))
    with gzip.open(comb_p, "rt", encoding="utf-8") as fh:
        comb = json.load(fh)
    ours = json.load(open(ours_p))
    claims = {}

    # Dataset (Results, 'Categorization of mutations'; Table 1).
    t1p = {g: [num(x) for x in v] for g, v in pub["table1"].items()}
    t1o = ours["table1"]
    lab = lambda t, g: t[g][1] + t[g][2]
    med = lambda t, gs: statistics.median(lab(t, g) for g in gs)
    rng = lambda t, gs: (min(lab(t, g) for g in gs), max(lab(t, g) for g in gs))
    claims["text.dataset"] = {"label": "Dataset: mutations, SNVs and labelled SNVs per gene class", "fields": [
        F("mutations", "3706", ours["counts"]["mutations"]),
        F("SNVs", "3591", ours["counts"]["snvs"], int(t1p["Total"][0])),
        F("non-neutral", "849", t1o["Total"][2], int(t1p["Total"][2])),
        F("neutral", "140", t1o["Total"][1], int(t1p["Total"][1])),
        F("uncertain", "2602", t1o["Total"][3], int(t1p["Total"][3])),
        F("oncogenes, median labelled SNVs", "28.5", med(t1o, ONC), med(t1p, ONC)),
        F("oncogenes, fewest", "23", rng(t1o, ONC)[0], rng(t1p, ONC)[0]),
        F("oncogenes, most", "38", rng(t1o, ONC)[1], rng(t1p, ONC)[1]),
        F("new cancer genes, median", "5", med(t1o, NEW), med(t1p, NEW)),
        F("new cancer genes, fewest", "1", rng(t1o, NEW)[0], rng(t1p, NEW)[0]),
        F("new cancer genes, most", "11", rng(t1o, NEW)[1], rng(t1p, NEW)[1]),
        F("TSGs, median", "81", med(t1o, TSG), med(t1p, TSG)),
        F("TSGs, fewest", "62", rng(t1o, TSG)[0], rng(t1p, TSG)[0]),
        F("TSGs, most", "640", rng(t1o, TSG)[1], rng(t1p, TSG)[1]),
    ]}

    t2p, t2o = pub["table2"], ours["table2"]
    claims["text.table2"] = {"label": "Calls of VEST and PROVEAN (Results, 'Agreement')", "fields": [
        F("VEST functional", "2465", t2o["VEST"]["Functional"][3], int(num(t2p["VEST"]["Functional"][3]))),
        F("VEST neutral", "1126", t2o["VEST"]["Neutral"][3], int(num(t2p["VEST"]["Neutral"][3]))),
        F("PROVEAN deleterious", "1630", t2o["PROVEAN"]["Deleterious"][3], int(num(t2p["PROVEAN"]["Deleterious"][3]))),
        F("PROVEAN neutral", "1961", t2o["PROVEAN"]["Neutral"][3], int(num(t2p["PROVEAN"]["Neutral"][3]))),
    ]}

    # Kappa (Fig. 1B, Additional file 3).
    for key, pubk, oursk, label in (("all", pub["af3"]["first"], ours["kappa"]["all"], "all 3,591 SNVs"),
                                    ("non_cosmic", pub["af3"]["second"], ours["kappa"]["non_cosmic"], "1,699 non-COSMIC SNVs")):
        P = {a: {b: [num(x) for x in v] for b, v in r.items()} for a, r in pubk.items()}
        c1p, c1o = kstats(P, pairs(CLUSTER1)), kstats(oursk, pairs(CLUSTER1))
        c2p, c2o = kstats(P, pairs(CLUSTER2)), kstats(oursk, pairs(CLUSTER2))
        bp, bo = kstats(P, pairs(CLUSTER1, CLUSTER2)), kstats(oursk, pairs(CLUSTER1, CLUSTER2))
        fields = [F("Cluster 1 median kappa", {"all": "0.5679", "non_cosmic": "0.4558"}[key], c1o[0], c1p[0])]
        if key == "all":
            fields += [F("Cluster 1 lowest", "0.3861", c1o[1], c1p[1]), F("Cluster 1 highest", "0.9004", c1o[2], c1p[2]),
                       F("CHASM (breast) / CHASM (lung)", "0.9004", oursk["CHASM (breast)"]["CHASM (lung)"][0], P["CHASM (breast)"]["CHASM (lung)"][0]),
                       F("Cluster 2 median", "0.4347", c2o[0], c2p[0]), F("Cluster 2 lowest", "0.3355", c2o[1], c2p[1]),
                       F("Cluster 2 highest", "0.5662", c2o[2], c2p[2]),
                       F("between clusters, median", "0.2062", bo[0], bp[0]), F("between clusters, lowest", "-0.0520", bo[1], bp[1]),
                       F("between clusters, highest", "0.4216", bo[2], bp[2])]
        claims[f"text.kappa_{key}"] = {"label": f"Kappa medians and ranges within and between the clusters, {label}", "fields": fields}
    claims["text.non_cosmic"] = {"label": "SNVs not in COSMIC v68", "fields": [
        F("SNVs not in COSMIC", "1699", ours["counts"]["non_cosmic"]),
        F("share not in COSMIC (%)", "47.3", 100 * ours["counts"]["non_cosmic"] / ours["counts"]["snvs"]),
        F("labelled SNVs not in COSMIC", "297", ours["counts"]["labelled_non_cosmic"]),
        F("non-neutral not in COSMIC", "188", ours["counts"]["labelled_non_cosmic_by_label"]["non-neutral"]),
        F("neutral not in COSMIC", "109", ours["counts"]["labelled_non_cosmic_by_label"]["neutral"]),
    ]}

    # Clusters (Fig. 1A, 1C; Additional file 4).
    def clade_of(cl, members):
        """Is there a clade holding exactly these predictors?"""
        return "yes" if sorted(members) in [sorted(c) for c in cl["clades"]] else "no"
    ca, cc, cl = ours["clustering"]["all"], ours["clustering"]["non_cosmic"], ours["clustering"]["labelled"]
    claims["text.clusters"] = {"label": "Cluster structure (Fig. 1A, 1C, Additional file 4)", "fields": [
        F("all SNVs: Cluster 1 is a clade", "yes", clade_of(ca, CLUSTER1)),
        F("all SNVs: Cluster 2 is a clade", "yes", clade_of(ca, CLUSTER2)),
        F("all SNVs: CanDrA (breast) joins Cluster 1 only after its members", "yes", clade_of(ca, CLUSTER1 + ["CanDrA (breast)"])),
        F("non-COSMIC: VEST and CanDrA (breast) apart from both clusters", "yes",
          "yes" if clade_of(cc, CLUSTER1 + CLUSTER2[:-1]) == "yes" and clade_of(cc, ["VEST", "CanDrA (breast)"]) == "yes" else "no"),
        F("989 SNVs: CanDrA (breast) in Cluster 1", "yes",
          "yes" if any("CanDrA (breast)" in c and set(CLUSTER1) <= set(c) and not set(CLUSTER2) & set(c) for c in cl["clades"]) else "no"),
    ]}

    # Low confidence (Additional files 8 and 9).
    lc = ours["low_confidence"]["all"]["per_predictor"]
    pub8 = {p: sum(int(v[3]) for c, v in r.items() if "Low confidence" in c) for p, r in pub["af8"]["all"].items()}
    vals_o, vals_p = list(lc.values()), list(pub8.values())
    pre = ["CanDrA (breast)", "CanDrA (lung)", "CanDrA (melanoma)", "PolyPhen-2", "Mutation Assessor"]
    hist = ours["low_confidence"]["all"]["by_count"]
    h9 = [int(v[0]) for v in pub["af9"]["by_count"].values()]
    claims["text.low_confidence"] = {"label": "Low-confidence calls (Additional files 8 and 9)", "fields": [
        F("median low-confidence SNVs per predictor", "437", statistics.median(vals_o), statistics.median(vals_p)),
        F("fewest (CanDrA (breast))", "44", min(vals_o), min(vals_p)),
        F("most (PROVEAN)", "1298", max(vals_o), max(vals_p)),
        F("most among predictors with a built-in category (Mutation Assessor)", "1099", max(lc[p] for p in pre), max(pub8[p] for p in pre)),
        F("SNVs with 8 or more low-confidence calls", "27", sum(hist[8:]), sum(h9[8:])),
        F("labelled SNVs of low confidence by PROVEAN only", "132", ours["low_confidence_only"]["PROVEAN"]),
        F("as a share of 989 (%)", "13.3", 100 * ours["low_confidence_only"]["PROVEAN"] / 989),
    ]}

    # Tables 3 and 4: summaries and significance calls.
    def tab(t):
        return {p: {k: [num(x) for x in v] for k, v in r.items()} for p, r in t.items()}

    def ours_tab(t):
        return {p: {k: [100 * r[k]["value"] if k != "composite" else r[k]["value"],
                        100 * r[k]["low"] if k != "composite" else r[k]["low"],
                        100 * r[k]["high"] if k != "composite" else r[k]["high"]] for k in STATS} for p, r in t.items()}

    def rep_tab(t, r):
        """Our table with the intervals of bootstrap repeat r (same point values)."""
        sc = lambda k, v: v if k == "composite" else 100 * v
        return {p: {k: [sc(k, row[k]["value"]), sc(k, row[k]["repeats"][r][0]), sc(k, row[k]["repeats"][r][1])]
                    for k in STATS} for p, row in t.items() if p in PRED}

    def repeats(expected, fn, tables):
        """How many of our bootstrap repeats give the printed answer: evidence for a call near the edge."""
        n = len(tables[0][PRED[0]]["accuracy"]["repeats"])
        hit = sum(str(fn(*[rep_tab(t, r) for t in tables])) == str(expected) for r in range(n))
        return f"{hit} of {n}"

    T3p, T3o, T4p, T4o = tab(pub["table3"]), ours_tab(ours["table3"]), tab(pub["table4"]), ours_tab(ours["table4"])

    def summ(T, k):
        v = [T[p][k][0] for p in PRED]
        return statistics.median(v), min(v), max(v)

    d = {"accuracy": 2, "sensitivity": 2, "specificity": 2, "ppv": 2, "npv": 2, "composite": 4}
    printed3 = {"accuracy": ("85.84", "73.71", "91.28"), "sensitivity": ("90.73", "74.44", "97.88"),
                "specificity": ("62.86", "0.00", "80.95"), "ppv": ("92.59", "85.19", "96.97"),
                "npv": ("50.00", "0.00", "79.31"), "composite": ("2.7866", "1.8056", "3.3413")}
    fields = []
    for k, (m, lo, hi) in printed3.items():
        o, a = summ(T3o, k), summ(T3p, k)
        for part, e, oi, ai in (("median", m, o[0], a[0]), ("lowest", lo, o[1], a[1]), ("highest", hi, o[2], a[2])):
            fields.append(F(f"{k} {part}", e, oi, ai))
    yn = lambda b: "yes" if b else "no"
    for name, e, test in (
        ("FATHMM (cancer) most accurate single predictor", "yes", lambda T: max(SINGLE, key=lambda p: T[p]["accuracy"][0]) == "FATHMM (cancer)"),
        ("PROVEAN least accurate", "yes", lambda T: min(PRED, key=lambda p: T[p]["accuracy"][0]) == "PROVEAN"),
        ("CanDrA (lung) not significantly more accurate than FATHMM (cancer)", "yes", lambda T: not sig_better(T["CanDrA (lung)"]["accuracy"][1:], T["FATHMM (cancer)"]["accuracy"][1:]) and not sig_better(T["FATHMM (cancer)"]["accuracy"][1:], T["CanDrA (lung)"]["accuracy"][1:])),
        ("FATHMM (cancer) significantly more sensitive than CanDrA (breast)", "yes", lambda T: sig_better(T["FATHMM (cancer)"]["sensitivity"][1:], T["CanDrA (breast)"]["sensitivity"][1:])),
        ("CHASM (breast) most specific single predictor", "yes", lambda T: max(SINGLE, key=lambda p: T[p]["specificity"][0]) == "CHASM (breast)"),
        ("CHASM (breast) and CanDrA (lung) specificity not significantly different", "yes", lambda T: not sig_better(T["CanDrA (lung)"]["specificity"][1:], T["CHASM (breast)"]["specificity"][1:]) and not sig_better(T["CHASM (breast)"]["specificity"][1:], T["CanDrA (lung)"]["specificity"][1:])),
        ("FATHMM (cancer) NPV significantly above every single predictor but CHASM (melanoma)", "yes", lambda T: all(sig_better(T["FATHMM (cancer)"]["npv"][1:], T[p]["npv"][1:]) for p in SINGLE if p not in ("FATHMM (cancer)", "CHASM (melanoma)")) and not sig_better(T["FATHMM (cancer)"]["npv"][1:], T["CHASM (melanoma)"]["npv"][1:])),
        ("FATHMM (cancer) and CanDrA (lung) NPV not significantly different", "yes", lambda T: not sig_better(T["FATHMM (cancer)"]["npv"][1:], T["CanDrA (lung)"]["npv"][1:]) and not sig_better(T["CanDrA (lung)"]["npv"][1:], T["FATHMM (cancer)"]["npv"][1:])),
        ("CHASM (lung) best single composite; not significantly below CanDrA (lung)", "yes", lambda T: max(SINGLE, key=lambda p: T[p]["composite"][0]) == "CHASM (lung)" and not sig_better(T["CanDrA (lung)"]["composite"][1:], T["CHASM (lung)"]["composite"][1:])),
    ):
        fields.append(dict(F(name, e, yn(test(T3o)), yn(test(T3p))),
                           repeats=repeats(e, lambda T: yn(test(T)), [ours["table3"]])))
    claims["text.table3"] = {"label": "Performance on the 989 labelled SNVs: medians, ranges and significance calls (Table 3)", "fields": fields}

    printed4 = {"accuracy": ("76.77", "54.88", "84.70"), "sensitivity": ("79.26", "51.06", "97.85")}
    fields = []
    for k, (m, lo, hi) in printed4.items():
        o, a = summ(T4o, k), summ(T4p, k)
        for part, e, oi, ai in (("median", m, o[0], a[0]), ("lowest", lo, o[1], a[1]), ("highest", hi, o[2], a[2])):
            fields.append(F(f"{k} {part}", e, oi, ai))

    def reduced(Ta, Tb, k):
        """Predictors whose statistic is significantly lower without COSMIC SNVs (CI rule)."""
        return [p for p in PRED if sig_better(Ta[p][k][1:], Tb[p][k][1:])]
    fields += [
        F("most accurate single predictor (MutationTaster)", "MutationTaster", max(SINGLE, key=lambda p: T4o[p]["accuracy"][0]), max(SINGLE, key=lambda p: T4p[p]["accuracy"][0])),
        F("most accurate meta-predictor (CanDrA (lung))", "CanDrA (lung)", max(META, key=lambda p: T4o[p]["accuracy"][0]), max(META, key=lambda p: T4p[p]["accuracy"][0])),
        dict(F("predictors whose accuracy is significantly lower without COSMIC", "13", len(reduced(T3o, T4o, "accuracy")), len(reduced(T3p, T4p, "accuracy"))),
             repeats=repeats(13, lambda a, b: len(reduced(a, b, "accuracy")), [ours["table3"], ours["table4"]])),
        dict(F("the two whose accuracy is not", "Mutation Assessor, MutationTaster", ", ".join(p for p in PRED if p not in reduced(T3o, T4o, "accuracy")), ", ".join(p for p in PRED if p not in reduced(T3p, T4p, "accuracy"))),
             repeats=repeats("Mutation Assessor, MutationTaster", lambda a, b: ", ".join(p for p in PRED if p not in reduced(a, b, "accuracy")), [ours["table3"], ours["table4"]])),
        dict(F("significantly lower sensitivity", "8", len(reduced(T3o, T4o, "sensitivity")), len(reduced(T3p, T4p, "sensitivity"))),
             repeats=repeats(8, lambda a, b: len(reduced(a, b, "sensitivity")), [ours["table3"], ours["table4"]])),
        dict(F("significantly lower PPV", "10", len(reduced(T3o, T4o, "ppv")), len(reduced(T3p, T4p, "ppv"))),
             repeats=repeats(10, lambda a, b: len(reduced(a, b, "ppv")), [ours["table3"], ours["table4"]])),
    ]
    claims["text.table4"] = {"label": "Performance on the 297 non-COSMIC SNVs and the change from Table 3 (Table 4)", "fields": fields}

    # Gene classes (Additional files 14-16).
    gc = ours["gene_classes"]
    G = {c: {p: {k: [num(x) for x in v] for k, v in r.items()} for p, r in pub["af16"][c].items()} for c in ("oncogenes", "tsg")}
    Go = {c: ours_tab(gc[c]) for c in ("oncogenes", "tsg")}
    better_tsg = lambda X: sorted(p for p in PRED if sig_better(X["tsg"][p]["accuracy"][1:], X["oncogenes"][p]["accuracy"][1:]))
    better_onc = lambda X: sorted(p for p in PRED if sig_better(X["oncogenes"][p]["accuracy"][1:], X["tsg"][p]["accuracy"][1:]))
    claims["text.gene_classes"] = {"label": "Oncogenes against tumour suppressor genes (Additional files 14-16)", "fields": [
        F("SNVs in oncogenes", "176", gc["n"]["oncogenes"]), F("SNVs in TSGs", "783", gc["n"]["tsg"]), F("SNVs in new cancer genes", "30", gc["n"]["new"]),
        F("oncogenes: most accurate single predictor", "FATHMM (cancer)", max(SINGLE, key=lambda p: Go["oncogenes"][p]["accuracy"][0]), max(SINGLE, key=lambda p: G["oncogenes"][p]["accuracy"][0])),
        F("oncogenes: its accuracy", "96.59", Go["oncogenes"]["FATHMM (cancer)"]["accuracy"][0], G["oncogenes"]["FATHMM (cancer)"]["accuracy"][0]),
        F("oncogenes: most accurate meta-predictor", "CanDrA (lung)", max(META, key=lambda p: Go["oncogenes"][p]["accuracy"][0]), max(META, key=lambda p: G["oncogenes"][p]["accuracy"][0])),
        F("oncogenes: its accuracy", "95.00", Go["oncogenes"]["CanDrA (lung)"]["accuracy"][0], G["oncogenes"]["CanDrA (lung)"]["accuracy"][0]),
        F("TSGs: most accurate single predictor", "CHASM (lung)", max(SINGLE, key=lambda p: (Go["tsg"][p]["accuracy"][0], p == "CHASM (lung)")), max(SINGLE, key=lambda p: (G["tsg"][p]["accuracy"][0], p == "CHASM (lung)"))),
        F("TSGs: its accuracy", "92.98", Go["tsg"]["CHASM (lung)"]["accuracy"][0], G["tsg"]["CHASM (lung)"]["accuracy"][0]),
        F("TSGs: most accurate meta-predictor", "CanDrA (melanoma)", max(META, key=lambda p: Go["tsg"][p]["accuracy"][0]), max(META, key=lambda p: G["tsg"][p]["accuracy"][0])),
        F("TSGs: its accuracy", "93.46", Go["tsg"]["CanDrA (melanoma)"]["accuracy"][0], G["tsg"]["CanDrA (melanoma)"]["accuracy"][0]),
        F("significantly more accurate in TSGs", ", ".join(sorted(["CHASM (breast)", "CHASM (melanoma)", "FATHMM (missense)", "Mutation Assessor", "CanDrA (melanoma)", "Condel"])),
          ", ".join(better_tsg(Go)), ", ".join(better_tsg(G))),
        F("significantly more accurate in oncogenes", ", ".join(sorted(["FATHMM (cancer)", "MutationTaster", "PolyPhen-2", "PROVEAN", "VEST"])),
          ", ".join(better_onc(Go)), ", ".join(better_onc(G))),
        F("Fisher's exact test of the neutral share below 0.0001", "yes", yn(gc["fisher_p"] < 1e-4)),
    ]}

    # Combinations (Results, 'Combination of mutation effect prediction algorithms'; Additional files 17-22).
    c_all, c_nc = ours["combinations"]["all"]["run1"], ours["combinations"]["non_cosmic"]["run1"]
    nb = c_all["named"][BEST]
    a19 = pub["af19"]["single"]
    best_p = comb["af17"][BEST]
    fields = [
        F("combinations", "11253", c_all["n_combinations"], len(comb["af17"])),
        F("higher mean accuracy than FATHMM (cancer) in both subsets", "1854", c_all["counts"]["single"]["accuracy"]["mean"][2], int(a19["accuracy"]["mean"][2])),
        F("of these, significantly higher in both", "6", c_all["counts"]["single"]["accuracy"]["significant"][2], int(a19["accuracy"]["significant"][2])),
        F("higher mean composite than CHASM (lung) in both subsets", "1483", c_all["counts"]["single"]["composite"]["mean"][2], int(a19["composite"]["mean"][2])),
        F("of these, significantly higher in both", "5", c_all["counts"]["single"]["composite"]["significant"][2], int(a19["composite"]["significant"][2])),
        F("first by accuracy and composite in both subsets", BEST, BEST if all(v == 1 for v in nb["rank"].values()) else "no",
          BEST if all(pub["af21"][f"{s}/{b}"]["top5"][0]["name"] == BEST for s in ("subset1", "subset2") for b in ("accuracy", "composite")) else "no"),
    ]
    spread = mc_spread(arr, "all")
    for sub, vals in (("subset1", ("95.46", "94.54", "96.51", "3.6255", "3.5584", "3.6982")),
                      ("subset2", ("95.43", "93.33", "97.27", "3.6236", "3.4841", "3.7573"))):
        o = nb[sub]
        for j, (k, part) in enumerate([("accuracy", 0), ("accuracy", 1), ("accuracy", 2), ("composite", 0), ("composite", 1), ("composite", 2)]):
            ov = o[k][part] * (100 if k == "accuracy" else 1)
            av = num(best_p[sub][k][part])
            pname = ["mean", "low", "high"][part]
            tol = ptol(vals[j]) + 3 * spread[(sub, k, pname)] * (100 if k == "accuracy" else 1)
            fields.append(dict(F(f"{BEST}, {sub}, {k} {pname}", vals[j], ov, av), tolerance={"abs": round(tol, 6)}))
    # Non-COSMIC: only this combination beats MutationTaster (the best single predictor by accuracy) in both subsets.
    T4mt = T4o["MutationTaster"]["accuracy"]
    fields.append(F("non-COSMIC: combinations significantly more accurate than MutationTaster in both subsets", "1",
                    c_nc["counts"]["single"]["accuracy"]["significant"][2], int(pub["af19"]["single"]["accuracy"]["significant"][5])))
    claims["text.combinations"] = {"label": "Combinations against the best single predictor (Additional files 17-21)", "fields": fields}

    # NPV of the best combination against the best single and meta-predictor (NPV), all subsets.
    fields = []
    for key, T, Tp, af in (("all", T3o, T3p, "af17"), ("non_cosmic", T4o, T4p, "af18")):
        bs = max(SINGLE, key=lambda p: T[p]["npv"][0])
        bm = max(META, key=lambda p: T[p]["npv"][0])
        bsp = max(SINGLE, key=lambda p: Tp[p]["npv"][0])
        bmp = max(META, key=lambda p: Tp[p]["npv"][0])
        nbk = ours["combinations"][key]["run1"]["named"][BEST]
        for sub in ("subset1", "subset2"):
            lo = 100 * nbk[sub]["npv"][1]
            lop = num(comb[af][BEST][sub]["npv"][1])
            fields.append(F(f"{key}, {sub}: NPV significantly above the best single and meta-predictor", "yes",
                            yn(lo >= T[bs]["npv"][2] and lo >= T[bm]["npv"][2]), yn(lop >= Tp[bsp]["npv"][2] and lop >= Tp[bmp]["npv"][2])))
    claims["text.npv"] = {"label": "The best combination improves NPV significantly in every subset", "fields": fields}

    # Recurrence (Fig. 4): MutationTaster, CHASM (breast) and CHASM (lung) are the three most frequent.
    fig4 = json.load(open(figs_p))["fig4"]
    fields = []
    for key, panel in (("all", "a"), ("non_cosmic", "b")):
        rec = ours["combinations"][key]["run1"]["recurrence"]
        for sub in ("subset1", "subset2"):
            for j, t in enumerate(("10", "20", "50", "100")):
                top3 = lambda r: sorted(SINGLE, key=lambda p: -r[p])[:3]
                o = rec[f"{sub}/composite"][t]
                a = {p: fig4[panel][sub]["series"][p][j] for p in SINGLE}
                trio = {"MutationTaster", "CHASM (breast)", "CHASM (lung)"}
                okf = lambda r: yn(all(r[p] >= max(r[q] for q in SINGLE if q not in trio) for p in trio))
                fields.append(F(f"{key}, {sub}, top {t}: MutationTaster, CHASM (breast) and CHASM (lung) at least as frequent as any other", "yes", okf(o), okf(a)))
    claims["text.recurrence"] = {"label": "MutationTaster and the CHASM breast and lung classifiers dominate the top combinations (Fig. 4)", "fields": fields}

    # Training sets (Discussion, Additional file 29): removing COSMIC or the training-set SNVs never makes a
    # predictor significantly more accurate.
    figs = json.load(open(figs_p))
    fields = []
    TRAIN = ["CHASM (breast)", "CHASM (lung)", "CHASM (melanoma)", "FATHMM (cancer)", "FATHMM (missense)", "PolyPhen-2"]
    for p in TRAIN:
        a = ours["table3"][p]["accuracy"]
        oset = {"non-COSMIC": ours["table4"][p]["accuracy"], "without the training set": ours["training_excluded"][p]["accuracy"]}
        pf = figs["af29"][p]["bars"]
        pset = {"non-COSMIC": pf["non_cosmic"]["accuracy"], "without the training set": pf["excluding_training"]["accuracy"]}
        for name in oset:
            o = oset[name]
            q = pset[name]
            fields.append(F(f"{p}, {name}: accuracy not significantly above all SNVs", "yes",
                            yn(not sig_better((o["low"], o["high"]), (a["low"], a["high"]))),
                            yn(not sig_better((q["low"], q["high"]), (pf["all"]["accuracy"]["low"], pf["all"]["accuracy"]["high"])))))
    claims["text.training"] = {"label": "Removing COSMIC or training-set SNVs never raises accuracy significantly (Discussion, Additional file 29)", "fields": fields}

    # Optimal n and p (Additional file 25): the printed relations.
    o = ours["combinations"]["all"]["run1"]["optimal"]
    a25 = pub["af25"]
    rel_n = lambda rows: yn(all(abs(int(r["n"]) - 2 * int(r["p"])) <= 1 for r in rows if 1 <= int(r["n"]) <= 4))
    rel_n_paper = lambda rows: yn(all(abs(int(r["p"]) - 2 * int(r["n"])) <= 1 for r in rows if 1 <= int(r["n"]) <= 4))
    rel_p = lambda rows: yn(all(abs(int(r["n"]) - int(r["p"]) / 2) <= 1 for r in rows if 3 <= int(r["p"]) <= 11))
    claims["text.optimal"] = {"label": "Optimal p and n (Additional file 25)", "fields": [
        F("for n = 1 to 4, the best p is about 2n", "yes", rel_n_paper(o["by_n"]), rel_n_paper(a25["by_n"])),
        F("for p = 3 to 11, the best n is about p/2", "yes", rel_p(o["by_p"]), rel_p(a25["by_p"])),
    ]}
    with open(out, "w") as fh:
        json.dump(claims, fh, indent=1, default=lambda v: v.item() if hasattr(v, "item") else str(v))
        fh.write("\n")


if __name__ == "__main__":
    main()

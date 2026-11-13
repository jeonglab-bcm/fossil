"""Put the paper's numbers next to ours for every item: comparison.json.

Usage: compare.py RUN_DIR OUT.json

RUN_DIR holds: datasets.json, fig2.json, digitized.json (Figs 2 and 3 read off the raster figures),
published_vector.json (Figs S1, S2, S3, S5 read from the vector PDFs), cv_summary.json,
robustness.json, and from markers.py: corgs/<dataset>.json, figure4.json, c2_counts.json and
symbol_map.json.
Each item gets "fields" (name, expected, observed) in the form check_results.py reads; the
expected values of printed numbers are strings so their printed precision is kept.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from common import LABELS

WITHIN_ORDER = ["nfkb", "leukemia", "prostate", "breast_netherlands", "breast_usa", "lung_michigan", "lung_boston"]
CROSS_ORDER = [("breast_netherlands", "breast_usa"), ("breast_usa", "breast_netherlands"),
               ("lung_michigan", "lung_boston"), ("lung_boston", "lung_michigan")]


def cross_label(s, t):
    return f"{LABELS[s]} -> {LABELS[t]}"


def r4(x):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), 4)


# Table S1 (class sizes), as printed.
TABLE_S1 = {
    "nfkb": ("Wildtype", "12", "Mutant", "12"),
    "prostate": ("Normal", "41", "Cancer", "62"),
    "leukemia": ("TEL-AML1", "79", "HH", "64"),
    "breast_netherlands": ("Metastatic", "78", "Non-metastatic", "217"),
    "breast_usa": ("Metastatic", "106", "Non-metastatic", "180"),
    "lung_boston": ("Poor", "31", "Good", "31"),
    "lung_michigan": ("Poor", "24", "Good", "62"),
}
CASE = {"nfkb": "Mutant", "prostate": "Cancer", "leukemia": "TEL-AML1", "breast_netherlands": "Metastatic",
        "breast_usa": "Metastatic", "lung_boston": "Poor", "lung_michigan": "Poor"}

# Table 1 and Table S2 rows: (pathway as printed, C2 set, frequency, "#CORGs/#members", CORGs)
TABLE1 = {
    ("lung_michigan", "lung_boston"): [
        ("Glutamine up-regulated genes", "GLUT_DOWN", "433/500", "5/313", "NP LDHA BZW1 TUBA1 LAMB3"),
        ("Gluconeogenesis", "GLUCO", "247/500", "2/32", "LDHA ENO2"),
        ("Glycolysis", "GLYCOL", "245/500", "3/22", "ENO2 PGK1 ALDOA"),
        ("Breast cancer estrogen signaling", "breast_cancer_estrogen_signalling", "203/500", "3/101", "VEGF KRT18 KRT19"),
        ("Glycolysis and gluconeogenesis", "MAP00010_Glycolysis_Gluconeogenesis", "176/500", "5/55", "GAPD LDHA ENO2 ALDH3B2 ALDH3B1"),
        ("Estrogen receptor modulators down-regulated genes", "FRASOR_ER_DOWN", "138/500", "4/74", "ARHE STC1 KRT7 COPEB"),
        ("Leucine down-regulated genes", "LEU_DOWN", "134.500", "4/180", "NP LDHA TUBA1 CCNA2"),
        ("B lymphocyte pathway", "blymphocytePathway", "102/500", "4/11", "CR2 ITGAL HLA-DRA CR1"),
    ],
    ("lung_boston", "lung_michigan"): [
        ("Breast cancer estrogen signaling", "breast_cancer_estrogen_signalling", "481/500", "6/101", "KRT18 KRT19 GAPD MT3 CDKN2A TFF1"),
        ("Pyrimidine metabolism", "MAP00240_Pyrimidine_metabolism", "258/500", "3/45", "POLR2E NP RRM1"),
        ("Glycolysis", "GLYCOL", "258/500", "2/22", "ENO2 PGK1"),
        ("MTA3 pathway", "mta3Pathway", "238/500", "3/16", "TUBA1 GAPD MTA1"),
        ("Insulin up-regulated genes", "INSULIN_2F_UP", "165/500", "10/235", "PGAM1 ARF4 ARCN1 DNCL1 EIF2S2 PSMA6 YWHAH PSMA3 ZNF9 CLNS1A"),
        ("P53 hypoxia pathway", "p53hypoxiaPathway", "148/500", "3/20", "FHL2 IGFBP3 HIF1A"),
        ("Glutamine down-regulated genes", "GLUT_DOWN", "133/500", "4/313", "PGAM1 ERH PAICS BZW1"),
        ("p53 signalling", "p53_signalling", "114/500", "6/101", "HIF1A FADD GAPD APEX1 CDKN2A CSNK2B"),
        ("Estrogen receptor modulators down-regulated genes", "FRASOR_ER_DOWN", "108/500", "3/74", "KRT7 DUSP4 MMD"),
        ("NFKB up-regulated genes", "NFKB_INDUCED", "103/500", "2/111", "KRT7 GBP1"),
    ],
}
TABLE_S2 = {
    ("breast_netherlands", "breast_usa"): [
        ("Cyclin regulated genes", "SA_REG_CASCADE_OF_CYCLIN_EXPR", "416/500", "2/13", "E2F1 CCNE2"),
        ("IL7 pathway", "il7Pathway", "200/500", "3/16", "BCL2 STAT5A IL7"),
        ("Cell cycle", "Cell_Cycle", "197/500", "3/84", "E2F1 ESPL1 CCNB2"),
        ("ActinY pathway", "actinYPathway", "142/500", "3/19", "PIR PSMA7 ACTR3"),
        ("GNF female genes", "GNF_FEMALE_GENES", "123/500", "3/85", "RPS4X RPS6 RPL6"),
    ],
    ("breast_usa", "breast_netherlands"): [
        ("Cell Cycle", "Cell_Cycle", "500/500", "4/84", "CCNE2 ESPL1 MAD2L1 CDK2"),
        ("Brentani cell cycle", "CR_CELL_CYCLE", "282/500", "4/86", "CCNE2 MAD2L1 CDK2 MXD1"),
        ("Cyclin regulated genes", "SA_REG_CASCADE_OF_CYCLIN_EXPR", "280/500", "3/13", "CCNE2 CDK2 CCNA2"),
        ("KRAS up-regulated genes", "KRAS_TOP100_KNOCKDOWN", "202/500", "3/84", "TUFT1 P4HA2 COL4A1"),
        ("Cell cycle checkpoint II genes", "cell_cycle_checkpointII", "200/500", "2/10", "CCNE2 FANCG"),
        ("Glutamine down-regulated genes", "GLUT_DOWN", "167/500", "6/313", "TCEB1 KPNA2 CYCS TMED9 UTP18 MORF4L2"),
        ("MMP/Cytokine connection", "SA_MMP_CYTOKINE_CONNECTION", "148/500", "5/15", "DEAF1 TNFRSF1B CD44 IL1B TGFB2"),
        ("Leucine down-regulated genes", "LEU_DOWN", "136/500", "6/180", "TCEB1 KPNA2 CYCS TDG CCT6A CSE1L"),
        ("IL22 pathway", "il22bpPathway", "124/500", "3/13", "SOCS3 STAT5A STAT3"),
        ("Rapamycin down-regulated genes", "RAP_DOWN", "111/500", "4/229", "STAU1 CYCS RAE1 MORF4L2"),
    ],
}
FIG3A_LABELS = {"nfkb": "12.6", "prostate": "1.9", "breast_netherlands": "16.9", "breast_usa": "3.6",
                "lung_michigan": "16.3", "lung_boston": "2.2"}
FIG3B_LABELS = {("breast_usa", "breast_netherlands"): "13.7", ("lung_michigan", "lung_boston"): "5.5",
                ("lung_boston", "lung_michigan"): "7.3"}
S2_PANELS = {"A": "knn3", "B": "knn5", "C": "nb", "D": "lda"}
S2_NAMES = {"A": "k-nearest neighbours, k = 3 (accuracy)", "B": "k-nearest neighbours, k = 5 (accuracy)",
            "C": "naive Bayes (AUC)", "D": "linear discriminant analysis (AUC)"}


def yn(b):
    return "yes" if b else "no"


def corg_key(symbols, mapping):
    """Paper's printed CORG symbols as row keys of the dataset (Entrez IDs, or symbols for lung)."""
    return [mapping.get(s, s) for s in symbols.split()]


def main(run: Path, out: Path):
    J = lambda name: json.loads((run / name).read_text())
    datasets, fig2, dig, vec = J("datasets.json"), J("fig2.json"), J("digitized.json"), J("published_vector.json")
    cv, rob, c2, fig4 = J("cv_summary.json"), J("robustness.json"), J("c2_counts.json"), J("figure4.json")
    symmap = J("symbol_map.json")  # paper symbol -> Entrez ID (breast) for the CORG comparison
    res = {}

    # ---- Table S1 and the Methods' counts
    fields = []
    for d, (c1, n1, c2_, n2) in TABLE_S1.items():
        r = datasets[d]
        obs = {CASE[d]: r["cases"]}
        other = [c for c in (c1, c2_) if c != CASE[d]][0]
        obs[other] = r["controls"]
        fields += [{"name": f"{LABELS[d]} {c1}", "expected": n1, "observed": obs[c1]},
                   {"name": f"{LABELS[d]} {c2_}", "expected": n2, "observed": obs[c2_]}]
    res["table_s1"] = {"fields": fields}
    res["text.methods_counts"] = {"fields": [
        {"name": "C2 gene sets", "expected": "522", "observed": c2["sets"]},
        {"name": "genes in C2", "expected": "5602", "observed": c2["genes"]},
        {"name": "top 10% of pathways", "expected": "52", "observed": c2["top10"]},
    ]}

    # ---- Fig. 2 (read off the figure)
    for panel, ours in fig2.items():
        pub = dig["fig2"][panel]["series"]
        fields = []
        for s in ("PAC", "Genes", "CORGs", "PAC_all"):
            for i, frac in enumerate(["1%", "2%", "3%", "5%", "10%"]):
                if pub[s][i] is None:
                    continue
                fields.append({"name": f"{s} top {frac}", "expected": pub[s][i], "observed": r4(ours["series"][s][i])})
        res[f"fig2.{panel.lower()}"] = {"fields": fields}

    # ---- Fig. 3A and 3B bars (read off the figure) and -log10(p) labels (printed)
    pub3 = dig["fig3"]["A"]["groups"]
    fields = []
    for d in WITHIN_ORDER:
        sc = cv["within"][d]["scores"]
        for m in ("Gene", "PAC", "PAC_random", "Mean", "Median", "PCA"):
            fields.append({"name": f"{LABELS[d]} {m}", "expected": pub3[LABELS[d]][m], "observed": r4(sc[f"{m}/lr"]["mean"])})
    res["fig3.a"] = {"fields": fields}
    pub3b = dig["fig3"]["B"]["groups"]
    fields = []
    for s, t in CROSS_ORDER:
        sc = cv["cross"][f"{s}__{t}"]["scores"]
        for m in ("Gene", "PAC"):
            fields.append({"name": f"{cross_label(s, t)} {m}", "expected": pub3b[cross_label(s, t)][m],
                           "observed": r4(sc[f"{m}/lr"]["mean"])})
    res["fig3.b"] = {"fields": fields}
    fields = []
    for d, v in FIG3A_LABELS.items():
        fields.append({"name": f"{LABELS[d]} -log10 p", "expected": v, "observed": r4(cv["within"][d]["tests"]["lr"]["neglog10p"])})
    for (s, t), v in FIG3B_LABELS.items():
        fields.append({"name": f"{cross_label(s, t)} -log10 p", "expected": v,
                       "observed": r4(cv["cross"][f"{s}__{t}"]["tests"]["lr"]["neglog10p"])})
    res["fig3.pvalues"] = {"fields": fields}

    # ---- Table 1 and Table S2: CORGs (deterministic), sizes, frequencies
    for tid, table in (("table1", TABLE1), ("table_s2", TABLE_S2)):
        corg_fields, size_fields, freq_fields = [], [], []
        for (s, t), rows in table.items():
            mk = J(f"corgs/{s}.json")
            freq = cv["cross"][f"{s}__{t}"]["pathway_frequency"]
            mp = symmap.get(s, {})
            for printed, c2name, f, size, corgs in rows:
                label = f"{cross_label(s, t).replace(' -> ', ' to ')}: {printed}"
                ours = mk["corgs"][c2name]
                ours_sym = mk["corg_symbols"][c2name]
                same = ours == corg_key(corgs, mp)
                corg_fields.append({"name": label, "expected": corgs,
                                    "observed": corgs if same else " ".join(ours_sym)})
                size_fields.append({"name": label, "expected": size,
                                    "observed": f"{len(ours)}/{c2['sizes'][c2name]}"})
                freq_fields.append({"name": label, "expected": f.split("/")[0].split(".")[0],
                                    "observed": int(freq.get(c2name, 0))})
        res[f"{tid}.corgs"] = {"fields": corg_fields}
        res[f"{tid}.sizes"] = {"fields": size_fields}
        res[f"{tid}.frequency"] = {"fields": freq_fields}

    # ---- Fig. 4: direction of the glycolysis and estrogen-signalling activities
    res["fig4"] = {"fields": [{"name": f"{p} up in Poor, {LABELS[d]}", "expected": "yes", "observed": yn(v > 0)}
                              for d, per in fig4["t"].items() for p, v in per.items()]}

    # ---- Fig. S1 (vector values)
    for d in WITHIN_ORDER:
        L = LABELS[d]
        pub = vec["figS1"][L]
        ours = rob["figS1"][L]
        fields = []
        for s in ("Pathways", "CORGs", "Genes"):
            for i, frac in enumerate(["1%", "2%", "3%", "5%", "10%", "20%"]):
                fields.append({"name": f"{s} top {frac}", "expected": pub[s][i], "observed": r4(ours[s][i])})
        res[f"fig_s1.{d}"] = {"fields": fields}

    # ---- Fig. S2 (vector values and labels)
    for panel, kind in S2_PANELS.items():
        pub = vec["figS2"][panel]
        fields, labels = [], []
        for d in WITHIN_ORDER:
            g = pub["within"][LABELS[d]]
            sc = cv["within"][d]["scores"]
            for m in ("Gene", "PAC", "Mean", "Median", "PCA"):
                fields.append({"name": f"{LABELS[d]} {m}", "expected": g["values"][m], "observed": r4(sc[f"{m}/{kind}"]["mean"])})
            if "neglogp" in g:
                labels.append({"name": f"{LABELS[d]} -log10 p", "expected": str(g["neglogp"]),
                               "observed": r4(cv["within"][d]["tests"].get(kind, {}).get("neglog10p"))})
        for s, t in CROSS_ORDER:
            g = pub["cross"][cross_label(s, t)]
            sc = cv["cross"][f"{s}__{t}"]["scores"]
            for m in ("Gene", "PAC"):
                fields.append({"name": f"{cross_label(s, t)} {m}", "expected": g["values"][m], "observed": r4(sc[f"{m}/{kind}"]["mean"])})
            if "neglogp" in g:
                labels.append({"name": f"{cross_label(s, t)} -log10 p", "expected": str(g["neglogp"]),
                               "observed": r4(cv["cross"][f"{s}__{t}"]["tests"].get(kind, {}).get("neglog10p"))})
        res[f"fig_s2.{panel.lower()}"] = {"fields": fields, "classifier": S2_NAMES[panel]}
        res[f"fig_s2.{panel.lower()}.pvalues"] = {"fields": labels}

    # ---- Fig. S3 (vector values)
    fields = []
    for d in WITHIN_ORDER:
        sc = cv["within"][d]["scores"]
        pub = vec["figS3"][LABELS[d]]
        for name, key in (("PAC_SEQ", "PAC/lr"), ("PAC_FWD", "PAC/fwd"), ("Gene_SEQ", "Gene/lr"), ("Gene_FWD", "Gene/fwd")):
            fields.append({"name": f"{LABELS[d]} {name}", "expected": pub[name], "observed": r4(sc[key]["mean"])})
    res["fig_s3"] = {"fields": fields}

    # ---- Fig. S5 (vector values; counts are integers)
    fields = []
    for d in WITHIN_ORDER:
        pub = vec["figS5"][LABELS[d]]
        ours = rob["figS5"][LABELS[d]]
        for k in ("q1", "median", "q3", "whisker_low", "whisker_high"):
            fields.append({"name": f"{LABELS[d]} {k.replace('_', ' ')}", "expected": f"{pub[k]:g}", "observed": ours[k]})
        fields.append({"name": f"{LABELS[d]} outliers", "expected": " ".join(f"{v:g}" for v in pub["outliers"]) or "none",
                       "observed": " ".join(f"{v:g}" for v in ours["outliers"]) or "none"})
    res["fig_s5"] = {"fields": fields}

    # ---- Claims in the text (ours)
    claims = {}
    src_panels = {"A": "breast_netherlands", "C": "breast_usa", "E": "lung_michigan", "G": "lung_boston"}
    ver_panels = {"B": "Breast Netherlands -> USA", "D": "Breast USA -> Netherlands",
                  "F": "Lung Michigan -> Boston", "H": "Lung Boston -> Michigan"}
    above = lambda a, b: all(x > y for x, y in zip(a, b))
    claims["text.pac_above_genes"] = [
        {"name": f"Fig. 2{p} ({'source' if p in src_panels else 'verification'})", "expected": "yes",
         "observed": yn(above(fig2[p]["series"]["PAC"], fig2[p]["series"]["Genes"]))} for p in "ABCDEFGH"]
    claims["text.pac_above_corgs_and_pac_all"] = (
        [{"name": f"Fig. 2{p}: PAC above CORGs", "expected": "yes",
          "observed": yn(above(fig2[p]["series"]["PAC"], fig2[p]["series"]["CORGs"]))} for p in src_panels]
        + [{"name": f"Fig. 2{p}: PAC_all below PAC", "expected": "yes",
            "observed": yn(above(fig2[p]["series"]["PAC"], fig2[p]["series"]["PAC_all"]))} for p in src_panels])
    claims["text.genes_above_corgs_in_source"] = [
        {"name": f"Fig. 2{p}: Genes above CORGs", "expected": "yes",
         "observed": yn(above(fig2[p]["series"]["Genes"], fig2[p]["series"]["CORGs"]))} for p in src_panels]

    def sig(test):
        return test["pac_better"] and test["p"] < 0.05

    claims["text.pac_beats_gene_within"] = [
        {"name": LABELS[d], "expected": "no" if d == "leukemia" else "yes",
         "observed": yn(sig(cv["within"][d]["tests"]["lr"]))} for d in WITHIN_ORDER]
    claims["text.pac_beats_gene_across"] = [
        {"name": cross_label(s, t), "expected": "no" if (s, t) == ("breast_netherlands", "breast_usa") else "yes",
         "observed": yn(sig(cv["cross"][f"{s}__{t}"]["tests"]["lr"]))} for s, t in CROSS_ORDER]
    claims["text.pac_above_random"] = [
        {"name": LABELS[d], "expected": "yes",
         "observed": yn(cv["within"][d]["scores"]["PAC/lr"]["mean"] > cv["within"][d]["scores"]["PAC_random/lr"]["mean"])}
        for d in WITHIN_ORDER]
    claims["text.summaries_above_random"] = [
        {"name": LABELS[d], "expected": "yes",
         "observed": yn(sum(cv["within"][d]["scores"][f"{m}/lr"]["mean"] for m in ("Mean", "Median", "PCA")) / 3
                        > cv["within"][d]["scores"]["PAC_random/lr"]["mean"])} for d in WITHIN_ORDER]
    claims["text.other_classifiers"] = []
    for kind, name in (("knn3", "kNN k = 3"), ("knn5", "kNN k = 5"), ("nb", "naive Bayes"), ("lda", "LDA"),
                       ("fwd", "forward selection")):
        wins = sum(cv["within"][d]["scores"][f"PAC/{kind}"]["mean"] > cv["within"][d]["scores"][f"Gene/{kind}"]["mean"]
                   for d in WITHIN_ORDER)
        claims["text.other_classifiers"].append({"name": f"{name}: PAC above Gene in most of the 7 datasets",
                                                 "expected": "yes", "observed": yn(wins >= 4)})
    sizes = rob["figS5_sizes"]
    claims["text.corg_sizes"] = [
        {"name": "median CORG set size between 2 and 4 in every dataset", "expected": "yes",
         "observed": yn(all(2 <= rob["figS5"][L]["median"] <= 4 for L in sizes))},
        {"name": "some pathways need more than eight CORGs", "expected": "yes",
         "observed": yn(any(max(v) > 8 for v in sizes.values()))},
    ]
    for k, v in claims.items():
        res[k] = {"fields": v}

    # ---- Arithmetic on the paper's own numbers (text.arithmetic)
    checks = []
    labels = [float(v) for v in FIG3A_LABELS.values()] + [float(v) for v in FIG3B_LABELS.values()]
    for p in vec["figS2"].values():
        for kind in ("within", "cross"):
            labels += [g["neglogp"] for g in p[kind].values() if "neglogp" in g]
    checks.append(("every printed -log(p) is at least -log10(0.05) = 1.30 (base 10; base e would need 3.00)",
                   min(labels) >= -math.log10(0.05) and min(labels) < -math.log(0.05)))
    pac_up = []
    for d in WITHIN_ORDER:
        if d in FIG3A_LABELS:
            g = pub3[LABELS[d]]
            pac_up.append(g["PAC"] > g["Gene"])
    for (s, t) in FIG3B_LABELS:
        g = pub3b[cross_label(s, t)]
        pac_up.append(g["PAC"] > g["Gene"])
    for p in vec["figS2"].values():
        for kind in ("within", "cross"):
            for g in p[kind].values():
                if "neglogp" in g:
                    pac_up.append(g["values"]["PAC"] > g["values"]["Gene"])
    checks.append((f"the PAC bar is above the Gene bar wherever a -log(p) is printed ({sum(pac_up)} of {len(pac_up)})", all(pac_up)))
    freqs = [int(r[2].split("/")[0].split(".")[0]) for tb in (TABLE1, TABLE_S2) for rows in tb.values() for r in rows]
    checks.append(("every Table 1 and Table S2 frequency is above 100 of 500", all(f > 100 for f in freqs)))
    checks.append(("10% of 522 pathways is 52", round(0.1 * 522) == 52))
    s5_ok = all(vec["figS5"][LABELS[d]]["q1"] <= vec["figS5"][LABELS[d]]["median"] <= vec["figS5"][LABELS[d]]["q3"] for d in WITHIN_ORDER)
    checks.append(("Fig. S5 medians lie between 2 and 4 (the text's 'two to four') and the largest set has more than eight",
                   all(2 <= vec["figS5"][LABELS[d]]["median"] <= 4 for d in WITHIN_ORDER)
                   and max(o for d in WITHIN_ORDER for o in vec["figS5"][LABELS[d]]["outliers"] + [vec["figS5"][LABELS[d]]["whisker_high"]]) > 8 and s5_ok))
    fig2_src = all(above(dig["fig2"][p]["series"]["PAC"], dig["fig2"][p]["series"]["Genes"]) for p in "ACEG"
                   if None not in dig["fig2"][p]["series"]["PAC"] + dig["fig2"][p]["series"]["Genes"])
    checks.append(("published Fig. 2: PAC above Genes in the source panels", fig2_src))
    res["text.arithmetic"] = {"checks": [{"claim": c, "holds": bool(h)} for c, h in checks],
                              "passed": all(h for _, h in checks)}
    # dot-free keys for the repository's results check (tools/check_results.py paths split on dots)
    res["item_list"] = [{"key": k.replace(".", "").replace("_", ""), "id": k, "fields": v["fields"]}
                        for k, v in res.items() if "fields" in v]
    out.write_text(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    r = main(Path(sys.argv[1]), Path(sys.argv[2]))
    for k, v in r.items():
        if "fields" in v:
            print(k, len(v["fields"]))
    print(json.dumps(r["text.arithmetic"], indent=1))

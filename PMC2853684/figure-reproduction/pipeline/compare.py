"""Compare our numbers with the paper's: the printed text and the values drawn in its figures.

    compare.py analysis.json published_values.json comparison.json

Writes, for each results.json item, its `values` fields (expected as printed, observed from our
run) or its `check`. Labels, sources, assumptions and causes are kept by hand in
results_notes.json; build_results.py merges the two.

Figure points drawn by the paper are read from the vector PDFs (read_published.py) and rounded
to the 0.1% the authors plotted (every Fig. 2 and Fig. S1 coordinate sits on a 0.1% grid to
within 0.001%). Bar heights of Figs 4 and S2 are given to three decimals.
"""

from __future__ import annotations

import json
import math
import sys


def s1(x):
    return None if x is None else f"{x:.1f}"


def pct1(x):
    return f"{x:.1f}"


def field(name, expected, observed, **kw):
    f = {"name": name, "expected": expected, "observed": observed}
    f.update(kw)
    return f


def align(pub, ours):
    """Match published points to ours in drawing order (longest common subsequence on equal
    points). Returns, for each published point, our matching point or None, and our points the
    paper does not draw."""
    n, m = len(pub), len(ours)
    L = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            L[i][j] = L[i + 1][j + 1] + 1 if pub[i] == ours[j] else max(L[i + 1][j], L[i][j + 1])
    i = j = 0
    match = [None] * n
    used = set()
    while i < n and j < m:
        if pub[i] == ours[j]:
            match[i] = ours[j]
            used.add(j)
            i += 1
            j += 1
        elif L[i + 1][j] >= L[i][j + 1]:
            i += 1
        else:
            j += 1
    extra = [ours[k] for k in range(m) if k not in used]
    return match, extra


def round_pts(pts):
    return [[round(r + 1e-9, 1), round(p + 1e-9, 1)] for r, p in pts]


def curve_fields(pub_fig, our_fig, methods):
    fields = []
    extras = {}
    for m in methods:
        pub = round_pts(pub_fig.get(m, []))
        ours = our_fig.get(m, [])
        match, extra = align(pub, ours)
        for i, (p, o) in enumerate(zip(pub, match)):
            for k, name in ((0, "recall"), (1, "precision")):
                fields.append(field(f"{m} point {i + 1} {name}", s1(p[k]), s1(o[k]) if o else "not drawn"))
        fields.append(field(f"{m} points drawn", str(len(pub)), str(len(ours))))
        if extra:
            extras[m] = extra
    return fields, extras


def main(argv):
    a = json.load(open(argv[1]))
    pub = json.load(open(argv[2]))
    out = {}

    # ---- Sec. 2.1
    c = a["counts"]
    out["text.sec21"] = {"values": {"tolerance": {"printed": True}, "fields": [
        field("HPRD main component, proteins", "8776", str(c["hprd_proteins"])),
        field("HPRD main component, interactions", "35820", str(c["hprd_interactions"])),
        field("OPHID proteins", "9842", str(c["ophid_proteins"])),
        field("OPHID interactions", "73130", str(c["ophid_interactions"])),
        field("genes with a locus", "8470", str(c["genes_with_locus"])),
        field("annotated genes", "1415", str(c["annotated_genes"])),
        field("diseases", "450", str(c["diseases"])),
        field("genes per disease", "4.60", f"{c['genes_per_disease']:.2f}"),
        field("diseases per gene", "1.46", f"{c['diseases_per_gene']:.2f}"),
        field("genes in a disease's intervals", "397", f"{c['genes_per_disease_intervals']:.0f}"),
        field("unannotated genes", "7361", str(c["unannotated_genes"])),
    ]}}

    # ---- Fig. 2 and Supp. Fig. S1
    single = ["Neighborhood", "Oti1", "Oti2", "Oti3", "GS1", "GS2", "GS3", "GS-All", "MCL", "VI-CutL", "VI-CutS", "Prop", "RW"]
    f, extra = curve_fields(pub["fig2a"], a["fig2a"], single)
    out["fig2a"] = {"values": {"tolerance": {"printed": True}, "fields": f}, "extra_points": extra}
    panel_b = [m for m in pub["fig2b"]]
    f, extra = curve_fields(pub["fig2b"], {m: [p for p in a["fig2a"][m] if 0 <= p[0] <= 20 and 20 <= p[1] <= 80] for m in panel_b}, panel_b)
    out["fig2b"] = {"values": {"tolerance": {"printed": True}, "fields": f}, "extra_points": extra}
    f, extra = curve_fields(pub["figS1"], a["figS1"], single)
    out["figS1"] = {"values": {"tolerance": {"printed": True}, "fields": f}, "extra_points": extra}
    if "Consensus" in a["fig2a"]:
        pubc = round_pts(pub["fig2a"]["Consensus"])
        ours = a["fig2a"]["Consensus"]
        f = []
        for i, (p, o) in enumerate(zip(pubc, ours)):
            th = a["consensus"]["points"][i]["theta"]
            f.append(field(f"theta {th} recall", s1(p[0]), s1(o[0])))
            f.append(field(f"theta {th} precision", s1(p[1]), s1(o[1])))
        f.append(field("all five points Pareto optimal", "yes", "yes" if all(a["consensus"]["pareto_optimal"]) else "no"))
        out["fig2a.consensus"] = {"values": {"tolerance": {"printed": True}, "fields": f}}

    # ---- Sec. 3.1 (our run) and the same claims from the paper's own figure points
    s = a["sec31"]

    def claims(fig):
        allp = [tuple(p) for m in single for p in fig[m]]
        clus = [tuple(p) for m in ["GS1", "GS2", "GS3", "GS-All", "MCL", "VI-CutL", "VI-CutS"] for p in fig[m]]
        rw = fig["RW"]
        nb = fig["Neighborhood"]
        return {
            "precision, lowest": min(p for _, p in allp),
            "precision, highest": max(p for _, p in allp),
            "recall, lowest": min(r for r, _ in allp),
            "recall, highest": max(r for r, _ in allp),
            "RW precision at its highest threshold": rw[-1][1],
            "clustering precision, lowest": min(p for _, p in clus),
            "clustering precision, highest": max(p for _, p in clus),
            "clustering recall, lowest": min(r for r, _ in clus),
            "clustering recall, highest": max(r for r, _ in clus),
            "Neighborhood precision, lowest": min(p for _, p in nb),
            "Neighborhood precision, highest": max(p for _, p in nb),
            "Neighborhood recall, lowest": min(r for r, _ in nb),
            "Neighborhood recall, highest": max(r for r, _ in nb),
            "Oti1 recall": fig["Oti1"][0][0],
            "Oti1 precision": fig["Oti1"][0][1],
        }

    printed = {
        "precision, lowest": "17.0", "precision, highest": "92.3", "recall, lowest": "1.2", "recall, highest": "37.6",
        "RW precision at its highest threshold": "92.3",
        "clustering precision, lowest": "18.4", "clustering precision, highest": "68.6",
        "clustering recall, lowest": "1.1", "clustering recall, highest": "17.9",
        "Neighborhood precision, lowest": "23.5", "Neighborhood precision, highest": "40.1",
        "Neighborhood recall, lowest": "2.1", "Neighborhood recall, highest": "23.7",
        "Oti1 recall": "29.5", "Oti1 precision": "19.0",
    }
    ours = claims(a["fig2a"])
    paper_fig = claims({m: round_pts(v) for m, v in pub["fig2a"].items()})
    f = [field(k, printed[k], s1(ours[k])) for k in printed]
    rw = a["fig2a"]["RW"]
    f += [
        field("RW high-precision end, precision (Introduction)", "92", f"{rw[-1][1]:.0f}"),
        field("RW high-precision end, recall (Introduction)", "1", f"{rw[-1][0]:.0f}"),
        field("RW high-recall end, precision (Introduction)", "17", f"{rw[0][1]:.0f}"),
        field("RW high-recall end, recall (Introduction)", "38", f"{rw[0][0]:.0f}"),
        field("RW reaches the highest precision of any single method", "yes", "yes" if s["rw_best_single"] else "no"),
        field("VI-CutS mean precision", "66.0", s1(a["sec31_vicuts"]["mean_precision_grid"])),
        field("VI-CutS mean recall", "1.4", s1(a["sec31_vicuts"]["mean_recall_grid"])),
        field("Oti2 and Oti3 more precise than Oti1, Oti3 more than Oti2", "yes",
              "yes" if s["oti1"][1] < s["oti2"][1] < s["oti3"][1] else "no"),
        field("Oti2 and Oti3 lower recall than Oti1, Oti3 lower than Oti2", "yes",
              "yes" if s["oti1"][0] > s["oti2"][0] > s["oti3"][0] else "no"),
        field("Oti4 no improvement over Oti3", "yes",
              "yes" if not (s["oti4"][0] > s["oti3"][0] or s["oti4"][1] > s["oti3"][1]) else "no"),
    ]
    out["text.sec31"] = {"values": {"tolerance": {"printed": True}, "fields": f}}
    arith = {k: (printed[k], s1(paper_fig[k])) for k in printed}
    agree = [k for k, (e, o) in arith.items() if e == o]
    out["text.arithmetic"] = {
        "check": {
            "passed": len(agree) == len(arith) - 3,
            "detail": f"{len(agree)} of {len(arith)} Sec. 3.1 ranges come back from the points the paper draws in Fig. 2a; "
                      "the other 3 (highest precision, lowest recall, highest clustering precision) are not the "
                      "figure's extremes: " + "; ".join(f"{k}: text {e}, figure {o}" for k, (e, o) in arith.items() if e != o),
        },
        "arithmetic": arith,
    }

    # ---- Sec. 3.2
    b = a["sec32_baselines"]
    out["text.sec32.baselines"] = {"values": {"tolerance": {"printed": True}, "fields": [
        field("random genes in intervals, precision", "1.6", s1(b["random_precision"])),
        field("random genes in intervals, recall", "1.6", s1(b["random_recall"])),
        field("all genes in intervals, recall", "100.0", s1(b["all_recall"])),
        field("all genes in intervals, precision", "1.2", s1(b["all_precision"])),
    ]}}
    if "sec32_noloc" in a:
        n = a["sec32_noloc"]
        out["text.sec32.noloc"] = {"values": {"tolerance": {"printed": True}, "fields": [
            field("random walks, lowest precision", "1.3", s1(n["rw_precision"][0])),
            field("random walks, highest precision", "37.1", s1(n["rw_precision"][1])),
            field("random walks, lowest recall", "1.2", s1(n["rw_recall"][0])),
            field("random walks, highest recall", "29.0", s1(n["rw_recall"][1])),
            field("clustering, lowest precision", "4.4", s1(n["clustering_precision_min"][0])),
            field("clustering, lowest precision, method", "MCL", n["clustering_precision_min"][1]),
            field("clustering, highest precision", "48.0", s1(n["clustering_precision_max"][0])),
            field("clustering, highest precision, method", "VI-CutS", n["clustering_precision_max"][1]),
            field("clustering, lowest recall", "1.1", s1(n["clustering_recall_min"][0])),
            field("clustering, lowest recall, method", "VI-CutS", n["clustering_recall_min"][1]),
            field("clustering, highest recall", "17.9", s1(n["clustering_recall_max"][0])),
            field("clustering, highest recall, method", "MCL", n["clustering_recall_max"][1]),
        ]}}

    # ---- Fig. 3 and Sec. 3.3 (margins printed in the figure)
    f3 = a["fig3"]
    cols_pub = [142, 4, 16, 14, 20, 25, 24, 8, 7, 58]
    rows_pub = [124, 1, 2, 12, 7, 9, 7, 10, 2, 144]
    f = [field(f"recall {i / 10:.1f}-{(i + 1) / 10:.1f}, diseases", str(v), str(f3["columns"][i])) for i, v in enumerate(cols_pub)]
    f += [field(f"precision {(9 - i) / 10:.1f}-{(10 - i) / 10:.1f}, diseases", str(v), str(f3["rows_top_down"][i])) for i, v in enumerate(rows_pub)]
    out["fig3"] = {"values": {"tolerance": {"printed": True}, "fields": f}}
    q = a["sec33"]
    named = ["Bare", "Bernard-Soulier", "Dysfibrinogenemia", "Elliptocytosis", "Epidermolysis", "Griscelli", "Heinz",
             "Hemochromatosis", "Mismatch", "MODY", "Nephronophthisis", "Ovarioleukodystrophy", "Thalassemia", "Trichothiodystrophy"]
    out["text.sec33"] = {"values": {"tolerance": {"printed": True}, "fields": [
        field("diseases with maximum precision > 90%", "124", str(q["max_precision_over_90"])),
        field("diseases with maximum precision < 10%", "144", str(q["max_precision_under_10"])),
        field("diseases predicted by at least 7 methods, all with precision >= 90%", "19", str(q["supp4_rule_count"])),
        field("diseases with >= 3 genes, maximum precision and recall > 90%", "14", str(len(q["both_over_90_three_genes"]))),
        field("the same 14 diseases as named", "yes", "yes" if sorted(x.lower() for x in q["both_over_90_three_genes"]) == sorted(x.lower() for x in named) else "no"),
        field("Fanconi anemia, maximum precision", "100", f"{100 * q['fanconi'][0]:.0f}"),
        field("Fanconi anemia, maximum recall", "69.2", f"{100 * q['fanconi'][1]:.1f}"),
    ]}}
    supp4 = ["Albinism", "Aldosterone", "Bradyopsia", "C1r/C1s", "Chronic", "Cold-induced", "Dysfibrinogenemia", "Exostoses",
             "Gaucher", "GM2-gangliosidosis", "Griscelli", "Hemochromatosis", "Liddle", "Meckel", "Nephronophthisis", "Omenn",
             "Persistent", "Thyrotropin-releasing", "Trichothiodystrophy"]
    out["text.supp4"] = {"values": {"tolerance": {"printed": True}, "fields": [
        field("diseases listed", "19", str(q["supp4_rule_count"])),
        field("the same 19 diseases", "yes", "yes" if sorted(x.lower() for x in q["supp4_rule_diseases"]) == sorted(x.lower() for x in supp4) else "no"),
    ]}}

    # ---- Fig. 4 (counts and legend values printed in the figure; bars and error bars from the PDF)
    legend = {"fig4a": {"Neighborhood": "0.91", "GS-All": "0.65", "VI-CutL": "0.61", "RW": "0.73", "Prop": "0.85"},
              "fig4b": {"Neighborhood": "-0.46", "GS-All": "-0.53", "VI-CutL": "-0.55", "RW": "-0.67", "Prop": "-0.41"}}
    counts = {"fig4a": [311, 37, 24, 24, 11, 10, 12, 10, 3, 8], "fig4b": [46, 84, 162, 113, 45]}
    labels = {"fig4a": ["<10", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80-89", "90-100"],
              "fig4b": ["1-2", "2-3", "3-4", "4-5", ">5"]}
    for k in ("fig4a", "fig4b"):
        ours = a[k]
        f = [field(f"bin {labels[k][i]}, diseases", str(v), str(ours["counts"][i])) for i, v in enumerate(counts[k])]
        f += [field(f"{m}, legend value (Pearson r)", v, f"{ours['fits'][m]['r']:.2f}") for m, v in legend[k].items()]
        f += [field(f"bin {labels[k][i]}, bar height", f"{bar['height']:.3f}", f"{ours['bars'][i]:.3f}") for i, bar in enumerate(pub[k]["bars"])]
        f += [field(f"bin {labels[k][i]}, error bar half-length", f"{(e['high'] - e['low']) / 2:.3f}",
                    f"{ours['spreads']['var_values'][i]:.3f}") for i, e in enumerate(pub[k]["errorbars"])]
        out[k] = {"values": {"tolerance": {"printed": True}, "fields": f}}
    f = []
    for panel, vals in pub["figS2"].items():
        if panel.startswith("_"):
            continue
        for i, v in enumerate(vals):
            lab = labels["fig4a" if panel.startswith("a") else "fig4b"][i]
            f.append(field(f"{panel.replace('_', ' ')}, bin {lab}", f"{v:.3f}", f"{a['figS2'][panel][i]:.3f}"))
    s2_legend = {
        "a_precision": {"Neighborhood": "0.81", "GS-All": "0.60", "VI-CutL": "0.61", "RW": "0.67", "Prop": "0.71"},
        "a_recall": {"Neighborhood": "0.90", "GS-All": "0.64", "VI-CutL": "0.56", "RW": "0.69", "Prop": "0.86"},
        "b_precision": {"Neighborhood": "-0.35", "GS-All": "-0.37", "VI-CutL": "-0.39", "RW": "-0.45", "Prop": "-0.24"},
        "b_recall": {"Neighborhood": "-0.48", "GS-All": "-0.58", "VI-CutL": "-0.60", "RW": "-0.70", "Prop": "-0.47"},
    }
    for panel, vals in s2_legend.items():
        for m, v in vals.items():
            f.append(field(f"{panel.replace('_', ' ')}, {m} legend value (Pearson r)", v, f"{a['figS2']['r'][panel][m]:.2f}"))
    f.append(field("caption: average precision at homophily 60-69% (about, %)", "95", f"{100 * a['figS2']['a_precision'][6]:.0f}"))
    out["figS2"] = {"values": {"tolerance": {"printed": True}, "fields": f}}

    # ---- Sec. 3.5
    u = a["sec35"]
    out["text.sec35"] = {"values": {"tolerance": {"printed": True}, "fields": [
        field("Neighborhood uniqueness (%)", "18.9", s1(u["uniqueness"]["Neighborhood"])),
        field("VI-CutL uniqueness (%)", "7.6", s1(u["uniqueness"]["VI-CutL"])),
        field("GS-All uniqueness (%)", "5.0", s1(u["uniqueness"]["GS-All"])),
        field("Prop uniqueness (%)", "3.1", s1(u["uniqueness"]["Prop"])),
        field("RW uniqueness (%)", "30.7", s1(u["uniqueness"]["RW"])),
        field("predictions made by the five methods", "976", str(u["predictions"])),
        field("wrong and made by all five", "19", str(u["wrong_by_all_five"])),
        field("wrong and made by all five (%)", "1.9", s1(u["wrong_by_all_five_pct"])),
    ]}}

    # ---- Supplementary Table 1 (scores our rerun computes without linkage intervals)
    if "suppT1" in a:
        t = a["suppT1"]
        printed_t1 = {
            "PRMT2|Myocardial": {"Neighborhood": "0.1", "Oti": "1", "MCL": "0.03", "Prop": "0.12", "RW": "9.8e-5"},
            "PSMA5|Myocardial": {"GS1 (authors' file)": "0.5", "GS2 (authors' file)": "0.5", "MCL": "0.8", "Prop": "0.18", "RW": "2.3e-4"},
            "BCAS2|Myocardial": {"Neighborhood": "0.25", "Oti": "1", "MCL": "0.03", "Prop": "0.17", "RW": "9.3e-5"},
            "ALOX5|Myocardial": {"Neighborhood": "0.2", "Oti": "1", "GS1 (authors' file)": "1.0", "GS2 (authors' file)": "1.0",
                                 "MCL": "0.5", "VI-CutL (authors' file)": "1.0", "Prop": "0.18", "RW": "0.02"},
            "MYC|Cleft": {"Neighborhood": "0.02", "Oti": "1", "Prop": "0.009", "RW": "6.1e-4"},
            "MDM2|Melanoma": {"Neighborhood": "0.02", "Oti": "1", "Prop": "0.016", "RW": "8.2e-4"},
            "ATM|Pancreatic": {"Neighborhood": "0.08", "Oti": "3", "Prop": "0.044", "RW": "2.7e-3"},
        }
        f = []
        for pair, cols in printed_t1.items():
            for m, v in cols.items():
                o = t.get(pair, {}).get(m)
                if o is None:
                    obs = "not available"
                elif "e" in v:
                    mant_dec = len(v.split("e")[0].split(".")[1]) if "." in v else 0
                    obs = f"{o:.{mant_dec}e}".replace("e-0", "e-").replace("e+0", "e+")
                else:
                    dec = len(v.split(".")[1]) if "." in v else 0
                    obs = f"{o:.{dec}f}"
                f.append(field(f"{pair.replace('|', ' / ')}: {m}", v, obs))
        out["tableS1"] = {"values": {"tolerance": {"printed": True}, "fields": f}}

    # ---- the rerun against the authors' scores
    r = a["rerun"]
    tot = sum(v["pairs"] for net in r.values() for v in net.values())
    eq = sum(v["equal"] for net in r.values() for v in net.values())
    nl = a.get("noloc", {}).get("agreement", {})
    nl_tot = sum(v["pairs_in_file"] for v in nl.values())
    nl_eq = sum(v["equal"] for v in nl.values())
    out["port"] = {"check": {
        "passed": eq == tot and nl_eq == nl_tot,
        "detail": f"Neighborhood, Oti, RW, Prop (diseasenet) and MCL 14-137 rerun on HPRD and OPHID: {eq:,} of {tot:,} "
                  f"candidate-pair scores equal the authors' prediction files (relative difference below 1e-9; the files "
                  f"print 12 digits); without linkage intervals, {nl_eq:,} of {nl_tot:,} scores in the thresholded "
                  f"HPRD-NOLOC files.",
    }}
    # The same fields as a list, for the repository's results-check (its paths split keys on dots).
    out["item_list"] = [{"key": k.replace(".", ""), "fields": v["values"]["fields"]} for k, v in out.items() if "values" in v]
    json.dump(out, open(argv[3], "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

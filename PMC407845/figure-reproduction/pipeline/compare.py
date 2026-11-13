"""Compare our outputs with the paper: every field, pixel score and claim that results.json needs.

  compare.py RUN_DIR OUT_JSON

Reads networker.py, validate.py and figures.py outputs from RUN_DIR and writes comparison.json:
{"items": {id: {"method": ..., "values" | "pixels" | "check": ..., "outputs": [...]}}, "summary": {...}}.
Printed values are strings, so check_results.py compares them at printed precision.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

from networker import DELETION_TFS, PAPER_TFS

TABLE1 = {
    "Abf1": (5638, 138, 136, 470), "Ace2": (5843, 33, 33, 473), "Arg81": (5985, 11, 10, 376),
    "Bas1": (5975, 28, 13, 366), "Cad1": (5854, 26, 13, 489), "Dal81": (5823, 24, 16, 519),
    "Dig1": (5872, 20, 11, 479), "Fhl1": (5754, 146, 37, 445), "Fkh2": (5261, 61, 45, 1015),
    "Gal4": (5149, 20, 20, 1193), "Gat3": (5891, 40, 29, 422), "Gcn4": (5919, 58, 21, 384),
    "Hal9": (5948, 4, 13, 417), "Hap4": (5939, 47, 21, 375), "Hir1": (5963, 19, 10, 390),
    "Hir2": (5932, 8, 13, 429), "Hsf1": (5929, 35, 17, 401), "Leu3": (5988, 8, 13, 373),
    "Mbp1": (5641, 65, 40, 636), "Mcm1": (5709, 42, 46, 585), "Met31": (5983, 15, 13, 371),
    "Msn4": (5952, 23, 7, 400), "Mss11": (4735, 11, 9, 1627), "Ndd1": (5799, 50, 42, 491),
    "Nrg1": (5912, 61, 20, 389), "Rlm1": (5900, 13, 24, 445), "Sig1": (5683, 0, 0, 699),
    "Sko1": (5155, 2, 0, 1225), "Sok2": (4881, 10, 6, 1485), "Stb1": (5791, 13, 10, 568),
    "Ste12": (5725, 19, 31, 607), "Sum1": (5919, 35, 26, 402), "Swi4": (5528, 75, 48, 731),
    "Swi5": (5358, 47, 45, 932), "Thi2": (5940, 5, 1, 436), "Yap1": (5959, 28, 16, 379),
    "Yap6": (5924, 33, 54, 371),
}
TABLE2 = {  # TF: genome mean, sd, B+/C+ mean, sd, -log10 p, B+/C- mean, sd, -log10 p
    "Dig1": ("0.759", "0.198", "0.567", "0.360", "3.76", "0.846", "0.080", "0.04"),
    "Gcn4": ("0.785", "0.177", "0.294", "0.329", "28.23", "0.793", "0.170", "0.24"),
    "Hir2": ("0.724", "0.218", "0.180", "0.295", "4.00", "0.760", "0.194", "0.14"),
    "Mbp1": ("0.830", "0.121", "0.541", "0.324", "27.86", "0.770", "0.172", "2.79"),
    "Swi4": ("0.524", "0.338", "0.348", "0.352", "4.89", "0.533", "0.333", "0.24"),
    "Swi5": ("0.744", "0.204", "0.583", "0.373", "5.98", "0.759", "0.186", "0.17"),
    "Yap1": ("0.756", "0.201", "0.471", "0.376", "7.66", "0.587", "0.337", "2.67"),
}
TABLE4 = {  # B-, B+/D+, B+/D-, not available, GO B+/D+, GO B+/D-
    "Dig1": (5881, 1, 30, 115, 32, 16), "Gcn4": (5928, 16, 63, 60, 19, 17), "Hir2": (5941, 2, 19, 105, 24, 5),
    "Mbp1": (5647, 2, 103, 315, 22, 12), "Swi4": (5535, 19, 106, 407, 9, 6), "Swi5": (5368, 10, 82, 607, 2, 0),
    "Yap1": (5968, 7, 37, 55, 0, 0),
}
CLASS_NAMES = ["B-", "B+/C+", "B+/C-", "unclassified"]
SIG = 0.05  # the paper's significance level where it states none
PIX_THRESHOLD = 0.9


def fmt1(x):
    return None if x is None else f"{x:.1f}"


def share_coupled(counts):
    """Mean over TFs with bound genes of B+/C+ / (B+/C+ + B+/C-), in percent."""
    v = [c[1] / (c[1] + c[2]) for c in counts if c[1] + c[2] > 0]
    return 100 * float(np.mean(v)), 100 * sum(c[1] for c in counts) / sum(c[1] + c[2] for c in counts)


def main(run_dir, out_json):
    run = Path(run_dir)
    J = lambda n: json.load(open(run / n))
    sel, t1, go, dele, mot, div, sim, figs = (J("selection.json"), J("table1.json"), J("go.json"), J("deletion.json"),
                                               J("motifs.json"), J("divergent.json"), J("simon.json"), J("figures.json"))
    items = {}

    # --- Fig. 1b: caption claim, which group of experiments carries the largest activity changes
    with open(run / "tfap.tsv", encoding="utf-8") as f:
        tfap = list(csv.DictReader(f, delimiter="\t"))
    groups = {"stress": "Gasch_2000", "pheromone": "Roberts_2000", "cell cycle": "Spellman_1998"}
    expect = {"Hap4": "stress", "Ndd1": "cell cycle", "Ste12": "pheromone"}
    fields, detail = [], {}
    for tf, exp in expect.items():
        m = {g: float(np.mean([abs(float(r[tf])) for r in tfap if r["source"] == s])) for g, s in groups.items()}
        detail[tf] = {g: round(v, 3) for g, v in m.items()}
        fields.append({"name": f"{tf}: group with the largest mean |activity|", "expected": exp, "observed": max(m, key=m.get)})
    items["fig1b"] = {"method": "values", "values": {"fields": fields, "tolerance": {"printed": True}, "mean_abs_t": detail},
                      "outputs": ["figure-reproduction/output/fig1_ours.png", "figure-reproduction/output/fig1_overlay.png"]}

    # --- Fig. 1c: pixels
    for tf in ("Hap4", "Ndd1", "Ste12"):
        s = figs["fig1"][f"fig1c.{tf}"]
        items[f"fig1c.{tf.lower()}"] = {
            "method": "pixels",
            "pixels": {"tolerance_px": s["tolerance_px"], "dpi": 160, "published_near_ours": s["published_near_ours"],
                       "ours_near_published": s["ours_near_published"], "threshold": PIX_THRESHOLD, "controls": s["controls"]},
            "outputs": ["figure-reproduction/output/fig1_ours.png", "figure-reproduction/output/fig1_overlay.png"]}

    # --- text: TF selection
    items["text.tf_selection"] = {"method": "values", "values": {"fields": [
        {"name": "TFs kept by backward selection (of 113)", "expected": "37", "observed": str(sel["n_selected"])},
        {"name": "the paper's 37 TFs among those kept", "expected": "37", "observed": str(len(sel["paper_tfs_selected"]))},
    ], "tolerance": {"printed": True}}, "detail": {"top37_overlap": sel["top37_overlap"],
                                                   "not_selected": sel["paper_tfs_not_selected"]}}

    # --- Table 1
    main_counts = t1["variants"]["main"]["counts"]
    fields = []
    for tf in PAPER_TFS:
        for k, col in enumerate(CLASS_NAMES):
            obs = main_counts.get(tf)
            fields.append({"name": f"{tf} {col}", "expected": str(TABLE1[tf][k]), "observed": None if obs is None else str(obs[k])})
    items["table1"] = {"method": "values", "values": {"fields": fields, "tolerance": {"printed": True}}}

    def t1_score(variant):
        c = t1["variants"][variant]["counts"]
        hits = sum(1 for tf in PAPER_TFS if tf in c for k in range(4) if c[tf][k] == TABLE1[tf][k])
        bc = sum(abs(c[tf][1] - TABLE1[tf][1]) for tf in PAPER_TFS if tf in c)
        n = sum(1 for tf in PAPER_TFS if tf in c)
        sh = share_coupled([c[tf] for tf in PAPER_TFS if tf in c])
        return {"fields_exact": hits, "tfs": n, "sum_abs_diff_b+c+": bc, "mean_coupled_share": round(sh[0], 1)}
    items["table1"]["variants"] = {v: t1_score(v) for v in t1["variants"]}
    bplus = sum(1 for tf in PAPER_TFS if tf in main_counts and main_counts[tf][1] + main_counts[tf][2] == TABLE1[tf][1] + TABLE1[tf][2])
    items["table1"]["detail"] = {"b+_total_exact": bplus}

    # --- text: 58%
    ours_share = share_coupled([main_counts[tf] for tf in PAPER_TFS if tf in main_counts])
    items["text.coupled_share"] = {"method": "values", "values": {"fields": [
        {"name": "mean share of bound genes that couple (%)", "expected": "58", "observed": f"{ours_share[0]:.0f}"},
    ], "tolerance": {"printed": True}}, "detail": {"mean": round(ours_share[0], 2), "pooled": round(ours_share[1], 2)}}

    # --- text.arithmetic: the paper's claims from its own tables
    paper_share = share_coupled([TABLE1[tf] for tf in PAPER_TFS])
    rows_6382 = sum(1 for v in TABLE1.values() if sum(v) == 6382)
    t2_insig = sum(1 for v in TABLE2.values() if float(v[7]) < -np.log10(SIG))
    t2_sig = sum(1 for v in TABLE2.values() if float(v[4]) > -np.log10(SIG))
    from validate import TABLE3
    t3_all = all(float(pc) > float(pm) for _, _, pc, pm in TABLE3)
    pub = go["published"]
    zero_green = sum(1 for g in pub["green"] if g == 0)
    t4_sums = {tf: sum(v[:4]) for tf, v in TABLE4.items()}
    claims = [
        ("58% of bound genes couple, from Table 1", f"{paper_share[0]:.0f}" == "58"),
        ("every Table 1 row sums to the same gene count (6382)", rows_6382 == 37),
        ("B+/C+ respond to deletion for all 7 TFs, from Table 2 (P < 0.05)", t2_sig == 7),
        ("B+/C- response insignificant for most TFs, from Table 2 (P < 0.05)", t2_insig > 3.5),
        ("B+/C- motif enrichment below B+/C+ in every case, from Table 3", t3_all),
        ("no enriched GO category in most B+/C- groups, from Fig. 2", zero_green > len(pub["green"]) / 2),
    ]
    ok = sum(c[1] for c in claims)
    items["text.arithmetic"] = {"method": "check", "check": {
        "passed": ok == len(claims),
        "detail": f"{ok} of {len(claims)} claims come back from the paper's own tables and Fig. 2 values "
                  f"(58% is {paper_share[0]:.1f}% per TF, {paper_share[1]:.1f}% pooled; B+/C- insignificant for "
                  f"{t2_insig} of 7 in Table 2; {zero_green} of 37 B+/C- bars are 0). Table 4 rows sum to "
                  f"{sorted(set(t4_sums.values()))} genes (Dig1 {t4_sums['Dig1']}), not to Table 1's 6382."},
        "claims": [{"claim": c, "holds": h} for c, h in claims]}

    # --- Fig. 2 (values from the vector EPS)
    fields = []
    for k, tf in enumerate(go["tfs"]):
        o = go["ours"].get(tf)
        for col, name, cls in (("red", "B+/C+", "B+/C+"), ("green", "B+/C-", "B+/C-")):
            exp = pub[col][k]
            if exp is None:   # no bar drawn (Sig1 has no B+/C+ genes)
                continue
            fields.append({"name": f"{tf} {name}", "expected": str(exp), "observed": None if o is None else str(o[cls]["bonferroni"])})
    var = {}
    for key in ("bonferroni", "bonferroni_hit_terms", "bh"):
        hits = 0
        for k, tf in enumerate(go["tfs"]):
            o = go["ours"].get(tf)
            for col, cls in (("red", "B+/C+"), ("green", "B+/C-")):
                if o and pub[col][k] is not None and o[cls][key] == pub[col][k]:
                    hits += 1
        var[key] = hits
    items["fig2"] = {"method": "values", "values": {"fields": fields, "tolerance": {"printed": True}},
                     "variants_exact_fields": var,
                     "outputs": ["figure-reproduction/output/fig2_ours.png", "figure-reproduction/output/fig2_overlay.png"]}

    # --- text: GO claim
    ours_go = [go["ours"][tf] for tf in go["tfs"] if go["ours"].get(tf)]
    zero_ours = sum(1 for o in ours_go if o["B+/C-"]["bonferroni"] == 0)
    more = sum(1 for o in ours_go if o["B+/C+"]["bonferroni"] > o["B+/C-"]["bonferroni"])
    less = sum(1 for o in ours_go if o["B+/C+"]["bonferroni"] < o["B+/C-"]["bonferroni"])
    items["text.go_claim"] = {"method": "values", "values": {"fields": [
        {"name": "no enriched GO category in most B+/C- groups", "expected": "yes", "observed": "yes" if zero_ours > len(ours_go) / 2 else "no"},
        {"name": "B+/C+ groups enriched more often than B+/C- groups", "expected": "yes", "observed": "yes" if more > less else "no"},
    ], "tolerance": {"printed": True}}, "detail": {"b+c-_zero": zero_ours, "tfs": len(ours_go), "paper_b+c-_zero": zero_green,
                                                   "b+c+_more": more, "b+c-_more": less}}

    # --- text: deletion response (Table 2's claim; computed on Hughes log10 ratios)
    sig_cc = sum(1 for tf in DELETION_TFS if (dele["ours"][tf]["B+/C+"]["log_ratio"] or {}).get("neglog10_p", 0) > -np.log10(SIG))
    insig_cm = sum(1 for tf in DELETION_TFS if (dele["ours"][tf]["B+/C-"]["log_ratio"] or {}).get("neglog10_p", 0) < -np.log10(SIG))
    items["text.deletion"] = {"method": "values", "values": {"fields": [
        {"name": "B+/C+ genes respond to the deletion (P < 0.05), TFs of 7", "expected": "7", "observed": str(sig_cc)},
        {"name": "B+/C- response insignificant for most TFs", "expected": "yes", "observed": "yes" if insig_cm > 3.5 else "no"},
    ], "tolerance": {"printed": True}}, "detail": {tf: {"b+c+": round(dele["ours"][tf]["B+/C+"]["log_ratio"]["neglog10_p"], 2),
                                                        "b+c-": round(dele["ours"][tf]["B+/C-"]["log_ratio"]["neglog10_p"], 2)}
                                                   for tf in DELETION_TFS}}
    genome = {tf: dele["ours"][tf]["genome"] for tf in DELETION_TFS}
    items["table2"] = {"method": "none", "detail": {"genome_log10_ratio": {tf: [round(g["log_ratio"]["mean"], 3), round(g["log_ratio"]["sd"], 3)] for tf, g in genome.items()},
                                                    "genome_abs_log10_ratio": {tf: [round(g["abs_log_ratio"]["mean"], 3), round(g["abs_log_ratio"]["sd"], 3)] for tf, g in genome.items()}}}

    # --- Table 3 and its claim
    fields = []
    for r in mot["rows"]:
        for k, cls in enumerate(("B+/C+", "B+/C-")):
            fields.append({"name": f"{r['motif']} {r['tf']} {cls}", "expected": r["paper"][k], "observed": fmt1(r[cls]["neglog10_p"])})
    items["table3"] = {"method": "values", "values": {"fields": fields, "tolerance": {"printed": True}},
                       "variants_exact_fields": {v: sum(1 for r in rows for k, c in enumerate(("B+/C+", "B+/C-")) if fmt1(r[c]["neglog10_p"]) == r["paper"][k])
                                                 for v, rows in mot["variants"].items()}}
    allv = {v: all(r["B+/C+"]["neglog10_p"] > r["B+/C-"]["neglog10_p"] for r in rows) for v, rows in mot["variants"].items()}
    items["text.motif_claim"] = {"method": "values", "values": {"fields": [
        {"name": "B+/C- enrichment below B+/C+ in every case", "expected": "yes", "observed": "yes" if allv["main"] else "no"},
    ], "tolerance": {"printed": True}}, "variants": allv,
        "detail": [f"{r['motif']} {r['tf']}: {r['B+/C+']['neglog10_p']:.1f} vs {r['B+/C-']['neglog10_p']:.1f}" for r in mot["rows"]]}

    # --- text: Simon overlap
    items["text.simon_overlap"] = {"method": "values", "values": {"fields": [
        {"name": "mean overlap of B+/C+ groups, Simon et al. against Lee et al. (%)", "expected": "85",
         "observed": f"{100 * sim['mean_share_of_lee']:.0f}"},
    ], "tolerance": {"printed": True}}, "detail": {k: round(100 * sim[k], 1) for k in ("mean_share_of_lee", "mean_share_of_simon", "mean_jaccard")}}

    # --- text: divergent probes
    items["text.divergent_probes"] = {"method": "values", "values": {"fields": [
        {"name": "ChIP probes shared by divergently transcribed genes", "expected": "1592", "observed": str(div["probes_shared"])},
        {"name": "ChIP probes in all", "expected": "4532", "observed": str(div["probes"])},
    ], "tolerance": {"printed": True}}}

    # --- Fig. 3
    fields = []
    for r in div["fig3"]:
        v = r.get("neglog10_p_one_sided")
        obs = None if v is None else (">12.0" if v > 12 else f"{v:.1f}")
        fields.append({"name": f"{r['tf']} to {r['gene']}", "expected": r["paper"], "observed": obs})
    items["fig3"] = {"method": "values", "values": {"fields": fields, "tolerance": {"printed": True}},
                     "two_sided": {f"{r['tf']} to {r['gene']}": (None if r.get("neglog10_p_two_sided") is None else round(r["neglog10_p_two_sided"], 2)) for r in div["fig3"]},
                     "outputs": ["figure-reproduction/output/fig3_ours.png", "figure-reproduction/output/fig3_overlay.png"]}

    comp = J("compendium.json")
    items["text.inputs"] = {"method": "values", "values": {"fields": [
        {"name": "expression arrays in the library", "expected": "751", "observed": str(comp["arrays"])},
        {"name": "TFs with ChIP data", "expected": "113", "observed": str(sel["n_tfs"])},
    ], "tolerance": {"printed": True}}}

    items["table4"] = {"method": "none", "detail": {"row_sums": t4_sums}}
    items["fig1a"] = {"method": "none"}

    # item_list: the same items as a list keyed without dots, for tools/check_results.py paths
    item_list = [{"key": k.replace(".", "_"), **v} for k, v in items.items()]
    Path(out_json).write_text(json.dumps({"items": items, "item_list": item_list}, indent=1) + "\n")
    print(f"{len(items)} items compared")


if __name__ == "__main__":
    main(*sys.argv[1:3])

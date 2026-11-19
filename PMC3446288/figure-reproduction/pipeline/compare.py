#!/usr/bin/env python3
"""Compare our numbers with the paper's: one entry per item of results.json (values, pixels or checks).

Usage: compare.py PAPER_VALUES.json ANALYSIS.json FIGURES.json CONSERVATION.json REFSEQ_STOPS.json
                  JDB_STATS.json PORT_CHECKS.json OUT.json
The hand-written parts of each item (labels, assumptions, causes) are in results_notes.json; build_results.py
merges the two.
"""

import json
import sys

SAMPLES = ["BMM_WT", "BMM_KO", "Liver_WT", "Liver_KO"]
NICE = {"BMM_WT": "BMM WT", "BMM_KO": "BMM KO", "Liver_WT": "Liver WT", "Liver_KO": "Liver KO"}


def num(s):
    return float(str(s).replace(",", ""))


def r(x, nd=0):
    """Round for an observed field, keeping integers integral."""
    if x is None:
        return None
    return int(round(x)) if nd == 0 else round(float(x), nd)


def field(name, expected, observed, tol=None):
    f = {"name": name, "expected": expected, "observed": observed}
    if tol is not None:
        f["tolerance"] = tol
    return f


def values(fields, tol=None, exceptions=None):
    v = {"tolerance": tol or {"printed": True}, "fields": fields}
    if exceptions:
        v["exceptions"] = exceptions
    return {"method": "values", "values": v}


def main(pv_path, an_path, fig_path, cons_path, stops_path, jdb_path, port_path, out_path):
    pv = json.load(open(pv_path))
    an = json.load(open(an_path))
    fg = json.load(open(fig_path))
    cons = json.load(open(cons_path))
    st = json.load(open(stops_path))
    jdb = json.load(open(jdb_path))
    port = json.load(open(port_path))
    items = {}

    # ---- junction database
    items["text.junction_db"] = values([field("unique junctions in the combinatorial database", pv["junction_db"], jdb["junctions"])])

    # ---- Fig. 1a
    fl = []
    for s in SAMPLES:
        for k in ("exonic", "junction", "intronic", "intergenic", "total_mapped"):
            fl.append(field(f"{NICE[s]} {k.replace('_', ' ')}", pv["fig1a"][s][k], an["fig1a"][s][k]))
        fl.append(field(f"{NICE[s]} mapping frequency", pv["fig1a"][s]["mapping_frequency"], r(an["fig1a"][s]["mapping_frequency"], 4)))
    items["fig1a"] = values(fl)

    # ---- mapping numbers in the text
    m = an["mapping"]
    tm = pv["text_mapping"]
    trunc = sorted(m["truncation_fraction"].values())
    th_share = [an["tableS1"][s]["tophat_only"] / an["tableS1"][s]["total"] for s in SAMPLES]
    items["text.mapping"] = values([
        field("reads mapped to genome or transcriptome (%)", tm["mapped_pct"], r(100 * m["mapped_fraction"], 2)),
        field("mapped reads on splice junctions (%)", tm["junction_pct_of_mapped"], r(100 * m["junction_fraction_of_mapped"], 2)),
        field("unique splice junctions, four samples", tm["unique_junctions"], an["unique_junctions_all_samples"]),
        field("unique junctions with at least three reads (approximately)", tm["junctions_min3"], an["unique_junctions_min3"], {"abs": 5000}),
        field("reads recovered by truncation, lowest sample (%)", tm["truncation_pct_low"], r(100 * trunc[0], 2)),
        field("reads recovered by truncation, highest sample (%)", tm["truncation_pct_high"], r(100 * trunc[-1], 2)),
        field("junctions found by TopHat only, lowest sample (%)", tm["tophat_unique_pct_low"], r(100 * min(th_share), 2)),
        field("junctions found by TopHat only, highest sample (%)", tm["tophat_unique_pct_high"], r(100 * max(th_share), 2)),
    ])
    items["text.truncation"] = values([field(NICE[s], pv["truncation"][s], m["truncation_recovered"][s]) for s in SAMPLES])
    items["text.tmm"] = values([field(NICE[s], pv["tmm"][s], r(an["tmm_factors"][s], 4)) for s in SAMPLES])

    # ---- Table S1
    fl = []
    for s in SAMPLES:
        for k, lab in (("comb_db_only", "Comb. DB only"), ("tophat_only", "TopHat only"), ("both", "Both"), ("total", "Total")):
            fl.append(field(f"{NICE[s]}, {lab}", pv["tableS1"][s][k], an["tableS1"][s][k]))
    items["tableS1"] = values(fl)

    # ---- Table S2
    fl, exc = [], []
    for t in ("BMM", "Liver"):
        o = an["tissues"][t]["tableS2"]
        p = pv["tableS2"][t]
        for k, lab in (("all", "all junctions"), ("ptc", "PTC+ junctions"), ("tophat_all", "all TopHat junctions"), ("tophat_ptc", "PTC+ TopHat junctions")):
            fl.append(field(f"{t}, {lab}", p[k], o[k]))
        fl.append(field(f"{t}, TopHat share of all junctions (%)", p["tophat_all_pct"], r(100 * o["tophat_all"] / o["all"], 2)))
        fl.append(field(f"{t}, TopHat share of PTC+ junctions (%)", p["tophat_ptc_pct"], r(100 * o["tophat_ptc"] / o["ptc"], 2) if o["ptc"] else None))
    items["tableS2"] = values(fl)

    # ---- PTC filters
    fl = [field(f"junctions with an unannotated exon, {NICE[s]}", pv["ptc_filters"]["unannotated"][s],
                an["ptc_filters"]["unannotated_exon_junctions"][s]) for s in SAMPLES]
    for t in ("BMM", "Liver"):
        fl.append(field(f"false-positive PTC genes untagged, {t}", pv["ptc_filters"]["false_positive_genes"][t], an["tissues"][t]["false_positive_genes"]))
        fl.append(field(f"junctions with ambiguous CDS excluded, {t}", pv["ptc_filters"]["ambiguous_cds"][t], an["tissues"][t]["ambiguous_cds_junctions"]))
    items["text.ptc_filters"] = values(fl)

    # ---- Fig. 2a
    fl = []
    for t in ("BMM", "Liver", "Common"):
        src = an["common"] if t == "Common" else an["tissues"][t]
        for block, key in (("all", "fig2a_all"), ("ptc", "fig2a_ptc")):
            for reg in ("up", "unregulated", "down"):
                for ui, unit in enumerate(("junctions", "genes")):
                    lab = f"{t}, {'PTC+' if block == 'ptc' else 'all'} {unit}, {reg}"
                    fl.append(field(lab, pv["fig2a"][t][block][reg][ui], src[key][reg][unit]))
                    fl.append(field(lab + " (%)", pv["fig2a"]["pct"][t][block][reg][ui], r(src[key][reg][unit + "_pct"], 2)))
    items["fig2a"] = values(fl)

    # ---- Fig. 2 numbers in the text
    tf = pv["text_fig2"]
    T = an["tissues"]
    items["text.fig2"] = values([
        field("junctions with >= 3 reads, BMM (approximately)", tf["junctions_BMM"], T["BMM"]["evident_junctions"], {"abs": 5000}),
        field("junctions with >= 3 reads, liver (approximately)", tf["junctions_Liver"], T["Liver"]["evident_junctions"], {"abs": 5000}),
        field("up-regulated junctions per gene, BMM", tf["up_per_gene_BMM"], r(T["BMM"]["up_junctions_per_gene"], 3)),
        field("up-regulated junctions per gene, liver", tf["up_per_gene_Liver"], r(T["Liver"]["up_junctions_per_gene"], 3)),
        field("PTC+ junctions up-regulated, BMM (%)", tf["ptc_up_pct"], r(100 * T["BMM"]["ptc_up_share"], 2)),
        field("PTC+ junctions up-regulated, liver (%)", tf["ptc_up_pct"], r(100 * T["Liver"]["ptc_up_share"], 2)),
        field("expressed genes with an up-regulated PTC+ junction, BMM (%)", tf["genes_ptc_up_pct_BMM"], r(100 * T["BMM"]["genes_with_up_ptc_share_of_expressed"], 2)),
        field("expressed genes with an up-regulated PTC+ junction, liver (%)", tf["genes_ptc_up_pct_Liver"], r(100 * T["Liver"]["genes_with_up_ptc_share_of_expressed"], 2)),
        field("all versus PTC+ junctions, chi-square (BMM)", "significant", "significant" if T["BMM"]["chisq_all_vs_ptc"]["p"] < 0.05 else "not significant"),
        field("all versus PTC+ junctions, chi-square (liver)", "significant", "significant" if T["Liver"]["chisq_all_vs_ptc"]["p"] < 0.05 else "not significant"),
    ])
    items["text.core_targets"] = values([
        field("up-regulated PTC+ junctions shared by both tissues", tf["core_junctions"], an["common"]["core_junctions"]),
        field("their genes", tf["core_genes"], len(an["common"]["core_genes"])),
    ])

    # ---- Fig. 3a
    fl = []
    for t in ("BMM", "Liver", "Common"):
        src = an["common"]["fig3a"] if t == "Common" else an["tissues"][t]["fig3a"]
        for kind in ("canonical", "alternative"):
            for k in ("up", "unregulated", "down", "ptc_of_up"):
                lab = f"{t}, {kind} junctions, {'PTC+ share of up-regulated' if k == 'ptc_of_up' else k} (%)"
                fl.append(field(lab, pv["fig3a"][t][kind][k], r(src[kind][k], 2)))
    items["fig3a"] = values(fl)
    t3 = pv["text_fig3"]
    fb = an["fig3b"]
    share = {t: an["tissues"][t]["fig3a"]["alternative"]["up"] * an["tissues"][t]["fig3a"]["alternative"]["ptc_of_up"] / 100 for t in ("BMM", "Liver")}
    items["text.fig3"] = values([
        field("unique AS junctions, BMM (approximately)", t3["as_BMM"], fb["BMM_union"], {"abs": 500}),
        field("unique AS junctions, liver (approximately)", t3["as_Liver"], fb["Liver_union"], {"abs": 500}),
        field("AS directly degraded by NMD, BMM (%)", t3["nmd_share_BMM"], r(share["BMM"], 2)),
        field("AS directly degraded by NMD, liver (%)", t3["nmd_share_Liver"], r(share["Liver"], 2)),
    ], exceptions=[{"field": "unique AS junctions, liver (approximately)", "category": "paper_error",
                    "evidence": "The Fig. 3b caption gives 33,164 unique AS junctions in liver; the text says approximately 35,000."}])

    # ---- Fig. 3b
    fl = []
    p3 = pv["fig3b"]
    for s in SAMPLES:
        fl.append(field(f"AS junctions, {NICE[s]}", p3["as_junctions"][s], fb[s]["as_junctions"]))
    for t in ("BMM", "Liver"):
        fl.append(field(f"AS junctions, {t} (WT or KO)", p3["as_junctions"][f"{t}_union"], fb[f"{t}_union"]))
    for s in SAMPLES:
        fl.append(field(f"AS junctions per million junction reads, {NICE[s]}", p3["per_million"][s], r(fb[s]["per_million_junction_reads"])))
    for s in SAMPLES:
        fl.append(field(f"slope, AS junctions, {NICE[s]}", p3["slope_as"][s], r(fb[s]["slope_as"], 3)))
        fl.append(field(f"slope, PTC+ junctions, {NICE[s]}", p3["slope_ptc"][s], r(fb[s]["slope_ptc"], 3)))
    items["fig3b"] = values(fl)

    # ---- Table 1
    fl = []
    for t in ("BMM", "Liver"):
        for row, cols in pv["table1"][t].items():
            for k, v in cols.items():
                o = an["table1"][t][row].get(k)
                fl.append(field(f"{t}, {row}, {k.replace('_', ' ')}", v, o))
            if "ptc" in cols and "total" in cols:
                o = an["table1"][t][row]
                pct = 100 * o["ptc"] / o["total"] if o["total"] else None
                pexp = round(100 * num(cols["ptc"]) / num(cols["total"]))
                fl.append(field(f"{t}, {row}, PTC+ (%)", str(pexp), r(pct, 2)))
    items["table1"] = values(fl)

    # ---- examples in the text
    fl = []
    for g, per in pv["examples"].items():
        for t, v in per.items():
            e = an["examples"][t].get(g)
            fl.append(field(f"{g} dPSI, {t} (%)", v, r(100 * e["dpsi"], 2) if e else None))
    for g, per in pv["gene_fc"].items():
        for t, v in per.items():
            fl.append(field(f"{g} gene fold change, {t}", v, r(an["gene_fc"][t].get(g), 3)))
    items["text.examples"] = values(fl)

    # ---- Tables S7 and S8
    items["tableS7"] = values([field("PTC-upon-inclusion SES events up in both tissues", pv["tableS7_events"], an["tableS7"]["events"])])
    items["tableS8"] = values([
        field("PTC-upon-exclusion SES events up in both tissues (Results)", pv["tableS8_events_results"], an["tableS8"]["events"]),
        field("their genes (Discussion, Additional file 9)", pv["tableS8_genes_file"], len(an["tableS8"]["genes"])),
    ])

    # ---- Table S5
    fl = []
    for t in ("BMM", "Liver"):
        for g, (gfc, wt, ko, canon) in pv["tableS5"][t].items():
            o = an["tableS5"][t].get(g, {})
            fl.append(field(f"{t} {g} gene Fc", gfc, r(o.get("gene_fc"), 3)))
            if canon is not None:
                fl.append(field(f"{t} {g} canonical fc", canon, r(o.get("canonical_fc"), 3)))
    items["tableS5"] = values(fl)

    # ---- Fig. 5 / S4 event counts
    f5 = cons["fig5"]
    for t, iid in (("Liver", "fig5.counts"), ("BMM", "figS4")):
        fl = []
        for g in ("exclusion_ptc", "exclusion_noptc", "inclusion_ptc", "inclusion_noptc", "unregulated"):
            fl.append(field(f"{t}, {g.replace('_noptc', ' PTC-').replace('_ptc', ' PTC+')} events", pv["fig5"][t][g],
                            f5.get(f"{t}:{g}", {}).get("events")))
        fl.append(field("mm9 RefSeq exons", pv["fig5"]["refseq_exons"], cons["refseq_internal_exons"]))
        items[iid] = values(fl)

    # ---- pixel-scored panels. Pass mark: 90% of pixels within 3 px both ways, and always above the
    # best negative control (by at least one point), so a known-wrong series can never pass.
    def pixels(d):
        best = max(c["score"] for c in d["controls"])
        return {"method": "pixels", "pixels": dict(d, tolerance_px=3, dpi=150, threshold=round(min(0.999, max(0.90, best + 0.01)), 4))}

    for key in ("fig6", "fig7a"):
        items[key] = pixels(fg[key])
    for p in ("a", "b"):
        items[f"fig5.{p}"] = pixels(fg["fig5"][p])

    # ---- Fig. 7a / S5 position counts, Fig. 7b
    c7 = cons["fig7a"]
    items["figS5"] = values([
        field("BMM PTC+ positions", pv["fig7a"]["BMM"], c7.get("BMM", {}).get("positions")),
        field("Liver PTC+ positions", pv["fig7a"]["Liver"], c7.get("Liver", {}).get("positions")),
        field("Normal RefSeq STOP positions", pv["fig7a"]["RefSeq_STOP"], c7.get("RefSeq_STOP", {}).get("positions")),
    ])
    f7 = fg["fig7b"]
    fl = [field(f"{f7['groups'][i // 3]} {['TAA', 'TAG', 'TGA'][i % 3]} frequency (read off the figure)", round(f7["published"][i], 3),
                f7["ours"][i], {"abs": 0.02}) for i in range(18)]
    fl += [field("RefSeq transcript models", pv["fig7b"]["refseq_models"], st["models_with_stop"]),
           field("BMM PTC-inducing junctions (n)", pv["fig7b"]["BMM_n"], f7["n"]["BMM"]),
           field("Liver PTC-inducing junctions (n)", pv["fig7b"]["Liver_n"], f7["n"]["Liver"]),
           field("UGA preference, BMM PTC+ against exonic (Fisher, P < 0.05)", "significant",
                 "significant" if f7["fisher_p"]["BMM"] < 0.05 else "not significant"),
           field("UGA preference, liver PTC+ against exonic (Fisher, P < 0.05)", "significant",
                 "significant" if f7["fisher_p"]["Liver"] < 0.05 else "not significant")]
    items["fig7b"] = values(fl)

    # ---- Fig. S2 (bar heights read off the EPS)
    for p in ("a", "b"):
        d = fg["figS2"][p]
        fl = [field(f"bin {b}", round(pu, 1), o, {"abs": max(5.0, 0.1 * pu)}) for b, pu, o in zip(d["bins"], d["published"], d["ours"])]
        items[f"figS2.{p}"] = values(fl)

    # ---- conservation claims (Figs 5 and S4), Kolmogorov-Smirnov at the paper's threshold
    ks = cons.get("ks", {})

    def sig(key, thr=2.2e-16):
        k = ks.get(key)
        return None if k is None else ("P < 2.2e-16" if k["p"] < thr else f"P = {k['p']:.2g}")

    def more(key, a, b):
        k = ks.get(key)
        return None if k is None else ("yes" if k[a] > k[b] else "no")

    items["text.conservation"] = values([
        field("liver, flanking introns of excluded exons more conserved than unregulated skipping (KS)", "P < 2.2e-16",
              sig("Liver:exclusion_vs_unregulated_intron")),
        field("liver, excluded exons: regulated introns more conserved than unregulated", "yes",
              more("Liver:exclusion_vs_unregulated_intron", "regulated_mean", "unregulated_mean")),
        field("BMM, the same, even more pronounced: regulated introns more conserved than unregulated", "yes",
              more("BMM:exclusion_vs_unregulated_intron", "regulated_mean", "unregulated_mean")),
        field("liver, PTC+ exclusion exons more conserved than PTC- exons (KS)", "P < 2.2e-16", sig("Liver:exclusion_ptc_vs_noptc_exon")),
        field("liver, PTC- exclusion introns more conserved than PTC+ introns", "yes",
              more("Liver:exclusion_noptc_vs_ptc_intron", "noptc_mean", "ptc_mean")),
        field("liver, included exons: regulated introns more conserved than unregulated", "yes",
              more("Liver:inclusion_vs_unregulated_intron", "regulated_mean", "unregulated_mean")),
        field("liver, PTC- inclusion introns more conserved than PTC+ introns", "yes",
              more("Liver:inclusion_noptc_vs_ptc_intron", "noptc_mean", "ptc_mean")),
    ])

    # ---- Fig. 6 claims (no numbers in the text)
    f6 = an.get("fig6_claims", {})
    items["text.fig6"] = values([
        field("PTC+ fraction higher in liver than in BMM in every RPKM bin (KO and WT)", "yes", f6.get("liver_above_bmm_all_bins")),
        field("PTC+ fraction highest at low expression in each sample (bin 1 above the bins over 10 RPKM)", "yes", f6.get("low_expression_enriched")),
        field("liver KO above liver WT at low expression (1 RPKM)", "yes", f6.get("ko_above_wt_liver_bin1")),
        field("BMM KO above BMM WT at low expression (1 RPKM)", "yes", f6.get("ko_above_wt_bmm_bin1")),
    ])

    # ---- Table S5 claim on our run
    liver = an["tableS5"]["Liver"]
    with_asnmd = [g for g, v in liver.items() if v.get("canonical_fc") is not None]
    up = [g for g in with_asnmd if liver[g]["canonical_fc"] > 1.5]
    down = [g for g in with_asnmd if liver[g]["canonical_fc"] < 1 / 1.5]
    items["text.tableS5"] = values([
        field("liver splice factors with AS-NMD (of 25)", pv["text_s5"]["liver_factors_with_asnmd"], len(with_asnmd)),
        field("of these, deregulated more than 1.5-fold", pv["text_s5"]["deregulated_1_5"], len(up) + len(down)),
        field("up", pv["text_s5"]["up"], len(up)),
        field("down", pv["text_s5"]["down"], len(down)),
    ])

    # ---- checks
    items["port.ptc_distance"] = values([
        field(f"{x['gene']} (PTC upon {x['event']})", str(x["paper_distance"]), x["distance"] if x["status"] == "ptc" else x["status"])
        for x in port["ptc_distance_rows"]])
    items["port.tmm_edger"] = {"method": "check", "check": port["tmm_edger"]}
    items["text.arithmetic"] = {"method": "check", "check": port["arithmetic"]}
    with open(out_path, "w") as f:
        json.dump({"items": items}, f, indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:9])

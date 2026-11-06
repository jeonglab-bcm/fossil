"""Merge the run's numbers with the hand-written notes into results.json (paper2repro/results/v1).

usage: build_results.py RUN_DIR FIGURES_DIR PUBLISHED_DATA_JSON OUT_JSON

RUN_DIR holds ffl.json, toggle.json and haem.json (and their fits); FIGURES_DIR holds scores.json.
Labels, sources, assumptions and causes come from results_notes.json (written by hand); every
number comes from the run. Verdicts and the summary are computed by check_results.py --write.
"""
import json
import math
import subprocess
import sys
from datetime import date
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PV = json.loads((HERE / "params" / "published_values.json").read_text())
NOTES = json.loads((HERE.parent / "results_notes.json").read_text())
FIGOUT = "figure-reproduction/output"


def r(x, nd):
    return float(round(float(x), nd))


def dec(s):
    s = str(s)
    return len(s.split(".")[1]) if "." in s else 0


def at(expected, observed):
    """observed rounded to one more digit than the expected value prints."""
    return r(observed, dec(expected) + 1)


def yesno(b):
    return "yes" if b else "no"


def relerr(est, true):
    e = np.abs(np.array(est, float) - np.array(true, float)) / np.array(true, float)
    return float(e.mean() * 100)


class Items:
    def __init__(self):
        self.items = []

    def add(self, iid, kind, source, method, **kw):
        n = NOTES["items"].get(iid, {})
        it = {"id": iid, "label": n.get("label", iid), "kind": kind, "source": n.get("source", source),
              "method": method}
        it.update(kw)
        for k in ("assumptions", "cause"):
            if k in n:
                it[k] = n[k]
        if "exceptions" in n and "values" in it:
            it["values"]["exceptions"] = n["exceptions"]
        if "note" in n:
            it["note"] = n["note"]
        self.items.append(it)


def values(fields, tol=None):
    v = {"fields": fields}
    if tol:
        v["tolerance"] = tol
    return v


def pixels(s):
    return {"tolerance_px": 2, "dpi": 600, "published_near_ours": s["published_near_ours"],
            "ours_near_published": s["ours_near_published"], "threshold": s["threshold"],
            "controls": s["controls"], "element": s["class"]}


def main(run, figs, pubdata, out):
    run, figs = Path(run), Path(figs)
    F = json.loads((run / "ffl.json").read_text())
    T = json.loads((run / "toggle.json").read_text())
    H = json.loads((run / "haem.json").read_text())
    TF = json.loads((run / "toggle_fits.json").read_text())
    HF = json.loads((run / "haem_fits.json").read_text())
    S = json.loads((figs / "scores.json").read_text())
    PD = json.loads(Path(pubdata).read_text())
    I = Items()
    PX = S["pixels"]

    def fig_px(iid, fig, panel):
        I.add(iid, "figure", "reconstructed", "pixels", pixels=pixels(PX[panel]),
              outputs=[f"{FIGOUT}/{fig}_ours.png", f"{FIGOUT}/{fig}_overlay.png"])

    # ------------------------------------------------------------ Fig. 1 and the toggle switch
    I.add("fig1", "figure", "none", "none")
    tv = PV["toggle_true"]
    fm = PV["toggle_fig1h_modes"]
    names = ["alpha", "lambda", "kp", "hp", "km", "hm"]
    joint = list(T["joint"]["mean"].values())
    I.add("fig1.h", "figure", "reconstructed", "values",
          values=values([{"name": f"{n} posterior mean", "expected": fm[n], "observed": at(fm[n], v)}
                         for n, v in zip(names, joint)], {"rel": 0.02}))
    I.add("text.toggle_error", "value", "reconstructed", "values",
          values=values([{"name": "mean relative error of the posterior means (%)", "expected": "6.8",
                          "observed": r(T["joint_rel_error_mean"], 1)}], {"printed": True}))

    # ------------------------------------------------------------ FFL (Figs 2-4)
    fa = F["fig2a"]
    I.add("fig2.a", "figure", "reconstructed", "values",
          values=values([{"name": "gZ further from the deterministic series than gX", "expected": "yes",
                          "observed": yesno(fa["gZ"]["r"] < fa["gX"]["r"])},
                         {"name": "gZ further from the deterministic series than gY", "expected": "yes",
                          "observed": yesno(fa["gZ"]["r"] < fa["gY"]["r"])}]))
    I.add("fig2.b", "figure", "none", "none")
    I.add("fig2.c", "figure", "none", "none")
    fig_px("fig2.d", "fig2", "fig2.d")
    fig_px("fig2.d.and", "fig2", "fig2.d.and")
    w13 = PV["ffl_fig13"]
    I.add("supp.fig13", "value", "reconstructed", "values",
          values=values([{"name": "GENIE3 weight gX->gY", "expected": w13["w_gX->gY"], "observed": r(F["genie3"]["gX->gY"], 3)},
                         {"name": "GENIE3 weight gY->gX", "expected": w13["w_gY->gX"], "observed": r(F["genie3"]["gY->gX"], 3)},
                         {"name": "GENIE3 weight gX->gZ", "expected": w13["w_gX->gZ"], "observed": r(F["genie3"]["gX->gZ"], 3)},
                         {"name": "GENIE3 weight gY->gZ", "expected": w13["w_gY->gZ"], "observed": r(F["genie3"]["gY->gZ"], 3)},
                         {"name": "r(gX, gY)", "expected": w13["r_gX,gY"], "observed": r(F["corr"]["gX,gY"], 2)},
                         {"name": "r(gX, gZ)", "expected": w13["r_gX,gZ"], "observed": r(F["corr"]["gX,gZ"], 2)},
                         {"name": "r(gY, gZ)", "expected": w13["r_gY,gZ"], "observed": r(F["corr"]["gY,gZ"], 2)}],
                        {"printed": True}))
    ms = sorted(F["model_selection"], key=lambda t: -t["aic"])
    pub14 = PV["ffl_fig14"]
    pub_rank = sorted(pub14, key=lambda m: -float(pub14[m][0]))
    I.add("supp.fig14", "table", "reconstructed", "values",
          values=values([{"name": "best model by AIC", "expected": pub_rank[0], "observed": ms[0]["model"]},
                         {"name": "second model by AIC", "expected": pub_rank[1], "observed": ms[1]["model"]},
                         {"name": "third model by AIC", "expected": pub_rank[2], "observed": ms[2]["model"]}]
                        + [{"name": f"AIC {m}", "expected": pub14[m][0],
                            "observed": r(next(t["aic"] for t in F["model_selection"] if t["model"] == m), 0)}
                           for m in pub_rank]))
    lz = F["ti"]
    I.add("text.ffl_bayes_factor", "value", "reconstructed", "values",
          values=values([{"name": "R(OR/AND) > 100", "expected": "yes", "observed": yesno(F["log10_bf_or_vs_and"] > 2)},
                         {"name": "R(OR, gX+ gY- / OR, gX- gY+) > 100", "expected": "yes",
                          "observed": yesno(F["log10_bf_or_vs_inverted"] > 2)},
                         {"name": "log p(D|M) of OR, gX+ gY-", "expected": PV["ffl_log_evidence"]["or(gX+,gY-)"],
                          "observed": r(lz["or(gX+,gY-)"], 0)},
                         {"name": "log p(D|M) of OR, gX- gY+", "expected": PV["ffl_log_evidence"]["or(gX-,gY+)"],
                          "observed": r(lz["or(gX-,gY+)"], 0)}], {"printed": True}))
    I.add("text.ffl_error", "value", "reconstructed", "values",
          values=values([{"name": "mean relative error of the MAP estimates (%)", "expected": "17",
                          "observed": r(F["rel_error_uniform"], 1)}], {"printed": True}))
    I.add("text.ffl_error_informative", "value", "reconstructed", "values",
          values=values([{"name": "mean relative error with an informative prior on lambda (%)", "expected": "14.5",
                          "observed": r(F["rel_error_informative"], 1)}], {"printed": True}))
    I.add("text.ffl_ratio", "value", "reconstructed", "values",
          values=values([{"name": "posterior median of alpha / lambda", "expected": "400",
                          "observed": r(F["alpha_over_lambda"]["median"], 0)}], {"printed": True}))
    mu = list(F["map_uniform"].values())
    f3 = PV["ffl_fig3_modes"]
    I.add("fig3", "figure", "reconstructed", "values",
          values=values([{"name": f"{n} posterior mode", "expected": f3[n], "observed": at(f3[n], v)}
                         for n, v in zip(names, mu)]
                        + [{"name": "alpha / lambda", "expected": f3["ratio"], "observed": r(F["alpha_over_lambda"]["median"], 1)}],
                        {"rel": 0.02}))
    t4 = PV["ffl_table4_gZ"]
    mi = list(F["map_informative"].values())
    t4y = PV["ffl_table4_gY"]
    my = list(F["map_gY"].values())
    I.add("supp.table4", "table", "reconstructed", "values",
          values=values([{"name": f"gZ {n}", "expected": t4[n], "observed": at(t4[n], v)} for n, v in zip(names, mi)]
                        + [{"name": f"gY {n}", "expected": t4y[n], "observed": at(t4y[n], v)} for n, v in zip(names[:4], my)],
                        {"rel": 0.02}))
    for p in ("deletion", "knockdown", "simultaneous"):
        fig_px(f"fig4.{p}", "fig4", f"fig4.{p}")
    pt = F["perturbations"]
    I.add("text.fig4", "value", "reconstructed", "values",
          values=values([{"name": f"prediction fits the perturbed system ({p}; R^2 >= 0.8)", "expected": "yes",
                          "observed": yesno(pt[p]["r2"] >= 0.8)} for p in ("deletion", "knockdown", "simultaneous")]))

    # ------------------------------------------------------------ toggle switch (Figs 5-6)
    ev = T["geometry"]["eigenvalues"]
    nsig = int(sum(1 for i in range(len(ev) - 1) if ev[i] > 5 * ev[-1]))
    I.add("supp.fig6", "value", "reconstructed", "values",
          values=values([{"name": "significant diffusion-map eigenvalues", "expected": "4",
                          "observed": str(int(np.argmax(-np.diff(np.log(ev[:6]))) + 1))}]))
    I.add("fig5.left", "figure", "none", "none")
    for g in "ABCD":
        fig_px(f"fig5.g{g}", "fig5", f"fig5.g{g}")
    bars = PD["fig6.bars"]
    left = sorted([b for b in bars if abs(b[0] - 368.38) < 0.5], key=lambda b: b[1])
    right = sorted([b for b in bars if abs(b[0] - 446.0) < 0.5], key=lambda b: b[1])
    pub_scores = {}
    L = max(b[2] - b[0] for b in left)
    for b, m in zip(left, ["D-", "D+", "and(A+,D-)", "or(A+,D-)"]):
        pub_scores[m] = (b[2] - b[0]) / L
    for b, m in zip(right, ["A-", "and(A+,D+)", "or(A+,D+)"]):
        pub_scores[m] = (b[2] - b[0]) / L
    ours6 = {x["model"]: x["score"] for x in T["fig6"]}
    I.add("fig6.left", "figure", "reconstructed", "values",
          values=values([{"name": "best model", "expected": "and(A+,D-)", "observed": T["fig6_best"]}]
                        + [{"name": f"score {m}", "expected": f"{pub_scores[m]:.2f}", "observed": r(ours6[m], 3)}
                           for m in ["D-", "D+", "A-", "and(A+,D-)", "and(A+,D+)", "or(A+,D-)", "or(A+,D+)"] if m in pub_scores],
                        {"abs": 0.05}))
    a18 = sorted((x["aic"] for x in T["fig18"]), reverse=True)
    I.add("supp.fig18", "figure", "reconstructed", "values",
          values=values([{"name": "best model for gD", "expected": "and(A+,C-)", "observed": T["fig18_best"]},
                         {"name": "every other model at least 400 AIC units behind (paper: -589 against below -1000)",
                          "expected": "yes", "observed": yesno(a18[0] - a18[1] >= 400)}]))
    I.add("supp.wanderlust_dims", "value", "reconstructed", "values",
          values=values([{"name": "correlation of pseudo times, high against low dimension (%)", "expected": "92",
                          "observed": r(100 * T["wanderlust_low_vs_high"]["mean_corr"], 1)}], {"printed": True}))
    I.add("supp.robustness", "value", "none", "none")
    fig_px("fig6.right.top", "fig6", "fig6.top")
    fig_px("fig6.right.bottom", "fig6", "fig6.bottom")
    t6 = PV["toggle_table6"]
    I.add("supp.table6", "table", "reconstructed", "values",
          values=values([{"name": k, "expected": t6[k], "observed": r(T["table6"][k], 1)} for k in t6], {"printed": True}))
    t1 = PV["toggle_table1"]
    tb = T["table1"]
    I.add("supp.table1", "table", "reconstructed", "values",
          values=values([{"name": "low-dimensional, sigma 20", "expected": t1["low_20"], "observed": r(tb["20"]["low_mean"], 1)},
                         {"name": "high-dimensional, sigma 20", "expected": t1["high_20"], "observed": r(tb["20"]["high_mean"], 1)},
                         {"name": "low-dimensional, sigma 80", "expected": t1["low_80"], "observed": r(tb["80"]["low_mean"], 1)},
                         {"name": "high-dimensional, sigma 80", "expected": t1["high_80"], "observed": r(tb["80"]["high_mean"], 1)},
                         {"name": "low beats high at sigma 20", "expected": "yes", "observed": yesno(tb["20"]["low_mean"] < tb["20"]["high_mean"])},
                         {"name": "low beats high at sigma 80", "expected": "yes", "observed": yesno(tb["80"]["low_mean"] < tb["80"]["high_mean"])}],
                        {"printed": True}))
    ins3 = T["gC_inputs_0.3"]
    ins1 = T["gC_inputs_0.1"]
    sg = lambda d, g: {1: "+", -1: "-", 0: "?"}[d[g]["sign"]] if g in d else "none"
    I.add("supp.fig17", "value", "reconstructed", "values",
          values=values([{"name": "inputs of gC at w >= 0.3", "expected": "A,D", "observed": ",".join(sorted(ins3))},
                         {"name": "sign of gA on gC", "expected": "+", "observed": sg(ins3, "A")},
                         {"name": "sign of gD on gC", "expected": "-", "observed": sg(ins3, "D")},
                         {"name": "inputs of gC at w >= 0.1", "expected": "A,B,D", "observed": ",".join(sorted(ins1))}]))
    t7 = T["table7"]
    I.add("supp.table7", "table", "reconstructed", "values",
          values=values([{"name": "best model by BIC", "expected": "and(A+,D-)", "observed": T["table7_best_bic"]},
                         {"name": "best model by AIC", "expected": "and(or(A+,B-),D-)", "observed": T["table7_best_aic"]},
                         {"name": "log p(D|M) of and(A+,D-)", "expected": PV["toggle_table7_ti"]["and(A+,D-)"],
                          "observed": r(T["table7_ti"]["and(A+,D-)"], 4)},
                         {"name": "log p(D|M) of and(or(A+,B-),D-)", "expected": PV["toggle_table7_ti"]["and(or(A+,B-),D-)"],
                          "observed": r(T["table7_ti"]["and(or(A+,B-),D-)"], 4)},
                         {"name": "Bayes factor", "expected": PV["toggle_table7_ti"]["bayes_factor"],
                          "observed": r(min(T["table7_bayes_factor"], 1e300), 3)},
                         {"name": "Bayes factor favours and(A+,D-)", "expected": "yes", "observed": yesno(T["table7_bayes_factor"] > 1)}],
                        {"printed": True}))

    # ------------------------------------------------------------ haematopoiesis (Figs 7-9)
    q = H["qc"]
    hc = PV["haem_cells"]
    I.add("text.haem_cells", "value", "public_data", "values",
          values=values([{"name": "cells after quality control", "expected": hc["total"], "observed": q["cells_kept"]}]
                        + [{"name": f"{t} cells", "expected": hc[t], "observed": q["per_type"][t]}
                           for t in ("CLP", "GMP", "HSC", "LMPP", "PreMegE")]))
    I.add("fig7.a", "figure", "none", "none")
    I.add("supp.fig32", "value", "public_data", "values",
          values=values([{"name": "log10 sigma at the maximum of <d>", "expected": PV["haem_dimension_argmax"],
                          "observed": H["dimension_curve"]["argmax"]}], {"printed": True}))
    fig_px("fig7.b", "fig7", "fig7.b")
    pub_edges = json.loads((HERE / "params" / "published_networks.json").read_text())["fig7c_edges"]
    ours_edges = {(e["from"], e["to"]) for e in H["genie3"]["edges"]}
    I.add("fig7.c", "figure", "public_data", "values",
          values=values([{"name": f"{a} -> {b}", "expected": "yes", "observed": yesno((a, b) in ours_edges)} for a, b in pub_edges]
                        + [{"name": "edges with w > 0.08", "expected": str(len(pub_edges)), "observed": str(len(ours_edges))}]))
    fr = PV["haem_fig29_r"]
    I.add("supp.fig29", "value", "public_data", "values",
          values=values([{"name": f"r({k})", "expected": fr[k], "observed": r(H["fig29_r"][k], 4)} for k in fr], {"printed": True}))
    be = PV["haem_branch_error_pct"]
    bo = H["branch_clustering"]["branches"]
    I.add("supp.branch_errors", "value", "public_data", "values",
          values=values([{"name": f"{k} branch error (%)", "expected": be[k],
                          "observed": r(bo[k]["error_pct"], 2) if k in bo else "branch not found"} for k in be], {"printed": True}))
    sel = H["model_selection"]

    def best_eff(target, k=1):
        rows = sorted(sel[target]["table"], key=lambda t: -t["aic"])
        return rows[:k]

    def eff_str(row):
        return ",".join(row["effective"]) or "none"

    t8 = PV["haem_table8"]
    pub8 = sorted(t8, key=lambda m: -float(t8[m][0]))
    rows8 = sorted(sel["GATA2"]["table"], key=lambda t: -t["aic"])
    I.add("supp.table8", "table", "public_data", "values",
          values=values([{"name": "best GATA2 model by AIC", "expected": pub8[0], "observed": rows8[0]["model"]},
                         {"name": "worst GATA2 model by AIC", "expected": pub8[-1], "observed": rows8[-1]["model"]},
                         {"name": "effective inputs of the best model", "expected": "SCL+", "observed": eff_str(rows8[0])}]
                        + [{"name": f"AIC {m}", "expected": t8[m][0],
                            "observed": r(next(x["aic"] for x in sel["GATA2"]["table"] if x["model"] == m), 0)} for m in pub8]))
    for target, key in (("GFI1", "haem_table9_GFI1"), ("GFI1B", "haem_table9_GFI1B")):
        tp = PV[key]
        pubr = sorted(tp, key=lambda m: -float(tp[m][0]))
        rows = sorted(sel[target]["table"], key=lambda t: -t["aic"])
        I.add(f"supp.table9.{target}", "table", "public_data", "values",
              values=values([{"name": f"best {target} model by AIC", "expected": pubr[0], "observed": rows[0]["model"]},
                             {"name": f"worst {target} model by AIC", "expected": pubr[-1], "observed": rows[-1]["model"]}]
                            + [{"name": f"AIC {m}", "expected": tp[m][0],
                                "observed": r(next(x["aic"] for x in sel[target]["table"] if x["model"] == m), 0)} for m in pubr]))

    # Fig. 8: an edge is selected when it is an effective input of a model within 2 AIC units of the best
    def selected(target):
        rows = sorted(sel[target]["table"], key=lambda t: -t["aic"])
        top = rows[0]["aic"]
        eff = set()
        for x in rows:
            if x["aic"] >= top - 2:
                eff |= set(x["effective"])
                if len(x["effective"]) > 1 and x["model"].startswith("and"):
                    eff.add("and(" + ",".join(e[:-1] for e in x["effective"]) + ")")
        return eff
    s_g2, s_g1, s_g1b = selected("GATA2"), selected("GFI1"), selected("GFI1B")
    I.add("fig8", "figure", "public_data", "values",
          values=values([{"name": "SCL activates GATA2 (CLP)", "expected": "yes", "observed": yesno("SCL+" in s_g2)},
                         {"name": "GFI1 inhibits GATA2 (CLP)", "expected": "yes", "observed": yesno("GFI1-" in s_g2)},
                         {"name": "AND(GFI1, NFE2) on GATA2 (CLP)", "expected": "yes", "observed": yesno("and(GFI1,NFE2)" in s_g2)},
                         {"name": "GFI1B inhibits GFI1 (GMP)", "expected": "yes", "observed": yesno("GFI1B-" in s_g1)},
                         {"name": "GATA2 regulates GFI1 (GMP)", "expected": "no", "observed": yesno(any(e.startswith("GATA2") for e in s_g1))},
                         {"name": "GFI1 inhibits GFI1B (GMP)", "expected": "yes", "observed": yesno("GFI1-" in s_g1b)},
                         {"name": "GATA2 activates GFI1B (GMP)", "expected": "yes", "observed": yesno("GATA2+" in s_g1b)}]))
    for p in ("GATA2_SCL", "GATA2_GFI1", "GATA2_and", "GFI1_GFI1B", "GFI1B_GATA2", "GFI1B_GFI1"):
        fig_px(f"fig9.{p}", "fig9", f"fig9.{p}")
    cd = S["curves"]
    I.add("fig9.points", "figure", "public_data", "values",
          values=values([{"name": f"points in {p.split('.')[1]}", "expected": str(cd[p]["n_points_published"]),
                          "observed": str(cd[p]["n_points_ours"])} for p in ("fig9.GATA2_SCL", "fig9.GFI1_GFI1B", "fig9.GFI1B_GATA2")]))

    # ------------------------------------------------------------ arithmetic from the paper's own numbers
    t4v = [float(PV["ffl_table4_gZ"][n]) for n in names]
    tr = [PV["ffl_true"][n] for n in names]
    f3v = [float(PV["ffl_fig3_modes"][n]) for n in names]
    f1v = [float(PV["toggle_fig1h_modes"][n]) for n in names]
    t7l = PV["toggle_table7_ti"]
    rows7 = [l.split("\t") for l in (HERE / "params" / "supp_table7.tsv").read_text().splitlines()[1:]]
    nobs = [math.exp(2 * (1 + (float(b) - float(a)) / 6)) for m, b, a in rows7[:1]]
    I.add("text.arithmetic", "value", "papers_data", "values",
          values=values([
              {"name": "14.5% from supp. Table 4 (gZ)", "expected": "14.5", "observed": r(relerr(t4v, tr), 2)},
              {"name": "17% from the modes of Fig. 3", "expected": "17", "observed": r(relerr(f3v, tr), 1)},
              {"name": "6.8% from the posteriors of Fig. 1H", "expected": "6.8", "observed": r(relerr(f1v, [tv[n] for n in names]), 2)},
              {"name": "R > 100 from log p(D|M) = -385 and -400", "expected": "yes", "observed": yesno(math.exp(-385 + 400) > 100)},
              {"name": "Bayes factor 3.53 from log p(D|M) of supp. Table 7", "expected": t7l["bayes_factor"],
               "observed": r(math.exp(float(t7l["and(A+,D-)"]) - float(t7l["and(or(A+,B-),D-)"])), 4)},
              {"name": "Fig. 6 best model has score 1", "expected": "and(A+,D-)", "observed": max(pub_scores, key=pub_scores.get)},
              {"name": "AIC/BIC of supp. Fig. 14: best model is the OR gate gX+ gY-", "expected": "or(gX+,gY-)", "observed": pub_rank[0]},
          ], {"printed": True}))

    inputs = [{"name": "PMC4765871.1.pdf", "url": "https://pmc-oa-opendata.s3.amazonaws.com/PMC4765871.1/PMC4765871.1.pdf",
               "sha256": "4121f42f340cdad602e8c6fc92c9daf8e0e22ed7d2c89e787a9f20b93b60ee83"},
              {"name": "moignard2013_s3.xlsx",
               "url": "https://static-content.springer.com/esm/art%3A10.1038%2Fncb2709/MediaObjects/41556_2013_BFncb2709_MOESM81_ESM.xlsx",
               "sha256": "55fca1314dda722aff9e5f9cc9d4f9dfa58f1eb4b3a70564263e048e6e299be0"}]
    import platform
    import numba
    import scipy
    import sklearn
    res = {"schema": "paper2repro/results/v1", "paper": NOTES["paper"],
           "run": {"date": NOTES.get("date", str(date.today())),
                   "pipeline": "PMC4765871/figure-reproduction/main.nf",
                   "command": "nextflow run PMC4765871/figure-reproduction/main.nf --outdir results",
                   "inputs": inputs,
                   "environment": {"python": ".".join(platform.python_version_tuple()[:2]), "numpy": np.__version__, "scipy": scipy.__version__,
                                   "scikit-learn": sklearn.__version__, "numba": numba.__version__}},
           "session": {"ledger": "session/ledger.json"},
           "items": I.items}
    missing = set(NOTES["items"]) - {i["id"] for i in I.items}
    if missing:
        print("notes for unknown items:", sorted(missing), file=sys.stderr)
    Path(out).write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n")
    rc = subprocess.run([sys.executable, str(HERE / "check_results.py"), out, "--write", "--skip-files"]).returncode
    sys.exit(rc)


if __name__ == "__main__":
    main(*sys.argv[1:5])

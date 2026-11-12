"""Compare our simulation summaries with the values read off the published figures, and the claims
of the text with both.

  compare.py PUBLISHED_VALUES.json SUMMARY.json OUT.json

Figures 1-6 are Monte Carlo summaries of 100 replicates with unpublished seeds, so a bar or a curve
point cannot come back exactly: two runs of the same design differ by about sqrt(2) standard
errors. Each published value is a field, and its tolerance is fixed before comparing:

  tolerance = 3 * sqrt(SE_ours^2 + SE_paper^2) + one pixel of the published figure in data units

where SE_paper is taken equal to ours (same design, same number of replicates): for a mean IM, the
SD of the replicate means over sqrt(100); for a proportion p, sqrt(p(1 - p)/100) at the mean of the
two proportions (kept within 0.02-0.98). By chance, about 1 field in 370 falls outside.

Each figure also gets one consistency field: the sum of squared standardized differences
z = (ours - paper) / sqrt(SE_ours^2 + SE_paper^2 + pixel^2) over its distinct fields, against a
chi-square with as many degrees of freedom. "consistent" means p >= 0.01. The same test is run
with wrong inputs in place of ours (another LD model, another importance measure, another coding);
they must come out inconsistent, or the test could not tell.

Claims of the text (text.*) are computed twice: from the paper's own figure and table values
(text.arithmetic: does the statement follow from the paper's numbers?) and from our run (the
verdict).
"""

import json
import math
import sys

import numpy as np
from scipy.stats import chi2

from series import BAR_ORDER, HAP_ORDER, PRIMARY_RULE, R2, bar_series, curve, ld_model

N_REPS = 100
Z_TOL = 3.0


def se_prop(a, b, n=N_REPS):
    p = min(max((a + b) / 2, 0.02), 0.98)
    return math.sqrt(p * (1 - p) / n)


def field(name, pub, ours, se, px):
    tol = Z_TOL * math.sqrt(2) * se + px
    return {"name": name, "expected": f"{pub:.3f}", "observed": f"{ours:.3f}",
            "tolerance": {"abs": round(tol, 4)},
            "_z": (ours - pub) / math.sqrt(2 * se * se + px * px)}


def consistency(fields):
    zs = [f["_z"] for f in fields]
    stat = float(sum(z * z for z in zs))
    p = float(chi2.sf(stat, len(zs))) if zs else float("nan")
    return {"chi2": round(stat, 2), "df": len(zs), "p": p, "consistent": "yes" if p >= 0.01 else "no"}


# ---------------------------------------------------------------- bar figures

def bar_fields(fig, pub, vals, errs_se):
    px = 1.0 / abs(pub["row_per_unit"])
    out = []
    groups = pub["groups"]
    names = pub["series"]
    seen = set()
    for g, gl in enumerate(groups):
        for j, sname in enumerate(names):
            pv = pub["values"][g][j]
            ov = vals[g][j]
            if pv is None or ov is None:
                continue
            if fig in ("fig1", "fig4"):
                se = errs_se[g][j]
            else:
                se = se_prop(pv, ov)
            label = f"{'LD ' + gl if fig in ('fig1', 'fig2') else 'r2 ' + gl}: {sname}"
            f = field(label, pv, ov, se, px)
            # with 0 SNPs in LD, the n and r bars are the same LD model (n0): count it once
            key = (g, BAR_ORDER[j][0]) if fig in ("fig1", "fig2") and g == 0 else (g, j)
            f["_dup"] = key in seen
            seen.add(key)
            out.append(f)
    return out


def snp_bar_values(summ, fig, swap=None):
    """Our bar values, optionally with a wrong input swapped in (for the controls)."""
    vals, ses = [], []
    for k in range(5):
        gv, gs = [], []
        for combo, kind in BAR_ORDER:
            c, kd, kk = combo, kind, k
            if swap == "n_for_r":
                kd = "n" if kind == "r" else "r"
            elif swap == "im_swapped":
                c = combo.replace("IM0", "IMx").replace("IM1", "IM0").replace("IMx", "IM1")
            elif swap == "rf_swapped":
                c = combo.replace("RF0", "RFx").replace("RF1", "RF0").replace("RFx", "RF1")
            elif swap == "ld_shift":
                kk = min(k + 1, 4)
            s = summ["snp"][ld_model(kd, kk)][c]
            gv.append(s["mean_im"] if fig == "fig1" else s["above_noise"])
            gs.append(s["se_im"])
        vals.append(gv)
        ses.append(gs)
    return vals, ses


def hap_bar_values(summ, fig, swap=None, rule=PRIMARY_RULE):
    hap = summ["hap"][rule]
    vals, ses = [], []
    order = HAP_ORDER if swap != "coding_rotated" else ["HAP", "PRED", "SNP"]
    for i, r2 in enumerate(R2):
        rr = R2[min(i + 3, 10)] if swap == "r2_shift" else r2
        gv = [hap[rr][c]["mean_im"] if fig == "fig4" else hap[rr][c]["above_noise"] for c in order]
        gs = [hap[rr][c]["se_im"] for c in order]
        vals.append(gv)
        ses.append(gs)
    return vals, ses


def compare_bars(fig, pub, summ):
    if fig in ("fig1", "fig2"):
        vals, ses = snp_bar_values(summ, fig)
        controls = {"LD.nSNP models in place of LD.rSNP models": "n_for_r",
                    "IM0 and IM1 swapped": "im_swapped", "RF0 and RF1 swapped": "rf_swapped",
                    "one more SNP in LD": "ld_shift"}
        ctl_vals = {name: snp_bar_values(summ, fig, sw) for name, sw in controls.items()}
    else:
        vals, ses = hap_bar_values(summ, fig)
        controls = {"codings rotated (rHAP for rSNP, PRED for rHAP, rSNP for PRED)": "coding_rotated",
                    "r2 three steps higher": "r2_shift"}
        ctl_vals = {name: hap_bar_values(summ, fig, sw) for name, sw in controls.items()}
        alt = summ["hap"].get("equal_snp_freq")
        if alt and all(r2 in alt for r2 in R2):
            ctl_vals["haplotype frequencies by the other rule (equal SNP frequencies)"] = hap_bar_values(
                summ, fig, rule="equal_snp_freq")
    fields = bar_fields(fig, pub, vals, ses)
    uniq = [f for f in fields if not f["_dup"]]
    res = {"fields": fields, "consistency": consistency(uniq), "controls": []}
    for name, (cv, cs) in ctl_vals.items():
        cf = [f for f in bar_fields(fig, pub, cv, cs) if not f["_dup"]]
        within = sum(abs(float(f["observed"]) - float(f["expected"])) <= f["tolerance"]["abs"] for f in cf)
        kind = "near_miss" if "other rule" in name else "wrong_input"
        res["controls"].append({"name": name, "kind": kind, **consistency(cf), "fields_within": within,
                                "fields": len(cf)})
    return res


# ---------------------------------------------------------------- curve figures

def curve_value(xs, ys, X):
    if X < xs[0]:
        return 0.0
    if X > xs[-1]:
        return ys[-1]
    return ys[xs.index(X)]


def compare_curves(fig, pub, summ):
    out = {}
    for panel in pub["panels"]:
        pid = panel["id"]
        px_y = 1.0 / abs(panel["px"]["ay"])
        fields, ctl = [], {}
        names = list(panel["values"])
        for si, name in enumerate(names):
            xs, ys = curve(summ, fig, pid, name)
            # wrong input: the neighbouring series of the same panel
            other = names[(si + 1) % len(names)]
            oxs, oys = curve(summ, fig, pid, other)
            for X, pv in zip(panel["x"], panel["values"][name]):
                if pv is None:
                    continue
                ov = curve_value(xs, ys, X)
                se = se_prop(pv, ov)
                fields.append(field(f"{pid.split('.', 1)[1]} {name}, X={X}", pv, ov, se, px_y))
                cv = curve_value(oxs, oys, X)
                ctl.setdefault("neighbouring series in place of each series", []).append(
                    field("c", pv, cv, se_prop(pv, cv), px_y))
        out[pid] = (fields, ctl)
    return out


def compare_curve_items(fig, pub, summ):
    """Group the panels into items: fig3.a/b/c and fig6.a/b/c (left and right panels together)."""
    per_panel = compare_curves(fig, pub, summ)
    items = {}
    for pid, (fields, ctl) in per_panel.items():
        item = pid.rsplit(".", 1)[0]
        it = items.setdefault(item, {"fields": [], "ctl": {}})
        it["fields"] += fields
        for k, v in ctl.items():
            it["ctl"].setdefault(k, []).extend(v)
    out = {}
    for item, it in items.items():
        res = {"fields": it["fields"], "consistency": consistency(it["fields"]), "controls": []}
        for name, cf in it["ctl"].items():
            within = sum(abs(float(f["observed"]) - float(f["expected"])) <= f["tolerance"]["abs"] for f in cf)
            res["controls"].append({"name": name, "kind": "wrong_input", **consistency(cf),
                                    "fields_within": within, "fields": len(cf)})
        out[item] = res
    return out


# ---------------------------------------------------------------- claims of the text

def fig1_matrix(source):
    """5 x 8 matrix of mean IM in BAR_ORDER from the paper (dict) or ours (summary)."""
    return source


def r_series(m, combo):
    j = BAR_ORDER.index((combo, "r"))
    return [m[k][j] for k in range(5)]


def rng_(v):
    return max(v) - min(v)


def claims_from(f1, f2, f4, f5):
    """The text's claims about H4M4 as yes/no from Fig. 1/2 (5 x 8) and Fig. 4/5 (11 x 3) values."""
    c = {}
    dec = lambda v: all(b < a for a, b in zip(v, v[1:]))  # noqa: E731
    c["text.im0_decreases"] = dec(r_series(f1, "RF0:IM0")) and dec(r_series(f1, "RF1:IM0"))
    d = max(abs(a - b) for a, b in zip(r_series(f1, "RF0:IM0")[1:], r_series(f1, "RF1:IM0")[1:]))
    drop = r_series(f1, "RF0:IM0")[0] - r_series(f1, "RF0:IM0")[4]
    c["text.rf0_rf1_im0_close"] = d < 0.25 * drop
    c["text.rf0im1_steadier_than_rf1im1"] = rng_(r_series(f1, "RF0:IM1")) < rng_(r_series(f1, "RF1:IM1"))
    c["text.rf1im1_inflated"] = r_series(f1, "RF1:IM1")[4] > r_series(f1, "RF1:IM1")[0]
    # Discussion: SNPs in LD with noise SNPs have little effect (data not shown): the n series of
    # RF0:IM0 moves by less than a quarter of what the r series moves
    nser = [m[BAR_ORDER.index(("RF0:IM0", "n"))] for m in f1]
    c["text.ldn_little_effect"] = max(abs(v - nser[0]) for v in nser) < 0.25 * abs(r_series(f1, "RF0:IM0")[4] - nser[0])
    rngs = {k: rng_(r_series(f1, k)) for k in ("RF0:IM0", "RF0:IM1", "RF1:IM0", "RF1:IM1")}
    c["text.main_rf0im1_most_stable"] = min(rngs, key=rngs.get) == "RF0:IM1"
    rngs2 = {k: rng_(r_series(f2, k)) for k in ("RF0:IM0", "RF0:IM1", "RF1:IM0", "RF1:IM1")}
    c["text.fig2_rf1im0_most_stable"] = min(rngs2, key=rngs2.get) == "RF1:IM0"
    last = {k: r_series(f2, k)[4] for k in rngs2}
    c["text.fig2_rf1im1_best"] = (max(last, key=last.get) == "RF1:IM1"
                                  and r_series(f2, "RF1:IM1")[4] > r_series(f2, "RF1:IM1")[0])
    # Fig. 4: rHAP > PRED.rHAP > rSNP "in general" (at least 6 of the 11 r^2 levels), and the gap
    # between rHAP and rSNP narrows from r^2 = 0 to r^2 = 1
    order = sum(f4[i][1] > f4[i][2] > f4[i][0] for i in range(11))
    c["text.fig4_order"] = order >= 6 and (f4[0][1] - f4[0][0]) > (f4[10][1] - f4[10][0])
    c["text.fig4_rsnp_rises"] = f4[10][0] > f4[0][0] and f4[5][0] > f4[0][0]
    c["text.fig5_rsnp_rises"] = f5[10][0] > f5[0][0] and f5[5][0] > f5[0][0]
    # Discussion: predicted haplotypes perform between the risk SNPs and the risk haplotypes (Fig. 5)
    c["text.pred_between"] = sum(f5[i][0] <= f5[i][2] <= f5[i][1] for i in range(10)) >= 6
    return c


def claims_fig3(get):
    """Fig. 3 claims from a function get(panel, series, X) -> proportion or None."""
    c = {}
    ok_small, ok_large, n = True, True, 0
    for panel in ("fig3.a.left", "fig3.a.right"):
        for ld in ("r1", "r2", "r3", "r4"):
            a, b = get(panel, ld, 8), get(panel, "n0", 8)
            if a is not None and b is not None:
                ok_small &= a < b
                n += 1
            a, b = get(panel, ld, 30), get(panel, "n0", 30)
            if a is not None and b is not None:
                ok_large &= a >= b
                n += 1
    c["text.fig3_ld_low_then_high"] = (ok_small and ok_large) if n else None
    return c


def claims_fig3_rf(summ):
    """Fig. 3 bottom: for 1 and for 4 LD.rSNPs, RF0 beats RF1 (mean proportion over X = 4..40,
    averaged over IM0 and IM1)."""
    out = {}
    for k in (1, 4):
        snp = summ["snp"][f"r{k}"]
        m = {c: np.mean(snp[c]["top_any"][3:40]) for c in ("RF0:IM0", "RF0:IM1", "RF1:IM0", "RF1:IM1")}
        out[f"{k} LD.rSNP per rSNP"] = bool((m["RF0:IM0"] + m["RF0:IM1"]) > (m["RF1:IM0"] + m["RF1:IM1"]))
    return out


def other_model_claims(om):
    out = {}
    for model, lds in om.items():
        if not all(f"r{k}" in lds for k in range(1, 5)) or "n0" not in lds:
            continue
        ser = {c: [lds["n0" if k == 0 else f"r{k}"][c]["mean_im"] for k in range(5)]
               for c in ("RF0:IM0", "RF0:IM1", "RF1:IM0", "RF1:IM1")}
        dec = lambda v: all(b < a for a, b in zip(v, v[1:]))  # noqa: E731
        rngs = {k: rng_(v) for k, v in ser.items()}
        out[model] = {
            "text.im0_decreases": dec(ser["RF0:IM0"]) and dec(ser["RF1:IM0"]),
            "text.rf0im1_steadier_than_rf1im1": rngs["RF0:IM1"] < rngs["RF1:IM1"],
            "text.rf1im1_inflated": ser["RF1:IM1"][4] > ser["RF1:IM1"][0],
            "text.main_rf0im1_most_stable": min(rngs, key=rngs.get) == "RF0:IM1",
            "series": ser,
        }
    return out


TABLE4 = [  # SNP, genotypic p, allelic p (Table 4)
    ("rs2927477", 0.4483, 0.4122), ("rs4803759", 0.0833, 0.0242), ("rs4605275", 0.0962, 0.0291),
    ("rs8104483", 0.6459, 0.4007), ("rs4803767", 0.6459, 0.4007), ("rs10119", 0.0028, 0.0055),
    ("rs4420638", 2.651e-12, 7.73e-12), ("rs5158", 0.3015, 0.8121), ("rs3760627", 0.6852, 0.5458),
    ("rs16979595", 0.9526, 0.8689), ("rs7257916", 0.6859, 0.5471), ("rs10424046", 0.0106, 0.0038),
    ("rs1560725", 0.0507, 0.0466), ("rs11083758", 0.0474, 0.0134), ("rs3786507", 0.0374, 0.0396),
    ("rs2889490", 0.0252, 0.0094), ("rs10416445", 0.0187, 0.0065)]
TABLE3 = {"RF0:IM0": (0.1512, 9, 0.28, 3), "RF0:IM1": (0.1519, 9, 0.2803, 6),
          "RF1:IM0": (0.1436, 7, 0.3123, 4), "RF1:IM1": (0.3191, 11, 0.3123, 10)}


def ad_claims():
    missed = [s for s, g, a in TABLE4 if g > 0.05 and a > 0.05]
    d1 = {k: v[0] for k, v in TABLE3.items()}
    return {
        "n_top_snps": len(TABLE4), "missed_by_single_snp": len(missed), "missed": missed,
        "rs4420638_in_top11_all": all(v[1] <= 11 and v[3] <= 11 for v in TABLE3.values()),
        "rf0im0_lower_with_ld": TABLE3["RF0:IM0"][0] < TABLE3["RF0:IM0"][2],
        "rf1im1_highest_dataset1": max(d1, key=d1.get) == "RF1:IM1",
        "rf1im1_closest_to_no_ld": min(d1, key=lambda k: abs(d1[k] - TABLE3["RF0:IM0"][2])) == "RF1:IM1",
    }


def main():
    pubp, summp, outp = sys.argv[1:4]
    pub = json.load(open(pubp))
    summ = json.load(open(summp))
    res = {"tolerance_rule": f"{Z_TOL} combined SE + 1 px", "items": {}}
    for fig in ("fig1", "fig2", "fig4", "fig5"):
        res["items"][fig] = compare_bars(fig, pub[fig], summ)
    for fig in ("fig3", "fig6"):
        res["items"].update(compare_curve_items(fig, pub[fig], summ))
    # error bars of Figs 1 and 4: ratio of the published half-lengths to our standard errors
    eb = {}
    for fig in ("fig1", "fig4"):
        vals, ses = (snp_bar_values(summ, fig) if fig == "fig1" else hap_bar_values(summ, fig))
        ratios = [pub[fig]["errors"][g][j] / ses[g][j] for g in range(len(ses)) for j in range(len(ses[g]))
                  if pub[fig]["errors"][g][j] and ses[g][j] > 0]
        eb[fig] = {"median_ratio": float(np.median(ratios)), "q25": float(np.percentile(ratios, 25)),
                   "q75": float(np.percentile(ratios, 75)), "n": len(ratios)}
    res["error_bars"] = eb
    # claims
    p1, p2, p4, p5 = (pub[f]["values"] for f in ("fig1", "fig2", "fig4", "fig5"))
    o1, _ = snp_bar_values(summ, "fig1")
    o2, _ = snp_bar_values(summ, "fig2")
    o4, _ = hap_bar_values(summ, "fig4")
    o5, _ = hap_bar_values(summ, "fig5")
    paper = claims_from(p1, p2, p4, p5)
    ours = claims_from(o1, o2, o4, o5)

    def pub_get(panel, series, X):
        for p in pub["fig3"]["panels"]:
            if p["id"] == panel and X in p["x"]:
                return p["values"].get(series, [None] * len(p["x"]))[p["x"].index(X)]
        return None

    def our_get(panel, series, X):
        xs, ys = curve(summ, "fig3", panel, series)
        return curve_value(xs, ys, X)

    paper.update(claims_fig3(pub_get))

    # Consistency of Figs 5 and 6b: if a share s of replicates has all four risk haplotypes above
    # every noise SNP (Fig. 5), at least s has them in the top 4, and so in the top 5 (Fig. 6b).
    def f6b(series, X):
        for p in pub["fig6"]["panels"]:
            if p["id"] == "fig6.b.left" and X in p["x"]:
                return p["values"].get(series, [None] * len(p["x"]))[p["x"].index(X)]
        return None
    bound = []
    for i, r2 in enumerate(R2):
        v = f6b(f"r2={r2}", 5)
        if v is not None:
            bound.append({"r2": r2, "fig5_rhap": p5[i][1], "fig6b_top5": v, "consistent": v >= p5[i][1] - 0.05})
    res["fig5_fig6b_bound"] = bound
    paper["text.fig5_fig6b_consistent"] = all(b["consistent"] for b in bound) if bound else None
    ours.update(claims_fig3(our_get))
    ours["text.fig3_rf0_beats_rf1"] = claims_fig3_rf(summ)
    paper["text.fig3_rf0_beats_rf1"] = None  # the curves overlap in the published panels
    res["claims"] = {"paper": {k: (None if v is None else bool(v)) for k, v in paper.items()},
                     "ours": {k: (v if isinstance(v, dict) else bool(v)) for k, v in ours.items()},
                     "other_models": {m: {k: (bool(v) if k != "series" else v) for k, v in d.items()}
                                      for m, d in other_model_claims(summ.get("other_models", {})).items()},
                     "ad": ad_claims()}
    for it in res["items"].values():
        for f in it["fields"]:
            f.pop("_z", None)
            f.pop("_dup", None)
    # the same fields in a list keyed without dots, for the repository's tools/check_results.py
    res["item_list"] = [{"key": k.replace(".", ""), "fields": [{"observed": f["observed"]} for f in v["fields"]]}
                        for k, v in res["items"].items()]
    json.dump(res, open(outp, "w"), indent=1)


if __name__ == "__main__":
    main()

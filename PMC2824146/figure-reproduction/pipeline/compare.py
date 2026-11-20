"""Compare our run with the paper: tables and numbers at printed precision, every plotted point of
Figures 1 to 8 (read from the article's vector figures) within its Monte Carlo error, and the claims
in the text, each evaluated twice: on the paper's own figure values (arithmetic check) and on ours.

    python3 compare.py published_values.json targets.json summary.json comparison.json
"""

import json
import math
import sys

LEVELS = [5, 10, 25, 50, 75]
COEFS = ["X1", "X2", "X3", "X4", "X5", "X6", "X7", "X8d1", "X8d2"]
MI = ["MICE", "MICE_PMM", "MICE_PMM_notrans", "AREG", "MIX_notrunc"]
MI7 = ["MICE_PMM", "MICE_PMM_notrans", "AREG"]  # in Figs 7 and 8 under both mechanisms
NAMES = {"CC": "CC", "SI": "SI", "AREG": "aregImpute", "MICE": "MICE", "MICE_PMM": "MICE-PMM",
         "MICE_PMM_notrans": "MICE-PMM no transformation", "MIX_notrunc": "MIX no truncating",
         "NORM": "NORM", "MIX": "MIX"}
PAPER_REPS = 1000
QUANT_PT = 0.405  # the coordinate grid of the PDF figures, in points

# Printed values (paper text and tables)
TABLE1 = {"X1": ("53.05", "10.12"), "X2": ("1.16", "0.94"), "X3": ("3.35", "1.93"), "X4": ("3.35", "1.84"),
          "X5": ("0.36", "0.48"), "X6": ("0.58", "0.49"), "X7": ("0.88", "0.32"), "X8": ("3.27", "0.46")}
SKEW = {"X2": "2.87", "X3": "4.77", "X4": "3.07", "X8": "1.77"}
CORS = {"X1-X6": "0.77", "X3-X4": "0.39", "X2-X8": "0.33", "X5-X6": "0.28"}
LP = {"X1": "-0.0088", "X2": "0.051", "X3": "-0.0023", "X4": "0.00015", "X5": "-0.349", "X6": "0.225",
      "X7": "0.67", "X8d1": "0.223", "X8d2": "0.331"}
TABLE3 = {"X2|MX3": ["101.12", "45.5", "15.68", "5.50", "2.17"],
          "X5|MX2": ["42.04", "20.78", "7.41", "3.00", "1.51"],
          "X8|MX3": ["45.14", "14.23", "5.44", "1.92", "0.92"]}
FIG_QTY = {"fig2": "estimate", "fig3": "se", "fig4": "coverage", "fig5": "p_mean", "fig7": "estimate",
           "fig8": "coverage"}


def fmt(x, digits=6):
    return float(f"{x:.{digits}g}")


class Ours:
    def __init__(self, summary):
        self.s = summary
        self.truth = summary["truth"]["mean"]
        self.emp_se = summary["truth"]["empirical_se"]
        self.idx = {}
        for r in summary["summary"]:
            self.idx[(r["mechanism"], r["method"], round(100 * r["level"]), r["variable"], r["quantity"])] = r

    def get(self, mech, method, level, var, qty):
        if level == 0:
            r = self.idx.get(("NONE", "FULL", 0, var, qty))
        else:
            r = self.idx.get((mech, method, level, var, qty))
        return (r["value"], r.get("mcse"), r["reps"]) if r else (None, None, None)

    def val(self, mech, method, level, var, qty):
        return self.get(mech, method, level, var, qty)[0]


class Paper:
    """The paper's figure values, with the same accessor as Ours."""

    def __init__(self, pub):
        self.f = pub["figures"]
        p2, p3 = self.f["fig2"]["panels"], self.f["fig3"]["panels"]
        self.truth = {v: p2[v]["reference_lines"][1] for v in COEFS}
        self.emp_se = {v: p3[v]["reference_lines"][0] for v in COEFS}
        self.band = {v: (p2[v]["reference_lines"][2] - p2[v]["reference_lines"][0]) for v in COEFS}

    def val(self, mech, method, level, var, qty):
        fig = {("MAR", "estimate"): "fig2", ("MAR", "se"): "fig3", ("MAR", "coverage"): "fig4",
               ("MAR", "p_mean"): "fig5", ("MNAR", "estimate"): "fig7", ("MNAR", "coverage"): "fig8"}
        if var == "model":
            fig, panel, label = "fig6", qty, method
        else:
            fig = fig.get((mech, qty))
            if fig is None:
                return None
            panel = var
            label = method if fig not in ("fig7", "fig8") else f"{mech}:{method}"
        pts = self.f[fig]["panels"].get(panel, {}).get("series", {}).get(label)
        if pts is None and mech == "MAR" and qty == "estimate":
            pts = self.f["fig2"]["panels"][panel]["series"].get(method)
        if pts is None:
            return None
        d = {x: y for x, y in pts}
        return d.get(level)


# ---------------------------------------------------------------- tables and numbers


def values_items(t, ours):
    items = {}
    f = []
    for i, (v, (m, s)) in enumerate(TABLE1.items()):
        row = t["table1"][i]
        f.append({"name": f"{v} mean", "expected": m, "observed": fmt(row["mean"])})
        f.append({"name": f"{v} SD", "expected": s, "observed": fmt(row["sd"])})
    items["table1"] = {"fields": f}
    items["text.skewness"] = {"fields": [{"name": f"{v} skewness", "expected": e,
                                          "observed": fmt(t["skewness"][v]["b1"])} for v, e in SKEW.items()],
                              "other_definitions": {v: {k: fmt(x) for k, x in t["skewness"][v].items()} for v in SKEW}}
    cors = {c["pair"]: c for c in t["correlations"]}
    items["text.correlations"] = {"fields": [{"name": f"r({k})", "expected": e, "observed": fmt(cors[k]["raw"])}
                                             for k, e in CORS.items()],
                                  "transformed_scale": {k: fmt(cors[k]["transformed"]) for k in CORS}}
    items["lp"] = {"fields": [{"name": k, "expected": e, "observed": fmt(t["cox"]["efron"][k])} for k, e in LP.items()],
                   "breslow": {k: fmt(t["cox"]["breslow"][k]) for k in LP}}
    f = []
    for row in t["table3"]:
        for lev, e in zip(LEVELS, TABLE3[row["pair"]]):
            f.append({"name": f"{row['pair']} at {lev}%", "expected": e, "observed": fmt(row[f"pct{lev}"])})
    items["table3"] = {"fields": f}
    return items


def fig1_item(pub, t):
    out = []
    unmatched = []
    for name, p in pub["figures"]["fig1"]["panels"].items():
        h = t["histograms"][name]
        br, cn = h["breaks"], h["counts"]
        res = abs(p["y_map"][1]) * QUANT_PT  # one coordinate step, in counts
        for (x0, x1, y) in p["bars"]:
            j = min(range(len(cn)), key=lambda k: abs(br[k] - x0) + abs(br[k + 1] - x1))
            width = br[1] - br[0]
            if abs(br[j] - x0) > 0.1 * width or abs(br[j + 1] - x1) > 0.1 * width:
                unmatched.append(f"{name} bar {x0:.3g}-{x1:.3g}")
                continue
            out.append({"name": f"{name} [{br[j]:g}, {br[j + 1]:g}]", "expected": f"{y:.2f}",
                        "observed": cn[j], "tolerance": {"abs": round(0.5 + res, 3)}})
    return {"fields": out, "unmatched_bars": unmatched,
            "note": "Bar heights read from the vector figure; bars of one or two counts are too short to "
                    "read and are not listed."}


# ---------------------------------------------------------------- figures 2 to 8


def figure_items(pub, ours):
    items = {}
    for fig in ["fig2", "fig3", "fig4", "fig5", "fig6", "fig7", "fig8"]:
        F = pub["figures"][fig]
        fields, control_wrong, control_near, bias_rel = [], [], [], []
        for panel, p in F["panels"].items():
            ypt = abs(p["y_map"][1]) * QUANT_PT
            for label, pts in p["series"].items():
                mech, method = (label.split(":") if ":" in label else ("MAR", label))
                if fig == "fig6":
                    var, qty = "model", panel
                else:
                    var, qty = panel, FIG_QTY[fig]
                for x, y in pts:
                    v, m, n = ours.get(mech, method, x, var, qty)
                    if v is None:
                        continue
                    if qty == "coverage":
                        # binomial error at the paper's coverage, for both runs
                        pp = min(max(y / 100, 0.001), 0.999)
                        m_paper = 100 * math.sqrt(pp * (1 - pp) / PAPER_REPS)
                        m = 100 * math.sqrt(pp * (1 - pp) / n)
                    else:
                        m_paper = m * math.sqrt(n / PAPER_REPS) if m is not None else 0
                    tol = 3 * math.sqrt((m or 0) ** 2 + m_paper ** 2) + ypt
                    name = f"{panel} {NAMES.get(method, method)}{' ' + mech if fig in ('fig7', 'fig8') else ''} {x}%"
                    fields.append({"name": name, "expected": f"{y:.6g}", "observed": fmt(v),
                                   "tolerance": {"abs": float(f"{tol:.3g}")}})
                    # controls: the wrong mechanism, and the neighbouring missingness level
                    wm = {"MAR": "MNAR", "MNAR": "MAR"}[mech]
                    w = ours.val(wm, method, x, var, qty) if x > 0 else None
                    if w is not None:
                        # informative: our two mechanisms differ by more than the tolerance
                        control_wrong.append((abs(w - y) <= tol, abs(v - y) <= tol, abs(w - v) > tol))
                    if x > 0:
                        nx = {5: 10, 10: 25, 25: 50, 50: 75, 75: 50}[x]
                        nv = ours.val(mech, method, nx, var, qty)
                        py = dict((a, b) for a, b in pts).get(nx)
                        if nv is not None and py is not None:
                            # informative: the published curve moves by more than the tolerance
                            control_near.append((abs(nv - y) <= tol, abs(v - y) <= tol, abs(py - y) > tol))
                    if qty == "estimate":
                        pt = p["reference_lines"][1] if len(p["reference_lines"]) == 3 else None
                        if pt is not None:
                            bias_rel.append(abs((v - ours.truth[var]) - (y - pt)) <= tol)
        hits = sum(abs(float(f["expected"]) - f["observed"]) <= f["tolerance"]["abs"] for f in fields)
        item = {"fields": fields,
                "controls": [{"name": "wrong mechanism (MAR and MNAR swapped)", "kind": "wrong_input",
                              "matched": sum(c[0] for c in control_wrong), "of": len(control_wrong),
                              "informative_points": sum(c[2] for c in control_wrong),
                              "matched_informative": sum(c[0] for c in control_wrong if c[2]),
                              "ours_matched_informative": sum(c[1] for c in control_wrong if c[2])},
                             {"name": "neighbouring missingness level", "kind": "near_miss",
                              "matched": sum(c[0] for c in control_near), "of": len(control_near),
                              "informative_points": sum(c[2] for c in control_near),
                              "matched_informative": sum(c[0] for c in control_near if c[2]),
                              "ours_matched_informative": sum(c[1] for c in control_near if c[2])}],
                "matched": hits, "of": len(fields)}
        if bias_rel:
            item["bias_relative_to_own_truth"] = {"matched": sum(bias_rel), "of": len(bias_rel)}
        if any(p.get("anomalies") for p in F["panels"].values()):
            item["anomalies"] = {k: p["anomalies"] for k, p in F["panels"].items() if p.get("anomalies")}
        items[fig] = item
    # reference lines: true values (Fig. 2) and empirical SE (Fig. 3)
    f = []
    for v in COEFS:
        p2 = pub["figures"]["fig2"]["panels"][v]
        p3 = pub["figures"]["fig3"]["panels"][v]
        se = ours.emp_se[v]
        tol_m = 3 * se / math.sqrt(20000) * math.sqrt(2) + abs(p2["y_map"][1]) * QUANT_PT
        f.append({"name": f"{v} true value", "expected": f"{p2['reference_lines'][1]:.6g}",
                  "observed": fmt(ours.truth[v]), "tolerance": {"abs": float(f"{tol_m:.3g}")}})
        tol_s = 3 * se / math.sqrt(2 * 20000) * math.sqrt(2) + abs(p3["y_map"][1]) * QUANT_PT
        f.append({"name": f"{v} empirical SE", "expected": f"{p3['reference_lines'][0]:.6g}",
                  "observed": fmt(se), "tolerance": {"abs": float(f"{tol_s:.3g}")}})
    items["truth"] = {"fields": f}
    return items


# ---------------------------------------------------------------- claims in the text


def yn(b):
    return None if b is None else ("yes" if b else "no")


def first_level(cond):
    for lev in LEVELS:
        c = cond(lev)
        if c is None:
            return None
        if c:
            return str(lev)
    return "none"


def safe(f):
    try:
        return f()
    except TypeError:
        return None


def claims(src, truth, emp_se):
    """Every claim of the text that a figure or our run can answer, from one source of values."""
    V = src.val
    T, SE = truth, emp_se

    def pb(mech, m, lev, v):
        return 100 * (V(mech, m, lev, v, "estimate") - T[v]) / abs(T[v])

    def away(mech, m, lev, v):
        return abs(V(mech, m, lev, v, "estimate") - T[v]) > 0.5 * SE[v]

    c = {}
    # Figure 2 (MAR coefficients)
    c["text.fig2"] = {
        "CC within 0.5 SE at every level, all covariates": safe(lambda: yn(all(
            not away("MAR", "CC", l, v) for l in LEVELS for v in COEFS))),
        "SI more than 0.5 SE away for X2, X3 and X4 from 25%": safe(lambda: yn(all(
            away("MAR", "SI", l, v) for l in (25, 50, 75) for v in ("X2", "X3", "X4")))),
        "Most MI more than 0.5 SE away for X2, X3 and X4 from 25%": safe(lambda: yn(all(
            sum(away("MAR", m, l, v) for m in MI) >= 3 for l in (25, 50, 75) for v in ("X2", "X3", "X4")))),
    }
    for v in ("X2", "X3"):
        for m in MI:
            c["text.fig2"][f"{v} {NAMES[m]}: first level with bias over 10%"] = safe(
                lambda v=v, m=m: first_level(lambda l: abs(pb("MAR", m, l, v)) > 10))
    c["text.fig2"]["X5 bias over 10% at 50% with every MI"] = safe(lambda: yn(all(
        abs(pb("MAR", m, 50, "X5")) > 10 for m in MI)))
    for v in ("X1", "X6"):
        c["text.fig2"][f"{v} bias over 10% at 75% with MICE-PMM no transformation"] = safe(
            lambda v=v: yn(abs(pb("MAR", "MICE_PMM_notrans", 75, v)) > 10))
    c["text.fig2"]["X7, X8 dummies: bias within 10% at every level with every MI"] = safe(lambda: yn(all(
        abs(pb("MAR", m, l, v)) <= 10 for m in MI for l in LEVELS for v in ("X7", "X8d1", "X8d2"))))
    for v in ("X2", "X3", "X4"):
        c["text.fig2"][f"{v}: MICE-PMM no transformation least biased MI at 75%"] = safe(lambda v=v: yn(
            min(MI, key=lambda m: abs(V("MAR", m, 75, v, "estimate") - T[v])) == "MICE_PMM_notrans"))
    for v in ("X1", "X5", "X6"):
        c["text.fig2"][f"{v}: MICE-PMM no transformation most biased MI at 75%"] = safe(lambda v=v: yn(
            max(MI, key=lambda m: abs(V("MAR", m, 75, v, "estimate") - T[v])) == "MICE_PMM_notrans"))
    # Figure 3 (SE)
    c["text.fig3"] = {}
    for v in ("X2", "X3", "X5", "X8d1", "X8d2"):
        c["text.fig3"][f"{v}: every MI SE between SI and CC at 25 to 75%"] = safe(lambda v=v: yn(all(
            V("MAR", "SI", l, v, "se") <= V("MAR", m, l, v, "se") <= V("MAR", "CC", l, v, "se")
            for m in MI for l in (25, 50, 75))))
    for v in ("X1", "X4", "X6", "X7"):
        c["text.fig3"][f"{v}: CC SE rises by over 10% at 75%, SI and MI within 10% of full data"] = safe(
            lambda v=v: yn(V("MAR", "CC", 75, v, "se") > 1.1 * V("MAR", "CC", 0, v, "se") and all(
                abs(V("MAR", m, l, v, "se") / V("MAR", "CC", 0, v, "se") - 1) <= 0.1
                for m in ["SI"] + MI for l in LEVELS)))
    # Figure 4 (coverage)
    c["text.fig4"] = {
        "CC coverage 91 to 99% at every level, all covariates": safe(lambda: yn(all(
            91 <= V("MAR", "CC", l, v, "coverage") <= 99 for l in LEVELS for v in COEFS))),
    }
    for v in ("X2", "X3"):
        c["text.fig4"][f"SI coverage for {v} at 10% (about 90%)"] = safe(lambda v=v: V("MAR", "SI", 10, v, "coverage"))
    for v in ("X2", "X4"):
        for m in MI:
            c["text.fig4"][f"{v} {NAMES[m]}: coverage below 90% at 75%"] = safe(
                lambda v=v, m=m: yn(V("MAR", m, 75, v, "coverage") < 90))
    c["text.fig4"]["X2 MICE-PMM no transformation coverage at 75%"] = safe(
        lambda: V("MAR", "MICE_PMM_notrans", 75, "X2", "coverage"))
    for m in MI:
        c["text.fig4"][f"X3 {NAMES[m]}: first level with coverage below 90%"] = safe(
            lambda m=m: first_level(lambda l: V("MAR", m, l, "X3", "coverage") < 90))
    # Figure 5 (significance)
    c["text.fig5"] = {
        "CC X8 dummy 2: first level with p over 0.05": safe(lambda: first_level(
            lambda l: V("MAR", "CC", l, "X8d2", "p_mean") > 0.05)),
        "CC X5: first level with p over 0.05": safe(lambda: first_level(
            lambda l: V("MAR", "CC", l, "X5", "p_mean") > 0.05)),
        "CC X7: first level with p over 0.05": safe(lambda: first_level(
            lambda l: V("MAR", "CC", l, "X7", "p_mean") > 0.05)),
        "SI and MI: no covariate changes significance at 5%": safe(lambda: yn(all(
            (V("MAR", m, l, v, "p_mean") < 0.05) == (V("MAR", "CC", 0, v, "p_mean") < 0.05)
            for m in ["SI"] + MI for l in LEVELS for v in COEFS))),
    }
    # Figure 6 (model performance)
    c["text.fig6"] = {
        "LR test p below 0.01 for every method and level": safe(lambda: yn(all(
            V("MAR", m, l, "model", "lr_p") < 0.01 for m in ["CC", "SI"] + MI for l in LEVELS))),
        "At 50%: MICE has the smallest LR p of the MI methods": safe(lambda: yn(
            min(MI, key=lambda m: V("MAR", m, 50, "model", "lr_p")) == "MICE")),
        "At 50%: MIX no truncating has the largest LR p of the MI methods": safe(lambda: yn(
            max(MI, key=lambda m: V("MAR", m, 50, "model", "lr_p")) == "MIX_notrunc")),
        "R2 lower at 75% than with full data, SI and every MI": safe(lambda: yn(all(
            V("MAR", m, 75, "model", "r2") < V("MAR", "CC", 0, "model", "r2") for m in ["SI"] + MI))),
        "D lower at 75% than with full data, SI and every MI": safe(lambda: yn(all(
            V("MAR", m, 75, "model", "d") < V("MAR", "CC", 0, "model", "d") for m in ["SI"] + MI))),
        "At 75%: MICE-PMM no transformation and aregImpute have the highest R2 of the MI methods": safe(
            lambda: yn(set(sorted(MI, key=lambda m: -V("MAR", m, 75, "model", "r2"))[:2])
                       == {"MICE_PMM_notrans", "AREG"})),
        "2-year survival within 0.02 of full data, every method and level": safe(lambda: yn(all(
            abs(V("MAR", m, l, "model", "surv") - V("MAR", "CC", 0, "model", "surv")) <= 0.02
            for m in ["CC", "SI"] + MI for l in LEVELS))),
    }
    # Figures 7 and 8 (MNAR against MAR)
    c["text.mnar"] = {}
    for v in ("X3", "X4"):
        c["text.mnar"][f"MNAR {v}: more than 0.5 SE away from 25% with every MI shown"] = safe(lambda v=v: yn(all(
            away("MNAR", m, l, v) for m in MI7 + ["MICE"] for l in (25, 50, 75))))
        c["text.mnar"][f"MAR {v}, MICE-PMM no transformation: first level more than 0.5 SE away"] = safe(
            lambda v=v: first_level(lambda l: away("MAR", "MICE_PMM_notrans", l, v)))
        c["text.mnar"][f"{v} further from the truth under MNAR than MAR at 75%, every MI"] = safe(lambda v=v: yn(all(
            abs(V("MNAR", m, 75, v, "estimate") - T[v]) > abs(V("MAR", m, 75, v, "estimate") - T[v]) for m in MI7)))
    for v in ("X2", "X5"):
        c["text.mnar"][f"{v} closer to the truth under MNAR than MAR at 75%, every MI"] = safe(lambda v=v: yn(all(
            abs(V("MNAR", m, 75, v, "estimate") - T[v]) < abs(V("MAR", m, 75, v, "estimate") - T[v]) for m in MI7)))
    for v in ("X2", "X3", "X4"):
        c["text.mnar"][f"{v} coverage lower under MNAR than MAR at 75%, every MI"] = safe(lambda v=v: yn(all(
            V("MNAR", m, 75, v, "coverage") < V("MAR", m, 75, v, "coverage") for m in MI7)))
    # Abstract and conclusions
    c["text.main"] = {
        "MICE-PMM no transformation the least biased MI for X2 and X3 at 25 and 50% (MAR)": safe(lambda: yn(all(
            min(MI, key=lambda m: abs(V("MAR", m, l, v, "estimate") - T[v])) == "MICE_PMM_notrans"
            for v in ("X2", "X3") for l in (25, 50)))),
        "MICE-PMM no transformation within 10% bias for X2 and X3 at 25% (MAR)": safe(lambda: yn(all(
            abs(pb("MAR", "MICE_PMM_notrans", 25, v)) <= 10 for v in ("X2", "X3")))),
        "MICE-PMM no transformation more than 0.5 SE away for X2 or X3 at 50% (MAR)": safe(lambda: yn(any(
            away("MAR", "MICE_PMM_notrans", 50, v) for v in ("X2", "X3")))),
        "MICE-PMM no transformation more than 0.5 SE away for X2 or X3 at 50% (MCAR)": safe(lambda: yn(any(
            away("MCAR", "MICE_PMM_notrans", 50, v) for v in ("X2", "X3")))),
        "MICE-PMM no transformation more than 0.5 SE away for X2 or X3 at 50% (combined)": safe(lambda: yn(any(
            away("COMBINED", "MICE_PMM_notrans", 50, v) for v in ("X2", "X3")))),
        "MNAR: every MI more than 0.5 SE away for X3 from 25%": safe(lambda: yn(all(
            away("MNAR", m, l, "X3") for m in MI7 + ["MICE"] for l in (25, 50, 75)))),
    }
    # Other mechanisms and NORM/MIX (text only)
    c["text.other"] = {
        "MCAR: every estimate within 0.25 SE of MAR": safe(lambda: yn(all(
            abs(V("MCAR", m, l, v, "estimate") - V("MAR", m, l, v, "estimate")) <= 0.25 * SE[v]
            for m in ["CC", "SI"] + MI for l in LEVELS for v in COEFS))),
        "Combined: every estimate within 0.25 SE of MAR": safe(lambda: yn(all(
            abs(V("COMBINED", m, l, v, "estimate") - V("MAR", m, l, v, "estimate")) <= 0.25 * SE[v]
            for m in ["CC", "SI"] + MI for l in LEVELS for v in COEFS))),
        "NORM within 0.1 SE of MICE for every estimate (MAR)": safe(lambda: yn(all(
            abs(V("MAR", "NORM", l, v, "estimate") - V("MAR", "MICE", l, v, "estimate")) <= 0.1 * SE[v]
            for l in LEVELS for v in COEFS))),
        "MIX within 0.1 SE of MICE for every estimate (MAR)": safe(lambda: yn(all(
            abs(V("MAR", "MIX", l, v, "estimate") - V("MAR", "MICE", l, v, "estimate")) <= 0.1 * SE[v]
            for l in LEVELS for v in COEFS))),
    }
    return c


# what the text says, for each claim field
EXPECTED = {
    "first level with bias over 10%": lambda name: "50" if "no transformation" in name else "25",
    "first level with coverage below 90%": lambda name: "50" if ("no transformation" in name or "aregImpute" in name) else "25",
}


def expected_for(item, name):
    for key, fn in EXPECTED.items():
        if name.endswith(key):
            return fn(name)
    if name.startswith("X2 MICE-PMM no transformation: coverage below 90%"):
        return "no"
    if name == "X2 MICE-PMM no transformation coverage at 75%":
        return "93"
    if name.startswith("SI coverage for"):
        return "90"
    if name == "CC X8 dummy 2: first level with p over 0.05":
        return "25"
    if name in ("CC X5: first level with p over 0.05", "CC X7: first level with p over 0.05"):
        return "50"
    if "first level more than 0.5 SE away" in name:
        return "50"
    return "yes"


def tolerance_for(name):
    if name.startswith("SI coverage for"):
        return {"abs": 3}  # "around 90%"
    if name.endswith("coverage at 75%"):
        return {"printed": True}
    return None


def claim_items(paper_c, ours_c, mechs_run):
    items = {}
    arithmetic = {"back": 0, "checked": 0, "not_back": []}
    for item, fields in ours_c.items():
        out = []
        for name, obs in fields.items():
            exp = expected_for(item, name)
            pv = paper_c.get(item, {}).get(name)
            f = {"name": name, "expected": exp,
                 "observed": (fmt(obs, 4) if isinstance(obs, float) else obs)}
            tol = tolerance_for(name)
            if tol:
                f["tolerance"] = tol
            if pv is not None:
                f["paper_figures_give"] = fmt(pv, 4) if isinstance(pv, float) else pv
                arithmetic["checked"] += 1
                ok = (abs(float(pv) - float(exp)) <= (tol or {}).get("abs", 0.5 if tol else 0) + 1e-9
                      if isinstance(pv, float) else pv == exp)
                if ok:
                    arithmetic["back"] += 1
                else:
                    arithmetic["not_back"].append(f"{item}: {name} (figures give {f['paper_figures_give']})")
            if obs is None:
                f["observed"] = "not run"
            out.append(f)
        exc = []
        for f in out:
            pv = f.get("paper_figures_give")
            if pv is None or f["observed"] == "not run":
                continue
            def same(a, b, tol=f.get("tolerance")):
                if isinstance(a, float) or isinstance(b, float):
                    allowed = (tol or {}).get("abs", 0) + (0.5 if (tol or {}).get("printed") else 0)
                    return abs(float(a) - float(b)) <= allowed + 1e-9
                return a == b
            if not same(pv, f["expected"]) and not same(f["observed"], f["expected"]):
                exc.append({"field": f["name"], "category": "paper_error",
                            "evidence": f"The paper's own figure values give {pv}, not the text's {f['expected']}; ours give {f['observed']}"})
        items[item] = {"fields": out}
        if exc:
            items[item]["exceptions"] = exc
    return items, arithmetic


def main():
    pub = json.load(open(sys.argv[1]))
    t = json.load(open(sys.argv[2]))
    s = json.load(open(sys.argv[3]))
    ours = Ours(s)
    paper = Paper(pub)
    items = values_items(t, ours)
    items["fig1"] = fig1_item(pub, t)
    items.update(figure_items(pub, ours))
    # censoring and the missingness design (MAR, our run)
    cens = ours.val("NONE", "FULL", 0, "model", "censored")
    items["text.censoring"] = {"fields": [{"name": "censored (%)", "expected": "35",
                                           "observed": fmt(100 * cens, 4), "tolerance": {"printed": True}}]}
    f = []
    for lev in LEVELS:
        inc, inc_se, _ = ours.get("MCAR", "CC", lev, "design", "incomplete")
        if inc is None:
            continue
        f.append({"name": f"incomplete cases at {lev}% (MCAR)", "expected": str(lev),
                  "observed": fmt(100 * inc, 4), "tolerance": {"abs": float(f"{300 * (inc_se or 0):.3g}")}})
        for k, e in [("miss_X3", "70"), ("miss_X2", "55"), ("miss_X5", "20"), ("miss_X8", "10"),
                     ("both_X2X3", "35"), ("both_X5X2", "10"), ("both_X8X3", "5")]:
            v, se, _ = ours.get("MCAR", "CC", lev, "design", k)
            f.append({"name": f"{k.replace('miss_', '').replace('both_', 'both ')} share of incomplete at {lev}% (MCAR)",
                      "expected": e, "observed": fmt(100 * v / inc, 4),
                      "tolerance": {"abs": float(f"{300 * (se or 0) / inc:.3g}")}})
    items["text.design"] = {"fields": f}
    pc = claims(paper, paper.truth, paper.emp_se)
    oc = claims(ours, ours.truth, ours.emp_se)
    ci, arith = claim_items(pc, oc, None)
    items.update(ci)
    item_list = [dict({"key": k.replace(".", ""), "id": k, "fields": v["fields"]},
                      **({"matched": v["matched"], "of": v["of"]} if "matched" in v else {}))
                 for k, v in items.items()]
    res = {"items": items, "item_list": item_list, "arithmetic": arith,
           "truth": {"ours": ours.truth, "ours_empirical_se": ours.emp_se, "paper_figures": paper.truth,
                     "paper_figures_empirical_se": paper.emp_se},
           "replicates": s["replicates"]}
    json.dump(res, open(sys.argv[4], "w"), indent=1)
    for k, v in items.items():
        if "fields" in v:
            n = len(v["fields"])
            print(f"{k:22s} {n:4d} fields", v.get("matched", ""), v.get("controls", "") and
                  [(c["kind"], c["matched"], c["of"], c.get("ours_matched_informative"),
                    c.get("matched_informative"), c.get("informative_points")) for c in v["controls"]])
    print("arithmetic", arith["back"], "of", arith["checked"])
    for x in arith["not_back"]:
        print("  not back:", x)


if __name__ == "__main__":
    main()

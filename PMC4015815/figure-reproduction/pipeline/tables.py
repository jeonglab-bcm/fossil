"""Table 1 rows of this study, Figure 3 means and the claims in the text, from the sweep outputs.

usage: tables.py DR_CSV DT_CSV|- WEIGHTS_DR WEIGHTS_DT|- OUT_JSON

Everything here is "ours" (our run), except the block "arithmetic", which applies the same
formulas to the paper's own Table 1 to show that we compute each claim the way the paper does.
"""
import csv
import json
import sys

import numpy as np

# Paper, Table 1 (average ROC and ROC50 over 54 families), as printed.
TABLE1 = {
    "SVM-DR": ("0.919", "0.715"), "Monomer-dist": ("0.919", "0.508"),
    "SVM-LA": ("0.925", "0.649"), "SVM-Pairwise": ("0.901", "0.399"),
    "SVM-DT": ("0.948", "0.800"), "SVM-Top-n-gram": ("0.907", "0.696"),
    "SVM-Top-n-gram-LSA": ("0.939", "0.767"), "SVM-PDT-Profile": ("0.950", "0.740"),
    "PseAACIndex-Porfile": ("0.922", "0.712"), "BioSVM-2L": ("0.927", "0.888"),
    "HHSearch": ("0.915", "0.990"),
}
SEQUENCE = ["Monomer-dist", "SVM-LA", "SVM-Pairwise"]
PROFILE = ["SVM-Top-n-gram", "SVM-Top-n-gram-LSA", "SVM-PDT-Profile", "PseAACIndex-Porfile",
           "BioSVM-2L", "HHSearch"]


def load(path):
    rows = list(csv.DictReader(open(path)))
    by = {}
    for r in rows:
        by.setdefault(int(r["dmax"]), {})[r["family"]] = (float(r["roc"]), float(r["roc50"]))
    return by


def means(by):
    return {d: (float(np.mean([v[0] for v in f.values()])), float(np.mean([v[1] for v in f.values()])),
                len(f)) for d, f in sorted(by.items())}


def comparisons(method, roc, roc50, table):
    """The paper's comparison sentences, evaluated with the given ROC values for `method`."""
    t = {k: (float(a), float(b)) for k, (a, b) in table.items()}
    if method == "SVM-DR":
        # The paper's Table 1 ties SVM-DR and Monomer-dist at ROC 0.919, so "outperforms" can
        # only rest on ROC50 with ROC not lower; we test it that way for both methods.
        return {
            "beats Monomer-dist (ROC50, ROC not lower)":
                "yes" if roc50 > t["Monomer-dist"][1] and roc >= t["Monomer-dist"][0] else "no",
            "beats SVM-Pairwise (ROC50, ROC not lower)":
                "yes" if roc50 > t["SVM-Pairwise"][1] and roc >= t["SVM-Pairwise"][0] else "no",
            "within 1 point of SVM-LA (ROC)": "yes" if abs(roc - t["SVM-LA"][0]) <= 0.01 else "no",
        }
    others = [k for k in PROFILE if k != "SVM-PDT-Profile"]
    return {
        "beats every other profile method but SVM-PDT-Profile (ROC)":
            "yes" if all(roc > t[k][0] for k in others) else "no",
        "below SVM-PDT-Profile (ROC)": "yes" if roc < t["SVM-PDT-Profile"][0] else "no",
    }


def weight_claims(w):
    out = {}
    for pair in ("G,G", "L,L"):
        v = np.array(w["weights"][pair])
        d0, rest = v[0], v[1:]
        out[pair] = {
            "composition_weight_d0": round(float(d0), 3),
            "d0_largest_magnitude": "yes" if abs(d0) > np.abs(rest).max() else "no",
            "share_positive_d1_150": round(float(np.mean(rest > 0)), 4),
            "mean_abs_d1_50": round(float(np.abs(rest[:50]).mean()), 3),
            "mean_abs_d101_150": round(float(np.abs(rest[100:]).mean()), 3),
            "ladder (mean |w| at d 1-50 above d 101-150)":
                "yes" if np.abs(rest[:50]).mean() > np.abs(rest[100:]).mean() else "no",
        }
    top = [tuple(p[:2]) for p in w["top_pairs"][:2]]
    out["top_two_pairs"] = [f"({a},{b})" for a, b in top]
    out["top_two_are_GG_LL"] = "yes" if set(top) == {("G", "G"), ("L", "L")} else "no"
    l2 = np.array(w["l2_first_second"])
    A = w["alphabet"]
    order = np.argsort(-l2.ravel())
    rank = {(A[k // 20], A[k % 20]): i + 1 for i, k in enumerate(order)}
    out["rank_GG"] = rank[("G", "G")]
    out["rank_LL"] = rank[("L", "L")]
    out["l2_max"] = round(float(l2.max()), 2)
    return out


def main(dr_csv, dt_csv, wdr, wdt, out):
    res = {"table1_published": TABLE1}
    dr = load(dr_csv)
    dt = load(dt_csv) if dt_csv != "-" else None
    rows = list(csv.DictReader(open(dr_csv)))
    res["benchmark"] = {"families": len({r["family"] for r in rows}),
                        # some families leave sequences out (code 0); the largest split uses all
                        "sequences": max(int(r["n_train"]) + int(r["n_test"]) for r in rows)}
    res["fig3"] = {"SVM-DR": {str(d): [round(a, 6), round(b, 6), n] for d, (a, b, n) in means(dr).items()}}
    if dt:
        res["fig3"]["SVM-DT"] = {str(d): [round(a, 6), round(b, 6), n] for d, (a, b, n) in means(dt).items()}
    t1 = {}
    for name, by in (("SVM-DR", dr), ("SVM-DT", dt)):
        if by is None or 150 not in by:
            continue
        roc, roc50, n = means(by)[150]
        t1[name] = {"roc": round(roc, 6), "roc50": round(roc50, 6), "families": n,
                    "roc_3dp": f"{roc:.3f}", "roc50_3dp": f"{roc50:.3f}",
                    "family_2.5.1.3_roc": by[150]["2.5.1.3"][0],
                    "comparisons": comparisons(name, roc, roc50, TABLE1)}
    res["table1_ours"] = t1
    # dMAX plateau: rise from 0 to 100 and change from 100 to 200
    plateau = {}
    for name, by in (("SVM-DR", dr), ("SVM-DT", dt)):
        if by is None:
            continue
        m = means(by)
        if all(d in m for d in (0, 100, 200)):
            rise = m[100][0] - m[0][0]
            later = max(m[d][0] for d in m if d >= 100) - min(m[d][0] for d in m if d >= 100)
            plateau[name] = {"rise_0_to_100": round(rise, 4), "range_100_to_200": round(later, 4),
                             "plateau (range 100-200 below a tenth of the rise)":
                                 "yes" if later < rise / 10 else "no"}
    res["dmax_plateau"] = plateau
    if "SVM-DT" in t1:
        res["improvement_over_top_n_gram"] = {
            "roc_points": round(100 * (t1["SVM-DT"]["roc"] - float(TABLE1["SVM-Top-n-gram"][0])), 2),
            "roc50_points": round(100 * (t1["SVM-DT"]["roc50"] - float(TABLE1["SVM-Top-n-gram"][1])), 2),
            "note": "ours minus the SVM-Top-n-gram row the paper quotes (not rerun), in points"}
        res["family_2513"] = {"SVM-DT": t1["SVM-DT"]["family_2.5.1.3_roc"],
                                 "SVM-DR": t1["SVM-DR"]["family_2.5.1.3_roc"],
                                 "DT above DR": "yes" if t1["SVM-DT"]["family_2.5.1.3_roc"] >
                                 t1["SVM-DR"]["family_2.5.1.3_roc"] else "no"}
    res["weights"] = {"SVM-DR": weight_claims(json.load(open(wdr)))}
    if wdt != "-":
        res["weights"]["SVM-DT"] = weight_claims(json.load(open(wdt)))
        gg_dr = res["weights"]["SVM-DR"]["G,G"]["share_positive_d1_150"]
        gg_dt = res["weights"]["SVM-DT"]["G,G"]["share_positive_d1_150"]
        res["weights"]["DR more positive (G,G) than DT"] = "yes" if gg_dr > gg_dt else "no"
    for m, w in list(res["weights"].items()):
        if isinstance(w, dict) and "G,G" in w:
            w["G,G mostly positive"] = "yes" if w["G,G"]["share_positive_d1_150"] > 0.5 else "no"
    # The same formulas on the paper's own Table 1
    p = {k: (float(a), float(b)) for k, (a, b) in TABLE1.items()}
    res["arithmetic"] = {
        "improvement_roc_points": round(100 * (p["SVM-DT"][0] - p["SVM-Top-n-gram"][0]), 2),
        "improvement_roc50_points": round(100 * (p["SVM-DT"][1] - p["SVM-Top-n-gram"][1]), 2),
        "SVM-DR": comparisons("SVM-DR", p["SVM-DR"][0], p["SVM-DR"][1], TABLE1),
        "SVM-DT": comparisons("SVM-DT", p["SVM-DT"][0], p["SVM-DT"][1], TABLE1),
    }
    a = res["arithmetic"]
    a["all_claims_come_back"] = "yes" if (
        a["improvement_roc_points"] == 4.1 and a["improvement_roc50_points"] == 10.4
        and all(v == "yes" for v in list(a["SVM-DR"].values()) + list(a["SVM-DT"].values()))) else "no"
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps({k: res[k] for k in ("table1_ours", "dmax_plateau", "arithmetic")}, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:6])

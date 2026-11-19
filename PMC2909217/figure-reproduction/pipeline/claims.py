"""The paper's claims in the text, computed from our run, and the arithmetic check on its own tables.

    python claims.py ROC.json TABLE1.json COUNTS.json NETWORK.json PUBLISHED_VALUES.json OUT.json

Every comparison is computed here; build_results.py only copies the fields.
"""

from __future__ import annotations

import json
import math
import sys

import numpy as np
from scipy.special import kolmogorov


def yn(v):
    return "yes" if v else "no"


def ks_p(D, n_eff):
    """Asymptotic two-sided KS P for statistic D at effective size n_eff = n1 n2 / (n1 + n2)."""
    return float(kolmogorov(D * math.sqrt(n_eff)))


def implied_n(D, P):
    """Effective sample size n1 n2 / (n1 + n2) at which the asymptotic KS P of D equals P."""
    lo, hi = 1.0, 1e9
    for _ in range(200):
        mid = math.sqrt(lo * hi)
        if ks_p(D, mid) > P:
            lo = mid
        else:
            hi = mid
    return mid


def p_field(name, printed, observed):
    """A P-value field at the printed precision. A value printed with an exponent ("7.05E-14") is
    compared in units of that exponent (expected "7.05", observed our P / 1E-14), so that tiny
    P-values are not equal to each other within check_results.py's absolute floor."""
    s = printed.strip()
    if "e" in s.lower():
        mant, ex = s.lower().split("e")
        unit = int(ex)
        return {"name": f"{name} (x 1E{unit:+03d})", "expected": mant, "observed": f"{observed / 10.0 ** unit:.6g}"}
    return {"name": name, "expected": s, "observed": f"{observed:.6g}"}


def main(roc_p, t1_p, counts_p, net_p, pub_p, out_p):
    roc = json.load(open(roc_p))["curves"]
    t1 = {r["id"]: r for r in json.load(open(t1_p))["rows"]}
    counts = json.load(open(counts_p))
    net = json.load(open(net_p))
    pub = json.load(open(pub_p))
    grid = np.array(json.load(open(roc_p))["fpr_grid"])

    def tpr(key):
        return np.array(roc[key]["tpr_at_fpr_mean"])

    out = {}
    # 1. operating point: the best SSL TPR at FPR 0.09 over the experiments ("at a maximum")
    i09 = int(np.argmin(abs(grid - 0.09)))
    best = max((tpr(k)[i09], k) for k in roc if "/ssl/weighted" in k)
    out["text.operating_point"] = {"fields": [
        {"name": "Best SSL sensitivity at 1 - specificity 0.09", "expected": pub["operating_point"]["tpr"],
         "observed": f"{best[0]:.2f}"}], "detail": {"curve": best[1]}}

    # 2. SSL above SVM over almost all thresholds (Figs 2-4)
    fields = []
    for s, fig in (("unlabelled20", "Fig. 2"), ("unlabelled50", "Fig. 3"), ("unlabelled80", "Fig. 4")):
        a, b = tpr(f"{s}/ssl/weighted"), tpr(f"{s}/svm/weighted")
        inner = (grid > 0) & (grid < 1)
        share = float(np.mean(a[inner] >= b[inner]))
        fields.append({"name": f"{fig}: SSL at or above SVM over at least 90% of the FPR range",
                       "expected": "yes", "observed": yn(share >= 0.9), "share": round(share, 3)})
    out["text.ssl_above_svm"] = {"fields": fields}

    # 3. Fig. 2: SVM slightly better at the start of the curve, SSL elsewhere
    a, b = tpr("unlabelled20/ssl/weighted"), tpr("unlabelled20/svm/weighted")
    start = (grid > 0) & (grid <= 0.05)
    rest = (grid > 0.05) & (grid < 1)
    out["text.fig2_start"] = {"fields": [
        {"name": "SVM above SSL at FPR up to 0.05", "expected": "yes", "observed": yn(bool(np.all(b[start] > a[start])))},
        {"name": "SSL at or above SVM at FPR above 0.05 (90% of the range)", "expected": "yes",
         "observed": yn(float(np.mean(a[rest] >= b[rest])) >= 0.9)}]}

    # 4. small training sets: SSL much better at 80% unlabelled, and its lead grows as labels shrink
    gap = {s: roc[f"{s}/ssl/weighted"]["auc_mean"] - roc[f"{s}/svm/weighted"]["auc_mean"]
           for s in ("unlabelled20", "unlabelled50", "unlabelled80")}
    out["text.small_training"] = {"fields": [
        {"name": "Fig. 4: SSL area under the ROC curve above SVM's by more than 0.05", "expected": "yes",
         "observed": yn(gap["unlabelled80"] > 0.05)},
        {"name": "SSL's lead over SVM larger at 80% than at 20% unlabelled", "expected": "yes",
         "observed": yn(gap["unlabelled80"] > gap["unlabelled20"])}],
        "detail": {k: round(v, 4) for k, v in gap.items()}}

    # 5. Fig. 5: weighted above binary in almost all the range
    a, b = tpr("unlabelled50/ssl/weighted"), tpr("unlabelled50/ssl/binary")
    inner = (grid > 0) & (grid < 1)
    share = float(np.mean(a[inner] >= b[inner]))
    out["text.weighted_above_binary"] = {"fields": [
        {"name": "Weighted FGN at or above the binary network over at least 90% of the FPR range",
         "expected": "yes", "observed": yn(share >= 0.9), "share": round(share, 3)},
        {"name": "Weighted FGN area under the ROC curve above the binary network's", "expected": "yes",
         "observed": yn(roc["unlabelled50/ssl/weighted"]["auc_mean"] > roc["unlabelled50/ssl/binary"]["auc_mean"])}]}

    # 6. Discussion: KS significant for all, SGI higher average degree and closeness, weighted P smaller
    ours_sig = all(t1[k][n]["P"] < 0.05 for k in t1 for n in ("binary", "weighted"))
    out["text.ks_all_significant"] = {"fields": [
        {"name": "All Table 1 P-values below 0.05", "expected": "yes", "observed": yn(ours_sig)}]}
    out["text.sgi_higher"] = {"fields": [
        {"name": "SGI pairs have the higher average degree (weighted FGN)", "expected": "yes",
         "observed": yn(t1["avg_degree"]["weighted"]["sgi_higher"])},
        {"name": "SGI pairs have the higher average closeness (weighted FGN)", "expected": "yes",
         "observed": yn(t1["avg_closeness"]["weighted"]["sgi_higher"])}]}
    smaller = [t1[k]["weighted"]["P"] < t1[k]["binary"]["P"] for k in t1]
    out["text.weighted_p_smaller"] = {"fields": [
        {"name": "Weighted-network P below the binary network's for all 8 characteristics", "expected": "yes",
         "observed": yn(all(smaller))}], "detail": {"rows_smaller": int(sum(smaller))}}

    # 7. Methods data counts
    m = pub["methods_counts"]
    out["text.data_counts"] = {"fields": [
        {"name": "Tong 2004 query genes", "expected": m["tong_queries"], "observed": str(counts["tong_queries"])},
        {"name": "Deletion-array genes (about 4,700)", "expected": m["array_genes"], "observed": str(counts["array_genes"]),
         "tolerance": {"rel": 0.05}},
        {"name": "Tested pairs (about 650,000)", "expected": m["tested_pairs"], "observed": str(counts["tested_pairs"]),
         "tolerance": {"rel": 0.05}},
        {"name": "Synthetic lethal and sick interactions (about 4,000)", "expected": m["sgi_interactions"],
         "observed": str(counts["sgi_pairs"]), "tolerance": {"rel": 0.05}},
        {"name": "PPI interactions", "expected": m["ppi_interactions"], "observed": str(counts["ppi_interactions"])},
        {"name": "PPI proteins", "expected": m["ppi_proteins"], "observed": str(counts["ppi_proteins"])},
        {"name": "Complex interactions (about 49,000)", "expected": m["complex_interactions"],
         "observed": str(counts["complex_interactions"]), "tolerance": {"rel": 0.05}},
        {"name": "Expression conditions", "expected": m["expression_conditions"], "observed": str(counts["expression_conditions"])},
    ]}

    # 8. Arithmetic check: the claims recomputed from the paper's own Table 1
    pt = pub["table1"]
    p_sig = {f"{k}/{n}": float(pt[k][n]["P"]) < 0.05 for k in pt for n in ("binary", "weighted")}
    p_smaller = {k: float(pt[k]["weighted"]["P"]) < float(pt[k]["binary"]["P"]) for k in pt}
    nimp = {f"{k}/{n}": round(implied_n(float(pt[k][n]["D"]), float(pt[k][n]["P"])), 0)
            for k in pt for n in ("binary", "weighted")}
    med = {n: float(np.median([v for kk, v in nimp.items() if kk.endswith(n) and kk != "avg_degree/binary"]))
           for n in ("binary", "weighted")}
    p_at_median = ks_p(float(pt["avg_degree"]["binary"]["D"]), med["binary"])
    f6 = pub["fig6_labels"]
    fig6_vs_table = {k: (f6[k]["D"] == pt[f"diff_{f6[k]['property']}"]["weighted"]["D"],
                         math.isclose(float(f6[k]["P"]), float(pt[f"diff_{f6[k]['property']}"]["weighted"]["P"]), rel_tol=0.01))
                     for k in f6}
    out["text.arithmetic"] = {
        "all_p_below_0.05": all(p_sig.values()),
        "p_not_below_0.05": [k for k, v in p_sig.items() if not v],
        "weighted_p_smaller_rows": int(sum(p_smaller.values())),
        "weighted_p_not_smaller": [k for k, v in p_smaller.items() if not v],
        "implied_effective_n": nimp,
        "implied_effective_n_median": med,
        "avg_degree_binary_p_at_median_n": p_at_median,
        "binary_diff_degree_equals_diff_closeness": pt["diff_degree"]["binary"] == pt["diff_closeness"]["binary"],
        "fig6_labels_match_table1": {k: {"D": v[0], "P": v[1]} for k, v in fig6_vs_table.items()},
        "our_effective_n": round(net["sgi_pairs_in_network"] * net["nonsgi_pairs_in_network"]
                                 / (net["sgi_pairs_in_network"] + net["nonsgi_pairs_in_network"]), 0),
    }

    # 9. Table 1 and the Fig. 6 labels: our D and P against the printed values
    t1_fields, exceptions = [], []
    for k, row in pt.items():
        for n in ("binary", "weighted"):
            t1_fields.append({"name": f"{k} {n} D", "expected": row[n]["D"], "observed": f"{t1[k][n]['D']:.4f}"})
            t1_fields.append(p_field(f"{k} {n} P", row[n]["P"], t1[k][n]["P"]))
    out["table1"] = {"fields": t1_fields}
    f6_fields = []
    for k, v in f6.items():
        r = t1[f"diff_{v['property']}"]["weighted"]
        f6_fields.append({"name": f"Fig. 6{k} KSStat", "expected": v["D"], "observed": f"{r['D']:.4f}"})
        f6_fields.append(p_field(f"Fig. 6{k} P-value", v["P"], r["P"]))
    out["fig6.labels"] = {"fields": f6_fields}
    json.dump(out, open(out_p, "w"), indent=1)
    for k, v in out.items():
        if "fields" in v:
            print(k, [(f["expected"], f["observed"]) for f in v["fields"]][:4])
    print("arithmetic", json.dumps(out["text.arithmetic"])[:600])


if __name__ == "__main__":
    main(*sys.argv[1:7])

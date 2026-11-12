"""Our series for every scored panel, in the data units of the published panel.

ours(fig, panel, R, variant) returns {series name: [[x, y], ...]} (or, for the
scatter-plot regression lines of Figs S8 and S9, {"lines": {...}}), where R holds
the pipeline's results:
  R["sim"]       summarize.py output, noise SD 0.1 (our reading)
  R["sim_sd001"] the same with noise SD 0.01 (the other reading; a near miss)
  R["one"], R["one_sd001"]  one_dataset.R output (data set 1)
  R["fig1"]      fig1.R output
  R["leuk"]      leukemia.R output
  R["pi0_07"]    pi0 curves with pi0 = 0.7 (a wrong input for Fig. 3)
Variants: "ours", "sd0.01", "amp1.05", "amp0.95", "wrong", and per figure "draw2"
(another random leukemia subset), "delta_mean" (Fig. 1, delta read as the mean).
"""
import math

import numpy as np

FR11 = [0, .1, .2, .3, .4, .5, .6, .7, .8, .9, .99]
FR12 = FR11 + [1]
LEVELS = [round(0.05 * i, 2) for i in range(20)] + [0.99]


def k(x):
    return f"{round(x, 2) + 0.0:g}"


def curve(S, st, filt, meth, alpha, field, fractions):
    node = S[st][filt][meth][k(alpha)]
    return [[f, node[k(f)][field]] for f in fractions if k(f) in node]


def scale(series, a):
    if "lines" in series:
        return {"lines": {n: {**l, "intercept": l["intercept"] * a, "slope": l["slope"] * a}
                          for n, l in series["lines"].items()}}
    return {n: [[x, y * a] for x, y in pts] for n, pts in series.items()}


# ---------------------------------------------------------------- per figure

def fig1(panel, R, v):
    F = R["fig1"]
    src = {"ours": panel, "wrong": "alternative" if panel == "null" else "null"}.get(v, panel)
    d = dict(F[src])
    if v == "total_variance":                 # the text's W_V = S_Z^2 for the variance filter
        d["variance"] = F["total_variance"][panel]
    if v == "threshold_own" and panel == "alternative":
        d = F["alternative_own"]
    if v == "delta_mean" and panel == "alternative":
        d = F["alternative_mean1"]
    return {n: [[u, y] for u, y in zip(F["u"], d[n])] for n in ("none", "foldchange", "variance")}


def hist_lines(stats, null, edges, m):
    stats = np.asarray(stats)
    null = np.asarray(null, bool)
    out = {}
    for nm, sel in (("null", null), ("alternative", ~null)):
        cnt, _ = np.histogram(stats[sel], bins=edges)
        pts = []
        for i, c in enumerate(cnt):
            y = c / (m * (edges[i + 1] - edges[i]))
            pts += [[edges[i], y], [edges[i + 1], y]]
        out[nm] = pts
    return out


def fig2(panel, R, v, pub):
    one = R["one_sd001"] if v == "sd0.01" else R["one"]
    st = one["stats"]
    m = len(st["null"])
    stat = {"foldchange": st["foldchange"], "signal": st["signal"],
            "variance": [19 * s for s in st["variance"]]}
    if v == "wrong":           # a neighbouring statistic drawn on this panel's axes
        stat = {"foldchange": st["tstat"], "signal": st["foldchange"], "variance": st["variance"]}
    bars = pub["histogram"]
    edges = [b[0] for b in bars] + [bars[-1][1]]
    # stretch the published breaks to cover our range (bins of the same width)
    w = edges[1] - edges[0]
    lo, hi = min(stat[panel]), max(stat[panel])
    while edges[0] > lo:
        edges.insert(0, edges[0] - w)
    while edges[-1] < hi:
        edges.append(edges[-1] + w)
    return hist_lines(stat[panel], st["null"], np.array(edges), m)


def fig3(panel, R, v):
    S = R["sim_sd001"] if v == "sd0.01" else R["sim"]
    if v == "wrong":
        S = R["pi0_07"]
    out = {f: curve(S, "curves", f, "BH", 0.05, "pi0", FR12) for f in ("foldchange", "signal", "variance")}
    p0 = 0.7 if v == "wrong" else 0.8
    xs = np.linspace(0, 1, 101)
    out["best"] = [[x, max(0.0, (p0 - x) / (1 - x)) if x < 1 else 0.0] for x in xs]
    if "random" in S["curves"]:
        # drawn as the paper draws it: flat at pi0 to x = 1, then down to 0
        r = dict((round(x, 2), y) for x, y in curve(S, "curves", "random", "BH", 0.05, "pi0", FR12))
        out["random"] = [[0, r[0]], [1, r[0.99]], [1, 0.0]]
    return out


def fig4(panel, R, v):
    S = R["sim_sd001"] if v == "sd0.01" else R["sim"]
    meth = {"BH": "BY", "aBH": "BY", "BY": "BH", "qvalue": "BY"}[panel] if v == "wrong" else panel
    filters = ("variance", "signal") if panel == "qvalue" else ("variance", "signal", "foldchange")
    fr = FR11[:-1] if panel == "qvalue" else FR11
    return {f: curve(S, "curves", f, meth, 0.05, "fdr", fr) for f in filters}


def fig5(panel, R, v):
    S = R["sim_sd001"] if v == "sd0.01" else R["sim"]
    filt = {"foldchange": "signal", "signal": "variance", "variance": "foldchange"}[panel] if v == "wrong" else panel
    out = {}
    for f in FR11:
        out[f"{f:g}"] = [[a, S["levels"][filt]["BH"][k(a)][k(f)]["power"]] for a in LEVELS]
    return out


def box_series(cats, box, half=13.95):
    """A boxplot drawn as polylines in data units on a categorical x axis (x in points)."""
    out = {}
    for f, st in box.items():
        c = cats[f]
        if st["q1"] is None:
            continue
        out[f"box{f}"] = [[c - half, st["q1"]], [c + half, st["q1"]], [c + half, st["q3"]],
                          [c - half, st["q3"]], [c - half, st["q1"]]]
        out[f"median{f}"] = [[c - half, st["median"]], [c + half, st["median"]]]
        out[f"whisker{f}"] = [[c, st["whisker_low"]], [c, st["q1"]]]
        out[f"whiskerhi{f}"] = [[c, st["q3"]], [c, st["whisker_high"]]]
    return out


def test_boxes(one, filt):
    t = one["test"][filt]
    return {f"{f:g}": b for f, b in zip(t["fractions"], t["box"])}


def fig6(panel, R, v, cats):
    # Fig. 6 was drawn from a data set without the noise term (see results_notes.json)
    one = {"sd0.01": R["one_sd001"], "sd0.1": R["one"]}.get(v, R["one_sd0"])
    filt = "variance" if v == "wrong" else "foldchange"
    lines = {m: [[cats[f"{f:g}"], y] for f, y in zip(FR11, one["fdr"][filt][m])]
             for m in ("BH", "aBH", "BY", "bonferroni")}
    lines.update(box_series(cats, test_boxes(one, filt)))
    return lines


def leuk_series(L, field, which="main"):
    out = {}
    for n in ("n8", "n16", "n24"):
        src = L["main"][n] if which == "main" else L["draws"][n][1]
        for filt in ("foldchange", "signal", "variance"):
            col = {"fdr": 1, "power": 2}[field]
            out[f"{filt}.{n}"] = [[r[0], r[col]] for r in src[filt]]
    return out


def fig7(panel, R, v):
    field = "power" if v == "wrong" else "fdr"
    return leuk_series(R["leuk"], field, "draw2" if v == "draw2" else "main")


def figS5(panel, R, v):
    field = "fdr" if v == "wrong" else "power"
    return leuk_series(R["leuk"], field, "draw2" if v == "draw2" else "main")


def figS2(panel, R, v):
    S = R["sim_sd001"] if v == "sd0.01" else R["sim"]
    field = "fdr" if v == "wrong" else "power"
    filters = ("variance", "signal") if panel == "qvalue" else ("variance", "signal", "foldchange")
    fr = FR11[:-1] if panel == "qvalue" else FR11
    return {f: curve(S, "curves", f, panel, 0.05, field, fr) for f in filters}


def figS3(panel, R, v):
    S = R["sim_sd001"] if v == "sd0.01" else R["sim"]
    filt = {"foldchange": "signal", "signal": "variance", "variance": "foldchange"}[panel] if v == "wrong" else panel
    out = {}
    for f in FR11:
        node = S["levels"][filt]["BH"]
        out[f"{f:g}"] = [[node[k(a)][k(f)]["fdr"], node[k(a)][k(f)]["power"]] for a in LEVELS[1:]]
    return out


def figS4(panel, R, v, cats):
    one = R["one_sd001"] if v == "sd0.01" else R["one"]
    filt = {"foldchange": "variance", "variance": "signal", "signal": "foldchange"}[panel] if v == "wrong" else panel
    meths = ("BH", "aBH", "BY", "bonferroni") + (("qvalue",) if panel != "foldchange" else ())
    out = {}
    for m in meths:
        ys = one["fdr"][filt].get(m)
        if ys is None:
            continue
        fr = FR11 if m != "qvalue" else FR11[:-1]
        out[m] = [[cats[f"{f:g}"], y] for f, y in zip(fr, ys)]
    for f, b in test_boxes(one, filt).items():
        c = cats[f]
        out[f"median{f}"] = [[c - 2.8, b["median"]], [c + 2.8, b["median"]]]
    return out


def figS6(panel, R, v):
    S = R["sim_sd001"] if v == "sd0.01" else R["sim"]
    field = {"fdr": "fdr", "power": "power"}[panel]
    if v == "wrong":
        field = "power" if field == "fdr" else "fdr"
    return {f: curve(S, "wilcoxon", f, "BH", 0.05, field, FR11) for f in ("foldchange", "signal", "variance")}


def regression(post, filt, field, n=100):
    """Least-squares lines of each filtered situation against situation A, data sets 1..n."""
    rows = [r for r in post if r["filter"] == filt and r["dataset"] <= n]
    A = {r["dataset"]: r[field] for r in rows if r["situation"] == "A"}
    out = {}
    for sit, fr, nm in (("B", 0.25, "B25"), ("B", 0.5, "B50"), ("C", 0.1, "C10"), ("C", 0.2, "C20")):
        pairs = [(A[r["dataset"]], r[field]) for r in rows if r["situation"] == sit and abs(r["fraction"] - fr) < 1e-9]
        x = np.array([p[0] for p in pairs])
        y = np.array([p[1] for p in pairs])
        slope, icpt = np.polyfit(x, y, 1)
        out[nm] = {"intercept": float(icpt), "slope": float(slope), "x": [float(x.min()), float(x.max())],
                   "points": len(pairs)}
    return {"lines": out}


def figS8(panel, R, v):
    S = R["sim_sd001"] if v == "sd0.01" else R["sim"]
    return regression(S["post"], panel, "power" if v == "wrong" else "fdr")


def figS9(panel, R, v):
    S = R["sim_sd001"] if v == "sd0.01" else R["sim"]
    return regression(S["post"], panel, "fdr" if v == "wrong" else "power")


def ours(fig, panel, R, v="ours", pub=None):
    base = v if v in ("amp1.05", "amp0.95") else None
    vv = "ours" if base else v
    cats = (pub or {}).get("x_map", {}).get("categories")
    if fig == "fig1":
        s = fig1(panel, R, vv)
    elif fig == "fig2":
        s = fig2(panel, R, vv, pub)
    elif fig in ("fig6",):
        s = fig6(panel, R, vv, cats)
    elif fig == "figS4":
        s = figS4(panel, R, vv, cats)
    else:
        s = globals()[fig](panel, R, vv)
    if base:
        s = scale(s, 1.05 if base == "amp1.05" else 0.95)
    return s


CONTROLS = {
    "fig1": [("wrong", "wrong_input", "the other hypothesis's densities"),
             ("total_variance", "near_miss", "variance filter on S_Z^2 (the text's W_V)"),
             ("threshold_own", "near_miss", "thresholds set under the alternative itself"),
             ("delta_mean", "near_miss", "alternative read as a group difference of 1 (noncentrality 1.58)"),
             ("amp1.05", "near_miss", "densities x1.05"), ("amp0.95", "near_miss", "densities x0.95")],
    "fig2": [("wrong", "wrong_input", "a neighbouring statistic (|t| / fold change / S^2)"),
             ("sd0.01", "near_miss", "noise SD 0.01"),
             ("amp1.05", "near_miss", "heights x1.05"), ("amp0.95", "near_miss", "heights x0.95")],
    "fig3": [("wrong", "wrong_input", "pi0 = 0.7"), ("sd0.01", "near_miss", "noise SD 0.01"),
             ("amp1.05", "near_miss", "pi0 x1.05"), ("amp0.95", "near_miss", "pi0 x0.95")],
    "fig6": [("wrong", "wrong_input", "the variance filter's test and FDR lines"),
             ("sd0.1", "near_miss", "data set with noise SD 0.1 (the reading of Figs 3 to 5)"),
             ("sd0.01", "near_miss", "data set with noise SD 0.01"),
             ("amp1.05", "near_miss", "values x1.05"), ("amp0.95", "near_miss", "values x0.95")],
    "default": [("wrong", "wrong_input", None), ("sd0.01", "near_miss", "noise SD 0.01"),
                ("amp1.05", "near_miss", "values x1.05"), ("amp0.95", "near_miss", "values x0.95")],
    "leuk": [("wrong", "wrong_input", None), ("draw2", "near_miss", "another random subset of each size"),
             ("amp1.05", "near_miss", "values x1.05"), ("amp0.95", "near_miss", "values x0.95")],
}

WRONG = {"fig4": "another FDR method's curves (BY for BH, aBH and q-value; BH for BY)",
         "fig5": "another filter's curves", "fig6": "the variance filter's test and FDR lines",
         "fig7": "power instead of achieved FDR", "figS2": "achieved FDR instead of power",
         "figS3": "another filter's curves", "figS4": "another filter's test and FDR lines",
         "figS5": "achieved FDR instead of power", "figS6": "the other panel's quantity (power for FDR and back)",
         "figS8": "power instead of FDR", "figS9": "FDR instead of power"}


def controls(fig):
    if fig in ("fig7", "figS5"):
        c = CONTROLS["leuk"]
    else:
        c = CONTROLS.get(fig, CONTROLS["default"])
    return [(v, kind, desc or WRONG.get(fig, "")) for v, kind, desc in c]

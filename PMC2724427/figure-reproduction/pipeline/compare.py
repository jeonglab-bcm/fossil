"""Score the reproduction against the paper: Table 1, the claims in the text, Figs 1-3.

  compare.py PUBLISHED_DIR CALIB_JSON RUN_DIR FIGS_DIR SEEDS_DIR OUT_DIR

RUN_DIR holds the main run (fit.json, per_n.csv, samples_fig.csv, checks.json); FIGS_DIR the
renders (fig*_ours.png and controls/); SEEDS_DIR the seed-spread and hypothesis runs
(seed_*.json, xsd1_seed_*.json). Writes OUT_DIR/comparison.json (one entry per results.json
item: values, pixels or check), OUT_DIR/tables.json (Table 1 published against ours, the seed
spread and the sensitivity runs, for the page) and the overlays OUT_DIR/fig*_overlay.png.

Pixels: ink is grey below 170. Inside each published panel box (shrunk by 3 px to leave out the
frame; in Fig. 2 the reference line at 2 and in Fig. 3 the line at 2 are masked), the score is the
smaller of two shares: published ink within 2 px of ours, and ours within 2 px of the published.
Fig. 2 pools its six panels. Each control is scored the same way; the pass mark is 0.005 above
the best control.
"""
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

pub, calib_p, run, figs, seeds, out = map(Path, sys.argv[1:7])
out.mkdir(parents=True, exist_ok=True)
calib = json.loads(calib_p.read_text())
fit = json.loads((run / "fit.json").read_text())
checks = json.loads((run / "checks.json").read_text())
per_n = list(csv.DictReader(open(run / "per_n.csv")))
samples = list(csv.DictReader(open(run / "samples_fig.csv")))
INK, TOL = 170, 2


# ---------------------------------------------------------------- helpers
def decimals(s):
    s = s.lstrip("<>-")
    return len(s.split(".")[1]) if "." in s else 0


def fmt(x, like):
    """Our value printed like the paper's string `like` (same decimals; '<0.0001' for p)."""
    if like.startswith("<"):
        lim = float(like[1:])
        return like if x < lim else f"{x:.{decimals(like)}f}"
    return f"{x:.{decimals(like)}f}"


def row(table, term, param):
    return next(r for r in table if r["term"] == term and r["param"] == param)


def gray(p):
    return np.asarray(Image.open(p).convert("L"), dtype=float)


def ink_mask(img, panels, masks):
    m = np.zeros(img.shape, bool)
    for pid in panels:
        x0, x1, y0, y1 = calib[pid]["box"]
        m[y0 + 3:y1 - 2, x0 + 3:x1 - 2] = True
    for (axis, lo, hi) in masks:
        if axis == "x":
            m[:, lo:hi + 1] = False
        else:
            m[lo:hi + 1, :] = False
    return (img < INK) & m


def score(pub_img, our_img, panels, masks):
    a = ink_mask(pub_img, panels, masks)
    b = ink_mask(our_img, panels, masks)
    if not a.any() or not b.any():
        return 0.0, 0.0
    da = ndimage.distance_transform_edt(~a)
    db = ndimage.distance_transform_edt(~b)
    return float((db[a] <= TOL).mean()), float((da[b] <= TOL).mean())


def overlay(pub_img, our_img, path):
    rgb = np.stack([pub_img, our_img, our_img], axis=-1).clip(0, 255).astype(np.uint8)
    Image.fromarray(rgb).save(path, optimize=True)


def px(pid, axis, value):
    c = calib[pid][axis]
    return (value - c["at0"]) / c["per_px"]


items = {}

# ---------------------------------------------------------------- Table 1 and R squared
PAPER = {
    "x": {"intercept": ("2.011", "0.00072", "2785.9", "<0.0001"), "inv_n": ("23.9", "0.276", "86.48", "<0.0001")},
    "z": {"intercept": ("-0.898", "0.00065", "-1369.34", "<0.0001"), "inv_n": ("-9.524", "0.251", "-37.92", "<0.0001")},
}
NAMES = {"x": "continuous", "z": "discrete"}
PNAME = {"intercept": "Intercept", "inv_n": "n⁻¹"}
t1 = fit["table1"]["means"]
for term in ("x", "z"):
    fields = []
    for param in ("intercept", "inv_n"):
        r = row(t1, term, param)
        for name, key, exp in zip(("estimate", "SE", "t-value", "Pr(>|t|)"), ("estimate", "se", "t", "p"),
                                  PAPER[term][param]):
            fields.append({"name": f"{PNAME[param]} {name}", "expected": exp, "observed": fmt(r[key], exp)})
    items[f"table1.{NAMES[term]}"] = {"method": "values", "values": {"fields": fields, "tolerance": {"printed": True}}}
items["text.r2"] = {"method": "values", "values": {"fields": [
    {"name": "R², continuous", "expected": "0.963", "observed": fmt(row(t1, "x", "intercept")["r2"], "0.963")},
    {"name": "R², discrete", "expected": "0.836", "observed": fmt(row(t1, "z", "intercept")["r2"], "0.836")}],
    "tolerance": {"printed": True}}}

# ---------------------------------------------------------------- claims recomputed from the paper's own numbers
arith = []
for term in ("x", "z"):
    for param in ("intercept", "inv_n"):
        est, se, t, _ = PAPER[term][param]
        implied = abs(float(est) / float(t))
        arith.append({"claim": f"Table 1, {NAMES[term]} {PNAME[param]}: SE = estimate / t",
                      "paper": se, "recomputed": fmt(implied, se), "holds": fmt(implied, se) == se})
# P(x > 2.5) of Additional file 1 from x ~ N(2, 0.7)
pgt = 0.5 * math.erfc((2.5 - 2) / 0.7 / math.sqrt(2))
arith.append({"claim": "Additional file 1: P(x>2.5) for x ~ N(2, 0.7)", "paper": "0.2375",
              "recomputed": f"{pgt:.4f}", "holds": f"{pgt:.4f}" == "0.2375"})
n_hold = sum(a["holds"] for a in arith)
items["text.arithmetic"] = {"method": "check", "check": {
    "passed": n_hold == len(arith),
    "detail": (f"{n_hold} of {len(arith)} come back from the paper's own numbers"
               + "".join(f"; not back: {a['claim']} (paper {a['paper']}, recomputed {a['recomputed']})"
                         for a in arith if not a["holds"]))},
    "arithmetic": arith}
# Fig. 2's headings against the curve of Table 1 (beta + b1/n), at the six sizes: the paper
# against itself. Within 0.02 (about 2.5 Monte Carlo standard errors of a mean of 1,000 estimates
# at n = 1000, sd 0.25) counts as consistent.
heads = {100: "2.262", 150: "2.129", 300: "2.051", 500: "2.019", 750: "2.011", 1000: "2.003"}
cross = []
for n, h in heads.items():
    curve = 2.011 + 23.9 / n
    cross.append({"n": n, "heading": h, "table1_curve": round(curve, 3), "gap": round(float(h) - curve, 3),
                  "holds": abs(curve - float(h)) <= 0.02})
items["text.figures_vs_table1"] = {"method": "check", "check": {
    "passed": all(c["holds"] for c in cross),
    "detail": (f"{sum(c['holds'] for c in cross)} of 6 Fig. 2 headings lie within 0.02 of Table 1's curve 2.011 + 23.9/n; "
               + ", ".join(f"n={c['n']} {c['heading']} against {c['table1_curve']:.3f}" for c in cross))},
    "cross": cross}
items["text.supp_px"] = {"method": "values", "values": {"fields": [
    {"name": "P(x>2.5), from x ~ N(2, 0.7)", "expected": "0.2375", "observed": f"{pgt:.4f}"}],
    "tolerance": {"printed": True}}, "population_share": fit["population"]["p_x_gt_2_5"]}

# ---------------------------------------------------------------- claims about our run
b1x = row(t1, "x", "inv_n")["estimate"]
b1z = row(t1, "z", "inv_n")["estimate"]
yn = lambda c: "yes" if c else "no"  # noqa: E731
items["text.away_from_null"] = {"method": "values", "values": {"fields": [
    {"name": "Continuous coefficient: b1 > 0 (bias away from zero)", "expected": "yes", "observed": yn(b1x > 0)},
    {"name": "Discrete coefficient: b1 < 0 (bias away from zero)", "expected": "yes", "observed": yn(b1z < 0)},
    {"name": "Odds ratio of the continuous exposure at n = 100 above the large-sample value", "expected": "yes",
     "observed": yn(math.exp(row(t1, "x", "intercept")["estimate"] + b1x / 100) > math.exp(row(t1, "x", "intercept")["estimate"]))},
], "tolerance": {"printed": True}}}
items["text.fit_better_continuous"] = {"method": "values", "values": {"fields": [
    {"name": "R² higher for the continuous than for the discrete coefficient", "expected": "yes",
     "observed": yn(row(t1, "x", "intercept")["r2"] > row(t1, "z", "intercept")["r2"])}], "tolerance": {"printed": True}}}

six = {(int(float(r["n"])), r["term"]): r for r in fit["six_sizes"]}
ests = {}
for r in samples:
    if r["status"] == "ok":
        ests.setdefault(int(float(r["n"])), []).append(float(r["x"]))


def skew(v):
    v = np.asarray(v)
    m = v.mean()
    return float(((v - m) ** 3).mean() / ((v - m) ** 2).mean() ** 1.5)


def outlier_share(v):
    v = np.asarray(v)
    q1, q3 = np.percentile(v, [25, 75])
    h = 1.5 * (q3 - q1)
    return float(((v < q1 - h) | (v > q3 + h)).mean())


sk = {n: skew(v) for n, v in ests.items()}
osh = {n: outlier_share(v) for n, v in ests.items()}
items["text.skewness"] = {"method": "values", "values": {"fields": [
    {"name": "Skewness of the continuous coefficient falls from n = 100 to n = 1000", "expected": "yes",
     "observed": yn(sk[100] > sk[1000])},
    {"name": "Skewness falls at each step of the six sizes of Fig. 2", "expected": "yes",
     "observed": yn(all(sk[a] > sk[b] for a, b in zip(sorted(sk), sorted(sk)[1:])))}], "tolerance": {"printed": True}},
    "skewness": sk}
items["text.extremes"] = {"method": "values", "values": {"fields": [
    {"name": "Share of extreme estimates (beyond the box-plot whiskers) smaller at n = 1000 than at n = 100",
     "expected": "yes", "observed": yn(osh[1000] < osh[100])},
    {"name": "Largest estimate smaller at n = 1000 than at n = 100", "expected": "yes",
     "observed": yn(max(ests[1000]) < max(ests[100]))}], "tolerance": {"printed": True}},
    "outlier_share": osh, "largest": {n: max(v) for n, v in ests.items()}}
kx = next(k for k in checks["kernel"] if k["term"] == "x")
kz = next(k for k in checks["kernel"] if k["term"] == "z")
in_band = lambda k: k["loglog_slope"] is not None and -2.5 <= k["loglog_slope"] <= -1.5  # noqa: E731
items["text.kernel"] = {"method": "values", "values": {"fields": [
    {"name": "Continuous: kernel derivative has the sign of -b1/n² at every n from 150 to 1400", "expected": "yes",
     "observed": yn(kx["same_sign_150_1400"])},
    {"name": "Continuous: kernel derivative falls as n⁻² (log-log slope within 2 ± 0.5)", "expected": "yes",
     "observed": yn(in_band(kx))},
    {"name": "Discrete: kernel derivative has the sign of -b1/n² at every n from 150 to 1400", "expected": "yes",
     "observed": yn(kz["same_sign_150_1400"])},
    {"name": "Discrete: kernel derivative falls as n⁻² (log-log slope within 2 ± 0.5)", "expected": "yes",
     "observed": yn(in_band(kz))}], "tolerance": {"printed": True}},
    "loglog_slope": {"x": kx["loglog_slope"], "z": kz["loglog_slope"]}}
items["port"] = {"method": "check", "check": checks["port"]}

# Fig. 2 headings: the mean continuous coefficient at each size
items["fig2.headings"] = {"method": "values", "values": {"fields": [
    {"name": f"n={n}", "expected": h, "observed": f"{np.mean(ests[n]):.3f}"} for n, h in heads.items()],
    "tolerance": {"printed": True}}}

# ---------------------------------------------------------------- figures by pixels
CONTROLS = {
    "fig1": [("no_bias", "wrong_input", "per-size means with the fitted bias b1/n taken out"),
             ("every_fit_kept", "wrong_input", "every fit kept, separated samples included"),
             ("warning_rule", "near_miss", "only the fits R warns about left out"),
             ("bias_x1.1", "near_miss", "bias b1/n ×1.1"),
             ("bias_x0.9", "near_miss", "bias b1/n ×0.9"),
             ("shift_up", "near_miss", "shifted up by 1% of the axis range"),
             ("shift_down", "near_miss", "shifted down by 1% of the axis range")],
    "fig2": [("neighbour_n", "wrong_input", "estimates of the neighbouring sample size in each panel"),
             ("bw_x1.25", "near_miss", "kernel bandwidth ×1.25"),
             ("bw_x0.8", "near_miss", "kernel bandwidth ×0.8"),
             ("shift_right", "near_miss", "shifted right by 1% of the axis range"),
             ("shift_left", "near_miss", "shifted left by 1% of the axis range")],
    "fig3": [("neighbour_n", "wrong_input", "estimates of the neighbouring sample size in each box"),
             ("shift_up", "near_miss", "shifted up by 1% of the axis range"),
             ("shift_down", "near_miss", "shifted down by 1% of the axis range"),
             ("spread_x0.9", "near_miss", "spread around the median ×0.9"),
             ("spread_x1.1", "near_miss", "spread around the median ×1.1")],
}
fig2_ids = [f"fig2.n{n}" for n in heads]
mask2 = []
for pid in fig2_ids:
    x = round(px(pid, "x", 2.0))
    mask2.append(("x", x - 2, x + 2))
y2 = round(px("fig3", "y", 2.0))
PANELS = {"fig1.continuous": ("fig1", ["fig1.continuous"], []),
          "fig1.discrete": ("fig1", ["fig1.discrete"], []),
          "fig2": ("fig2", fig2_ids, mask2),
          "fig3": ("fig3", ["fig3"], [("y", y2 - 2, y2 + 2)])}
pub_imgs = {f: gray(pub / f"figure-{f[-1]}.jpg") for f in ("fig1", "fig2", "fig3")}
our_imgs = {f: gray(figs / f"{f}_ours.png") for f in ("fig1", "fig2", "fig3")}
for f in pub_imgs:
    if pub_imgs[f].shape != our_imgs[f].shape:
        raise SystemExit(f"{f}: render {our_imgs[f].shape} is not the published size {pub_imgs[f].shape}")
    overlay(pub_imgs[f], our_imgs[f], out / f"{f}_overlay.png")
for item, (f, panels, masks) in PANELS.items():
    a, b = score(pub_imgs[f], our_imgs[f], panels, masks)
    ctrls = []
    for name, kind, label in CONTROLS[f]:
        ca, cb = score(pub_imgs[f], gray(figs / "controls" / f"{f}_{name}.png"), panels, masks)
        ctrls.append({"name": label, "kind": kind, "score": round(min(ca, cb), 4)})
    best = max(c["score"] for c in ctrls)
    items[item] = {"method": "pixels", "pixels": {
        "tolerance_px": TOL, "dpi": None, "published_near_ours": round(a, 4), "ours_near_published": round(b, 4),
        "threshold": round(min(best + 0.005, 0.999), 4), "controls": ctrls},
        "outputs": [f"figure-reproduction/output/figs/{f}_ours.png", f"figure-reproduction/output/cmp/{f}_overlay.png"]}

# Points of Fig. 1 that fall outside the published axes (drawn clipped)
for term, pid in (("x", "fig1.continuous"), ("z", "fig1.discrete")):
    lo, hi = sorted(calib[pid]["y"]["usr"])
    ms = [float(r["mean"]) for r in per_n if r["term"] == term]
    items[pid]["outside_axes"] = {"points": sum(not (lo <= m <= hi) for m in ms), "of": len(ms),
                                  "axis": [round(lo, 4), round(hi, 4)]}

# Hypothesis renders, scored like ours (hypothesis tests, never agreement)
hyp_scores = {}
for name, f, item in (("population", "fig1", "fig1.continuous"), ("population", "fig1", "fig1.discrete"),
                      ("xsd1", "fig1", "fig1.continuous"), ("xsd1", "fig1", "fig1.discrete"),
                      ("xsd1", "fig2", "fig2"), ("xsd1", "fig3", "fig3")):
    pth = figs / "hypotheses" / f"{f}_{name}.png"
    if pth.exists():
        _, panels, masks = PANELS[item]
        ha, hb = score(pub_imgs[f], gray(pth), panels, masks)
        hyp_scores[f"{item}.{name}"] = {"score": round(min(ha, hb), 4), "published_near": round(ha, 4),
                                        "ours_near": round(hb, 4)}

# ---------------------------------------------------------------- seed spread and hypothesis runs
def load_runs(pattern):
    return [json.loads(p.read_text()) for p in sorted(seeds.glob(pattern))]


spread = load_runs("seed_*.json")
hyp_xsd1 = [json.loads(p.read_text()) for p in sorted((seeds / "xsd1").glob("fit.json"))]


def t1_values(run_, variant="means"):
    t = run_["table1"][variant]
    return {f"{NAMES[r['term']]}.{r['param']}.{k}": r[k] for r in t for k in ("estimate", "se", "t")} | \
        {f"{NAMES[r['term']]}.r2": r["r2"] for r in t if r["param"] == "intercept"}


paper_flat = {"continuous.intercept.estimate": 2.011, "continuous.intercept.se": 0.00072, "continuous.intercept.t": 2785.9,
              "continuous.inv_n.estimate": 23.9, "continuous.inv_n.se": 0.276, "continuous.inv_n.t": 86.48,
              "discrete.intercept.estimate": -0.898, "discrete.intercept.se": 0.00065, "discrete.intercept.t": -1369.34,
              "discrete.inv_n.estimate": -9.524, "discrete.inv_n.se": 0.251, "discrete.inv_n.t": -37.92,
              "continuous.r2": 0.963, "discrete.r2": 0.836}
spread_tab = {}
if spread:
    for k, pv in paper_flat.items():
        vals = np.array([t1_values(r)[k] for r in spread])
        spread_tab[k] = {"paper": pv, "min": float(vals.min()), "max": float(vals.max()), "mean": float(vals.mean()),
                         "sd": float(vals.std(ddof=1)), "paper_inside_range": bool(vals.min() <= pv <= vals.max()),
                         "share_below_paper": float((vals < pv).mean())}
    sd1000 = [next(r for r in s_["six_sizes"] if r["n"] == 1000 and r["term"] == "x")["sd"] for s_ in spread]
    spread_tab["sd_x_at_1000"] = {"min": min(sd1000), "max": max(sd1000)}
    spread_tab["fig2_headings"] = {}
    for n, h in heads.items():
        ms = [next(r for r in s_["six_sizes"] if r["n"] == n and r["term"] == "x")["mean"] for s_ in spread]
        spread_tab["fig2_headings"][str(n)] = {"paper": float(h), "min": min(ms), "max": max(ms),
                                               "paper_inside_range": min(ms) <= float(h) <= max(ms)}
    pops = [s_["population"]["glm"] for s_ in spread]
    spread_tab["population_glm"] = {k: {"min": min(p[k] for p in pops), "max": max(p[k] for p in pops)} for k in ("x", "z")}
tables = {
    "table1": [{"key": k, "paper": v, "ours": t1_values(fit)[k], "ours_all_estimates": t1_values(fit, "all")[k],
                "sensitivity_warning_rule": t1_values(fit, "means_warning_rule")[k],
                "sensitivity_every_fit_kept": t1_values(fit, "means_every_fit_kept")[k],
                "hypothesis_x_sd_1": t1_values(hyp_xsd1[0])[k] if hyp_xsd1 else None}
               for k, v in paper_flat.items()],
    "seed_spread": {"seeds": [s_["seed"] for s_ in spread], "fields": spread_tab},
    "population": fit["population"], "analytic_b1": fit["analytic_b1"],
    "analytic_b1_x_sd_1": hyp_xsd1[0]["analytic_b1"] if hyp_xsd1 else None,
    "six_sizes": fit["six_sizes"],
    "six_sizes_x_sd_1": hyp_xsd1[0]["six_sizes"] if hyp_xsd1 else None,
    "dropped": {k: v for k, v in fit["dropped"].items() if k != "by_n"},
    "arithmetic": arith, "skewness": sk, "outlier_share": osh,
    "kernel_loglog_slope": {"x": kx["loglog_slope"], "z": kz["loglog_slope"]},
    "hypothesis_scores": hyp_scores,
    "figures_vs_table1": cross,
}
(out / "tables.json").write_text(json.dumps(tables, indent=1, ensure_ascii=False) + "\n")
doc = {"items": items, "item_list": [{"key": k.replace(".", "_"), **v} for k, v in items.items()]}
(out / "comparison.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
for k, v in items.items():
    if v["method"] == "pixels":
        p = v["pixels"]
        print(f"{k}: {p['published_near_ours']:.4f} / {p['ours_near_published']:.4f}  controls max {max(c['score'] for c in p['controls']):.4f}")
    elif v["method"] == "values":
        f = v["values"]["fields"]
        print(f"{k}: " + "; ".join(f"{x['expected']} vs {x['observed']}" for x in f))
    else:
        print(f"{k}: {v['check']['passed']} {v['check']['detail'][:150]}")

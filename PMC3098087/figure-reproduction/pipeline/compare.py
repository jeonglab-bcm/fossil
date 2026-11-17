#!/usr/bin/env python3
"""Compare every published value of PMC3098087 with our runs.

  compare.py published_values.json summary.csv comparison.json

Each published number (a figure point read from the vector PDF, or a printed table cell) is
compared with our mean over replicates. A field matches when

    |ours - paper| <= printed + z * sqrt(se_ours^2 + se_paper^2)

with se = SD / sqrt(replicates). The paper's SD is its printed SD where a table gives one, otherwise
ours; its replicates are 1,000 (simulations) and 500 (breast cancer data). 'printed' is half a unit
in the last printed digit for table cells and 0.0005 for figure points (the reading error of the
vector coordinates is below 0.0002). z is the Bonferroni value for a 5% chance of any false miss
in the item: z = Phi^-1(1 - 0.025 / fields). Prediction intervals (percentiles) match within one
step of their grid (1 / test size).

For each figure the same fields are also compared with a known-wrong series of ours (a control),
to show the comparison tells right from wrong.
"""

import csv
import json
import math
import sys
from statistics import NormalDist

NAN_STRINGS = {"NA", "NaN", "nan", ""}
MAP_ER = {"PA": "PA", "PA_ER+": "PA1", "PA_ER-": "PA2", "PV_ER+": "PV1", "PV_ER-": "PV2", "AUC": "AUC"}


def load_summary(path):
    s = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            s[(r["setting"], r["test"], r["method"], r["metric"])] = r
    return s


def num(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(x) else x


def zcrit(n):
    return NormalDist().inv_cdf(1 - 0.025 / max(n, 1))


def kfmt(k):
    return f"{k:.2f}"


def sim_key(rec, x):
    """Our setting, test set, classifier and measure for one published point."""
    f, cl = rec["figure"], rec["classifier"]
    if f == "fig1":
        return f"null_p40_k{kfmt(x)}", "match20", cl, rec["metric"]
    if f == "fig2":
        return f"null_p{rec['p']}_k{kfmt(x)}", "bal20", cl, "PA1"
    if f in ("fig3", "af4", "af5"):
        fam = "alt20" if rec["p_de"] == 20 else "altall"
        return f"{fam}_p{rec['p']}_k{kfmt(x)}", "bal20", cl, "PA1"
    if f in ("fig4", "af7"):
        return f"mu_{rec['center']}_k{rec['k1train']:.1f}_mu{x:.1f}", "bal20", cl, "PA"
    if f in ("fig5", "af8"):
        c = rec["correction"]
        name = {"none": "alt20", "over": "over", "down": "down", "multds": "multds"}[c]
        return f"{name}_p1000_k{kfmt(x)}", "bal20", cl, rec["metric"]
    if f == "af9":
        return f"af9_p1000_k{kfmt(x)}", rec["test"], cl, rec["metric"]
    if f == "af11":
        return f"alt20_p1000_k{kfmt(x)}", "bal20", cl, rec["metric"]
    raise KeyError(f)


def field(name, expected, mean, sd, n_ours, sd_paper, n_paper, printed, z, extra=None):
    out = {"name": name, "expected": expected}
    exp = num(expected)
    if mean is None and exp is None:
        out["observed"] = "NA"
        return out
    if mean is None or exp is None:
        out["observed"] = "NA" if mean is None else round(mean, 4)
        return out
    sdp = sd_paper if sd_paper is not None else sd
    se = math.sqrt((sd or 0) ** 2 / n_ours + (sdp or 0) ** 2 / n_paper)
    tol = printed + z * se
    out["observed"] = round(mean, 4)
    out["tolerance"] = {"abs": round(tol, 6)}
    out["z"] = round((mean - exp) / se, 2) if se > 0 else (0.0 if abs(mean - exp) <= printed else None)
    if extra:
        out.update(extra)
    return out


def ours(summary, key, strict=True):
    r = summary.get(key)
    if r is None:
        return None
    return {"mean": num(r["mean"] if strict else r["mean_avail"]), "mean_avail": num(r["mean_avail"]),
            "sd": num(r["sd"]), "n": int(r["n"]), "n_na": int(r["n_na"]),
            "q025": num(r["q025"]), "q975": num(r["q975"])}


def figure_item(recs, summary, n_paper=1000, control=None):
    pts = [(rec, x, y) for rec in recs for x, y in rec["points"]]
    z = zcrit(len(pts))
    fields, missing, ctrl_hits, ctrl_n = [], 0, 0, 0
    for rec, x, y in pts:
        key = sim_key(rec, x)
        o = ours(summary, key, strict=False)
        label = " ".join(str(rec[k]) for k in ("classifier", "correction", "center", "p_de", "p", "k1train", "metric") if k in rec)
        name = f"{label}, x = {x}"
        if o is None:
            missing += 1
            continue
        fields.append(field(name, f"{y:.4f}", o["mean"], o["sd"], o["n"], None, n_paper, 0.0005, z))
        if control:
            ck = control(rec, x, key)
            c = ours(summary, ck, strict=False) if ck else None
            if c is not None:
                ctrl_n += 1
                f = field(name, f"{y:.4f}", c["mean"], c["sd"], c["n"], None, n_paper, 0.0005, z)
                ctrl_hits += int(abs(f["observed"] - y) <= f["tolerance"]["abs"])
    hits = sum(1 for f in fields if "tolerance" in f and abs(f["observed"] - float(f["expected"])) <= f["tolerance"]["abs"])
    return {"fields": fields, "matched": hits, "n_fields": len(fields), "missing_settings": missing,
            "z": round(z, 3), "control": {"matched": ctrl_hits, "n": ctrl_n} if control else None}


def table_item(cells, summary, keyf, n_paper):
    z = zcrit(len(cells))
    fields, missing = [], 0
    for c in cells:
        key = keyf(c)
        o = ours(summary, key, strict=True)
        if o is None:
            missing += 1
            continue
        name = " ".join(str(c[k]) for k in ("classifier", "k1train", "ntest", "n_pos", "n_neg", "metric") if k in c)
        exp = "NA" if c["value"] in NAN_STRINGS else c["value"]
        sd_p = num(c.get("sd"))
        printed = 0.5 * 10 ** -len(exp.split(".")[1]) if "." in exp else 0.5
        f = field(name, exp, o["mean"], o["sd"], o["n"], sd_p, n_paper, printed, z,
                  {"mean_available": None if o["mean_avail"] is None else round(o["mean_avail"], 4),
                   "replicates_na": o["n_na"]})
        fields.append(f)
    hits = 0
    for f in fields:
        e, o = num(f["expected"]), num(f["observed"])
        if e is None and o is None:
            hits += 1
        elif e is not None and o is not None and abs(o - e) <= f["tolerance"]["abs"]:
            hits += 1
    return {"fields": fields, "matched": hits, "n_fields": len(fields), "missing_settings": missing, "z": round(z, 3)}


def pi_item(recs, summary, keyf, step):
    """Prediction intervals: our 2.5th and 97.5th percentiles against the plotted bar ends."""
    fields = []
    for rec in recs:
        for key, lo, hi, name in keyf(rec):
            o = ours(summary, key)
            if o is None:
                continue
            for end, val, q in (("lower", lo, o["q025"]), ("upper", hi, o["q975"])):
                if val is None or q is None:
                    continue
                fields.append({"name": f"{name}, {end}", "expected": f"{val:.3f}", "observed": round(q, 4),
                               "tolerance": {"abs": round(step + 0.0005, 4)}})
    hits = sum(1 for f in fields if abs(f["observed"] - float(f["expected"])) <= f["tolerance"]["abs"])
    return {"fields": fields, "matched": hits, "n_fields": len(fields)}


def main():
    pub = json.load(open(sys.argv[1]))
    summary = load_summary(sys.argv[2])
    figs, tabs = pub["figures"], pub["tables"]
    by = lambda name: [r for r in figs if r["figure"] == name]  # noqa: E731
    out = {}
    # Controls: a known-wrong series of ours for the same fields.
    out["fig1"] = figure_item(by("fig1"), summary,
                              control=lambda r, x, k: (k[0], "bal20", k[2], k[3]))  # balanced test set
    out["fig2"] = figure_item(by("fig2"), summary,
                              control=lambda r, x, k: (f"null_p40_k{kfmt(x)}", "bal20", k[2], "PA1") if r["p"] != 40
                              else (f"null_p10000_k{kfmt(x)}", "bal20", k[2], "PA1"))  # another p
    out["fig3"] = figure_item(by("fig3"), summary,
                              control=lambda r, x, k: (k[0].replace("alt20", "null").replace("altall", "null"), k[1], k[2], k[3])
                              if not k[0].startswith("altall") or x != 0.95 else None)  # the null case
    out["fig4"] = figure_item(by("fig4"), summary,
                              control=lambda r, x, k: (k[0].replace(f"mu_{r['center']}", "mu_" + ("variables" if r["center"] == "samples" else "samples")), k[1], k[2], k[3]))
    out["fig5"] = figure_item(by("fig5"), summary,
                              control=lambda r, x, k: (k[0].replace("multds", "down").replace("over", "alt20") if r["correction"] in ("multds", "over") else k[0].replace("down", "alt20").replace("alt20_p1000", "down_p1000") if r["correction"] == "none" else k[0].replace("down", "alt20"), k[1], k[2], k[3]))
    for af in ("af4", "af5", "af7", "af8", "af9", "af11"):
        out[af] = figure_item(by(af), summary)
    # Fig. 6: class-specific PA (%) of no correction and MultDS on the ER data, with PIs.
    f6 = []
    for r in by("fig6"):
        corr = r["correction"]
        name = f"er_{r['center']}_{corr}_neg{r['n_neg']}_pos{r['n_pos']}"
        f6.append({"figure": "fig6", "classifier": r["classifier"], "key": (name, "bal40", r["classifier"], MAP_ER[r["metric"]]),
                   "label": f"{r['classifier']} {r['center']} {corr} {r['n_pos']} ER+/{r['n_neg']} ER- {r['metric']}",
                   "value": r["value"] / 100, "lo": r["lo"] / 100 if r["lo"] is not None else None,
                   "hi": r["hi"] / 100 if r["hi"] is not None else None})
    z = zcrit(len(f6))
    fields = []
    for r in f6:
        o = ours(summary, r["key"], strict=False)
        if o is None:
            continue
        fields.append(field(r["label"], f"{r['value']:.4f}", o["mean"], o["sd"], o["n"], None, 500, 0.0005, z))
    hits = sum(1 for f in fields if abs(f["observed"] - float(f["expected"])) <= f["tolerance"]["abs"])
    out["fig6"] = {"fields": fields, "matched": hits, "n_fields": len(fields), "z": round(z, 3)}
    out["fig6.pi"] = pi_item(f6, summary, lambda r: [(r["key"], r["lo"], r["hi"], r["label"])], 0.05)
    # Additional file 12: the prediction intervals of Fig. 6 for all nine classifiers.
    out["af12"] = pi_item(by("af12"), summary, lambda r: [((f"er_{r['center']}_{r['correction']}_neg{r['n_neg']}_pos{r['n_pos']}", "bal40",
                                                             r["classifier"], MAP_ER[r["metric"]]), r["lo"] / 100, r["hi"] / 100,
                                                            f"{r['classifier']} {r['center']} {r['correction']} {r['n_pos']} ER+/{r['n_neg']} ER- {r['metric']}")], 0.05)
    # Additional file 10: PIs of the overall PA. The caption says 500 test samples; the bars sit on a
    # 0.05 grid, which a 20-sample test set gives. Both are compared.
    def af10_keys(test):
        def f(r):
            res = []
            for x, lo, hi in r["points"]:
                name = {"none": "alt20", "over": "over", "down": "down", "multds": "multds"}[r["correction"]]
                res.append(((f"{name}_p1000_k{kfmt(x)}", test, r["classifier"], "PA"), lo, hi,
                            f"{r['classifier']} {r['correction']} k = {x}"))
            return res
        return f
    out["af10"] = pi_item(by("af10"), summary, af10_keys("bal20"), 0.05)
    out["af10.ntest500"] = pi_item(by("af10"), summary, af10_keys("bal500"), 0.002)
    # Tables.
    t = lambda name: [c for c in tabs if c["table"] == name]  # noqa: E731
    out["af1"] = table_item(t("af1"), summary, lambda c: (f"null_p40_k{kfmt(c['k1train'])}", f"bal{c['ntest']}", c["classifier"], c["metric"]), 1000)
    out["af3"] = table_item(t("af3"), summary, lambda c: (f"alt20_p1000_k{kfmt(c['k1train'])}", f"bal{c['ntest']}", c["classifier"], c["metric"]), 1000)
    out["af13"] = table_item(t("af13"), summary, lambda c: (f"er_samples_none_neg{c['n_neg']}_pos{c['n_pos']}", "bal40", c["classifier"], MAP_ER[c["metric"]]), 500)
    out["af14"] = table_item(t("af14"), summary, lambda c: (f"er_samples_multds_neg{c['n_neg']}_pos{c['n_pos']}", "bal40", c["classifier"], MAP_ER[c["metric"]]), 500)
    json.dump(out, open(sys.argv[3], "w"), indent=1)
    for k, v in out.items():
        c = v.get("control")
        print(f"{k}: {v['matched']} of {v['n_fields']}" + (f" (missing settings {v['missing_settings']})" if v.get("missing_settings") else "")
              + (f"; control {c['matched']} of {c['n']}" if c else ""))


if __name__ == "__main__":
    main()

"""Compare our run with every number the paper prints or draws.

Usage: compare.py PUBLISHED.json FIGURES.json FIG1_READING.json ANALYSIS.json COMBINATIONS.npz
                  PUBLISHED_COMBINATIONS.json.gz OUT.json

Writes, for each item of results.json, the fields {name, expected, observed, tolerance}: expected is
the printed (or drawn) value as a string, observed ours. Tolerances:
  printed   half a unit in the last printed digit (counts, kappa, the point values of Tables 3 and 4);
  mc        a quantity that depends on random resampling (bootstrap intervals, the means and intervals
            over the 1,000 random splits): printed precision plus three standard deviations of the
            difference between two independent runs, measured from our own repeat runs;
  drawn     a value read from the vector drawing: the reading precision.
Also the controls and hypothesis tests the causes cite.
"""
import gzip
import json
import math
import sys

import numpy as np

from check_results import field_matches
from data import META, PRED, SINGLE

STATS = ["accuracy", "sensitivity", "specificity", "ppv", "npv", "composite"]
SHORT = {"accuracy": "acc", "sensitivity": "sens", "specificity": "spec", "ppv": "PPV", "npv": "NPV", "composite": "comp"}


def num(s):
    s = str(s).replace(",", "").strip()
    if s in ("NA", "NaN", ""):
        return math.nan
    return float(s.rstrip("%"))


def scale(stat, s):
    """Our fraction on the printed scale: percent for the rates, as is for the composite score."""
    return s if stat == "composite" else 100 * s


def ptol(expected):
    s = str(expected).replace(",", "").rstrip("%")
    d = len(s.split(".")[1]) if "." in s else 0
    return 0.5 * 10 ** (-d)


def fmt(v, digits=6):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "NA"
    return float(f"{v:.{digits}g}") if isinstance(v, float) else v


def field(name, expected, observed, tol=None):
    f = {"name": name, "expected": expected, "observed": fmt(observed) if not isinstance(observed, str) else observed}
    if tol is not None:
        f["tolerance"] = tol
    return f


def hits(fields):
    """How many fields match, by check_results.py's own rule."""
    return sum(field_matches(f, {"printed": True}) for f in fields)


def block(fields, **extra):
    return {"fields": fields, "summary": {"fields": len(fields), "match": hits(fields)}, **extra}


# --- Tables -----------------------------------------------------------------------------------------

def table1(pub, ours):
    f = []
    for g, vals in pub["table1"].items():
        for col, e, o in zip(("total", "neutral", "non-neutral", "uncertain"), vals, ours["table1"][g]):
            f.append(field(f"{g} {col}", e, o))
    return block(f)


def table2(pub, ours):
    f = []
    for p, classes in pub["table2"].items():
        for cls, vals in classes.items():
            o = ours["table2"][p].get(cls, [0, 0, 0, 0])
            for col, e, ov in zip(("neutral", "non-neutral", "uncertain", "total"), vals, o):
                f.append(field(f"{p} {cls} {col}", e, ov))
    return block(f)


def perf_points(pub_rows, ours_rows, label):
    f = []
    for p, row in pub_rows.items():
        for k in STATS:
            e = row[k][0]
            f.append(field(f"{p} {SHORT[k]}", e, scale(k, ours_rows[p][k]["value"])))
    return block(f)


def perf_cis(pub_rows, ours_rows):
    f = []
    for p, row in pub_rows.items():
        for k in STATS:
            for j, end in ((1, "low"), (2, "high")):
                e = row[k][j]
                o = ours_rows[p][k][end]
                sd = scale(k, ours_rows[p][k]["mc_sd"][j - 1])
                tol = ptol(e) + 3 * math.sqrt(2) * (0 if math.isnan(sd) else sd)
                f.append(field(f"{p} {SHORT[k]} {end}", e, scale(k, o) if not math.isnan(o) else math.nan,
                               {"abs": round(tol, 6)}))
    return f


# --- Kappa ------------------------------------------------------------------------------------------

def kappa_cmp(pub_block, ours_block):
    f = []
    for i, a in enumerate(PRED):
        for b in PRED[i:]:
            e = pub_block[a][b]
            o = ours_block[a][b]
            for j, part in enumerate(("kappa", "low", "high")):
                f.append(field(f"{a} / {b} {part}", e[j], o[j]))
    return f


def class_fields(rows, ours_tab, cols, vocab):
    """Rows ('class', counts...) in the order of Table 2, assigned to the predictors by walking: each
    predictor takes rows while their class is one of its classes and not taken yet."""
    f, i = [], 0
    for p in PRED:
        classes = {c.lower(): c for c in vocab[p]}
        classes.update({"n/a": "N/A", "no weights": "No weights", "no-call": "No-call"})
        taken = set()
        while i < len(rows) and rows[i][0].lower() in classes and rows[i][0].lower() not in taken:
            cls = rows[i][0]
            taken.add(cls.lower())
            o = ours_tab[p].get(classes[cls.lower()], [0] * (len(cols) + 1))
            for col, e, ov in zip(cols, rows[i][1:], o if len(cols) == len(o) else o[:len(cols)]):
                f.append(field(f"{p} {cls} {col}", e, ov))
            i += 1
    if i != len(rows):
        raise ValueError(f"class table: {len(rows) - i} rows not assigned, from {rows[i]}")
    return f


def kappa_bin(k):
    """The colour key of Fig. 1: negative, 0.01-0.2, ..., 0.81-1 (intervals closed on the right)."""
    for hi, name in ((0, "negative"), (0.2, "0.01-0.2"), (0.4, "0.21-0.4"), (0.6, "0.41-0.6"), (0.8, "0.61-0.8")):
        if k <= hi:
            return name
    return "0.81-1"


# --- Combinations -----------------------------------------------------------------------------------

def mc_spread(arr, key):
    """For each (subset, statistic, part) the RMS difference between our two runs over all combinations:
    the standard deviation of the difference between two independent runs."""
    out = {}
    for sub in ("subset1", "subset2"):
        for k in STATS:
            for part in ("mean", "low", "high"):
                a = arr[f"{key}|run1|{sub}|{k}|{part}"]
                b = arr[f"{key}|run2|{sub}|{k}|{part}"]
                d = (a - b)[~np.isnan(a - b)]
                out[(sub, k, part)] = float(np.sqrt(np.mean(d ** 2))) if len(d) else 0.0
    return out


def af17(pub_comb, arr, key):
    """Every mean of Additional file 17 (or 18) against ours, within the printed precision plus three
    standard deviations of the run-to-run difference of that combination's mean (its own spread over the
    splits / sqrt(splits) x sqrt(2)). Also the intervals, within three times the measured run-to-run RMS
    difference of interval ends. Controls: the same comparison against the other data set's run, and
    against our second run's means with no Monte Carlo allowance."""
    names = list(arr[f"{key}|names"])
    spread = mc_spread(arr, key)
    res = {"means": {}, "intervals": {}}
    total = ok = itot = iok = 0
    for sub in ("subset1", "subset2"):
        for k in STATS:
            m = arr[f"{key}|run1|{sub}|{k}|mean"]
            sd = arr[f"{key}|run1|{sub}|{k}|sd"]
            n = arr[f"{key}|run1|{sub}|{k}|n"]
            lo = arr[f"{key}|run1|{sub}|{k}|low"]
            hi = arr[f"{key}|run1|{sub}|{k}|high"]
            c = ci = t = it = 0
            for i, nm in enumerate(names):
                e = pub_comb[nm][sub][k]
                mean_e = num(e[0])
                o = scale(k, m[i])
                if math.isnan(mean_e) and math.isnan(o):
                    c += 1
                else:
                    tol = ptol(e[0]) + 3 * math.sqrt(2) * scale(k, (sd[i] if not math.isnan(sd[i]) else 0)) / math.sqrt(max(n[i], 1))
                    c += abs(mean_e - o) <= tol + 1e-9
                t += 1
                for j, arr_ in ((1, lo), (2, hi)):
                    ev = num(e[j])
                    ov = scale(k, arr_[i])
                    part = "low" if j == 1 else "high"
                    if math.isnan(ev) and math.isnan(ov):
                        ci += 1
                    else:
                        tol = ptol(e[j]) + 3 * scale(k, spread[(sub, k, part)])
                        ci += abs(ev - ov) <= tol + 1e-9
                    it += 1
            res["means"][f"{sub} {k}"] = [c, t]
            res["intervals"][f"{sub} {k}"] = [ci, it]
            ok += c
            total += t
            iok += ci
            itot += it
    res["summary"] = {"means_within": ok, "means": total, "intervals_within": iok, "intervals": itot}
    return res


def af17_control(pub_comb, arr, key):
    """Our means of the other data set against this file, same tolerance: a wrong-input control."""
    names = list(arr[f"{key}|names"])
    ok = total = 0
    for sub in ("subset1", "subset2"):
        for k in STATS:
            m = arr[f"{key}|run1|{sub}|{k}|mean"]
            sd = arr[f"{key}|run1|{sub}|{k}|sd"]
            n = arr[f"{key}|run1|{sub}|{k}|n"]
            for i, nm in enumerate(names):
                e = pub_comb[nm][sub][k][0]
                o = scale(k, m[i])
                me = num(e)
                if math.isnan(me) and math.isnan(o):
                    ok += 1
                else:
                    tol = ptol(e) + 3 * math.sqrt(2) * scale(k, (sd[i] if not math.isnan(sd[i]) else 0)) / math.sqrt(max(n[i], 1))
                    ok += abs(me - o) <= tol + 1e-9
                total += 1
    return [ok, total]


def af19_arith(pub, pub_comb, af, tab, col0):
    """Additional file 19's counts recomputed from the paper's own Additional file 17 (or 18) and
    Table 3 (or 4): the arithmetic check of the rule (mean above the best predictor's value; significant
    when the low end of the combination's interval reaches the high end of the best predictor's)."""
    T = {p: {k: [num(x) for x in v] for k, v in pub[tab][p].items()} for p in pub[tab]}
    out = {}
    for grp, names in (("single", SINGLE), ("meta", META)):
        for k in STATS:
            best = max(names, key=lambda p: (T[p][k][0], -names.index(p)))
            res = {}
            for kind in ("mean", "significant"):
                c1 = c2 = cb = 0
                for nm, v in pub_comb[af].items():
                    if kind == "mean":
                        a = num(v["subset1"][k][0]) > T[best][k][0]
                        b = num(v["subset2"][k][0]) > T[best][k][0]
                    else:
                        a = num(v["subset1"][k][1]) >= T[best][k][2]
                        b = num(v["subset2"][k][1]) >= T[best][k][2]
                    c1, c2, cb = c1 + a, c2 + b, cb + (a and b)
                res[kind] = [c1, c2, cb]
            out[f"{grp} {k}"] = {"reference": best, **res}
    return out


def af19(pub, ours, key, col0, run="run1"):
    f = []
    c = ours["combinations"][key][run]["counts"]
    cols = ["subset 1", "subset 2", "both"]
    for grp in ("single", "meta"):
        for k in STATS:
            for kind in ("mean", "significant"):
                for j in range(3):
                    f.append(field(f"vs best {grp}, {SHORT[k]}, {'mean higher' if kind == 'mean' else 'significant'}, {cols[j]}",
                                   pub["af19"][grp][k][kind][col0 + j], c[grp][k][kind][j]))
    return f


def comb_stats_fields(prefix, pub_row, ours_row, spread, sub):
    f = []
    for k in STATS:
        for j, part in enumerate(("mean", "low", "high")):
            e = pub_row[k][j].rstrip("%")
            o = scale(k, ours_row[k][j])
            tol = ptol(e) + 3 * scale(k, spread[(sub, k, part)])
            f.append(field(f"{prefix} {SHORT[k]}{'' if part == 'mean' else ' ' + part}", e, o, {"abs": round(tol, 6)}))
    return f


def top_tables(pub_t, ours, key, perf, arr):
    """Additional files 21 and 22: the five names in rank order, their statistics, and the best single
    and meta-predictor (names and their Table 3/4 values)."""
    spread = mc_spread(arr, key)
    names = list(arr[f"{key}|names"])
    f = []
    run = ours["combinations"][key]["run1"]
    for blk, d in pub_t.items():
        sub, by = blk.split("/")
        ours_top = run["top5"][blk]
        for r, (p_row, o_row) in enumerate(zip(d["top5"], ours_top), 1):
            f.append(field(f"{sub}, by {by}, rank {r}", p_row["name"], o_row["name"]))
        for r, p_row in enumerate(d["top5"], 1):
            # The statistics of the published combination, from our run (whatever rank it has in ours).
            i = names.index(p_row["name"])
            o_row = {k: [float(arr[f"{key}|run1|{sub}|{k}|{part}"][i]) for part in ("mean", "low", "high")] for k in STATS}
            f += comb_stats_fields(f"{sub}, by {by}, {p_row['name']}:", p_row, o_row, spread, sub)
        for role in ("best_single", "best_meta"):
            nm = d[role]["name"].split(" [")[0]
            grp = SINGLE if role == "best_single" else META
            ours_best = max(grp, key=lambda p: (perf[p][by]["value"], -grp.index(p)))
            f.append(field(f"{sub}, by {by}, {role.replace('_', ' ')}", nm, ours_best))
    return f


def recurrence_fields(fig4_pub, ours, key, by="composite"):
    f = []
    run = ours["combinations"][key]["run1"]["recurrence"]
    for sub in ("subset1", "subset2"):
        for p in SINGLE:
            for j, t in enumerate(("10", "20", "50", "100")):
                e = fig4_pub[sub]["series"][p][j]
                if e is None:
                    continue
                f.append(field(f"{sub} top {t} {p}", f"{round(e):d}", run[f"{sub}/{by}"][t][p], {"abs": 0.5}))
    return f


def optimal_fields(pub_o, ours, key):
    f = []
    o = ours["combinations"][key]["run1"]["optimal"]
    for part, keyname in (("by_p", "p"), ("by_n", "n")):
        ours_by = {str(r[keyname]): r for r in o[part]}
        for r in pub_o[part]:
            q = ours_by[r[keyname]]
            other = "n" if keyname == "p" else "p"
            f.append(field(f"{keyname} = {r[keyname]}: best {other}", r[other], str(q[other])))
            f.append(field(f"{keyname} = {r[keyname]}: combination", r["name"], q["name"]))
    return f


# --- Figures ----------------------------------------------------------------------------------------

def fig1_kappa(cells, rows, kappa):
    f = []
    for j, a in enumerate(rows):
        for i, b in enumerate(rows):
            f.append(field(f"{a} / {b}", cells[j][i]["bin"], kappa_bin(kappa[a][b][0])))
    return f


def fig1_calls(reading, fig, clustering, tol):
    f = []
    ours_cl = {frozenset(c) for c in clustering["clades"]}
    for c in reading["clades"]:
        f.append(field("clade " + ", ".join(sorted(c)), "present", "present" if frozenset(c) in ours_cl else "absent"))
    h = clustering["height"]
    for j, (e, o) in enumerate(zip(fig["dendrogram"]["relative_heights"], sorted(v / h[-1] for v in h))):
        if j < len(h) - 1:
            f.append(field(f"join {j + 1} of {len(h)}, height relative to the root", f"{e:.4f}", o, {"abs": 0.0005}))
    for j, p in enumerate(reading["rows"]):
        for k in ("non-neutral", "neutral", "no call"):
            f.append(field(f"{p} share {k}", f"{fig['rows'][j][k]:.4f}", clustering["row_shares"][p][k], {"abs": tol}))
    return f


def fig2_fields(fig, ours_rows, draw_tol, mc=False):
    f = []
    for k in STATS:
        sub = fig[k]
        for b in sub["bars"]:
            p = b["name"]
            if b.get("absent"):
                # No bar drawn: a value of zero, or none (a statistic with no denominator).
                v = ours_rows[p][k]["value"]
                if not mc:
                    f.append(field(f"{p} {SHORT[k]}", "no bar", "no bar" if (math.isnan(v) or abs(v) < 1e-12) else v))
                continue
            if not mc:
                tol = draw_tol * (4 if k == "composite" else 1)
                f.append(field(f"{p} {SHORT[k]}", f"{b['value']:.4f}", ours_rows[p][k]["value"], {"abs": tol}))
            else:
                for end in ("low", "high"):
                    if end not in b:
                        continue
                    sd = ours_rows[p][k]["mc_sd"][0 if end == "low" else 1]
                    tol = draw_tol * (4 if k == "composite" else 1) + 3 * math.sqrt(2) * (0 if math.isnan(sd) else sd)
                    f.append(field(f"{p} {SHORT[k]} {end}", f"{b[end]:.4f}", ours_rows[p][k][end], {"abs": round(tol, 6)}))
    return f


def fig3_fields(fig, ours, key, sub, arr, perf, draw_tol, by="composite"):
    """Fig. 3 panel: the five combinations named in its legend (in rank order, ranked by composite score),
    then the 7 bars of each statistic: the five combinations, the best single and the best
    meta-predictor (by composite score), with their error bars."""
    spread = mc_spread(arr, key)
    names = list(arr[f"{key}|names"])
    run = ours["combinations"][key]["run1"]
    f = []
    for r, (e, o) in enumerate(zip(fig["combinations"], run["top5"][f"{sub}/{by}"]), 1):
        f.append(field(f"rank {r}", e, o["name"]))
    best_s = max(SINGLE, key=lambda p: perf[p][by]["value"])
    best_m = max(META, key=lambda p: perf[p][by]["value"])
    for k in STATS:
        bars = fig[k]["bars"]
        for j, b in enumerate(bars):
            if j < 5:
                i = names.index(fig["combinations"][j])
                vals = [float(arr[f"{key}|run1|{sub}|{k}|{part}"][i]) for part in ("mean", "low", "high")]
                label = f"#{j + 1}"
                tols = [3 * spread[(sub, k, part)] for part in ("mean", "low", "high")]
            else:
                p = best_s if j == 5 else best_m
                vals = [perf[p][k]["value"], perf[p][k]["low"], perf[p][k]["high"]]
                label = p
                tols = [0.0] + [3 * math.sqrt(2) * (perf[p][k]["mc_sd"][q] or 0) for q in (0, 1)]
            dt = draw_tol * (4 if k == "composite" else 1)
            f.append(field(f"{label} {SHORT[k]}", f"{b['value']:.4f}", vals[0], {"abs": round(dt + tols[0], 6)}))
            for end, v, t in (("low", vals[1], tols[1]), ("high", vals[2], tols[2])):
                if end in b:
                    f.append(field(f"{label} {SHORT[k]} {end}", f"{b[end]:.4f}", v, {"abs": round(dt + t, 6)}))
    # Significance marks: stars on the ranking statistic's panel, triangles on the NPV panel.
    for k in (by, "npv"):
        marks = fig[k]["markers"]["per_bar"]
        for j, nm in enumerate(fig["combinations"][:5]):
            i = names.index(run["top5"][f"{sub}/{by}"][j]["name"])
            low = float(arr[f"{key}|run1|{sub}|{k}|low"][i])
            for kind, ref in (("vs best single", best_s), ("vs best meta", best_m)):
                ours_mark = "yes" if low >= perf[ref][k]["high"] else "no"
                f.append(field(f"#{j + 1} {SHORT[k]} mark {kind}", "yes" if marks[j][kind] else "no", ours_mark))
    return f


def main():
    pub_p, figs_p, reading_p, ours_p, npz_p, comb_p, out = sys.argv[1:8]
    pub = json.load(open(pub_p))
    figs = json.load(open(figs_p))
    reading = json.load(open(reading_p))
    ours = json.load(open(ours_p))
    arr = dict(np.load(npz_p))
    with gzip.open(comb_p, "rt", encoding="utf-8") as fh:
        pub_comb = json.load(fh)
    res = {}
    res["table1"] = table1(pub, ours)
    res["table2"] = table2(pub, ours)
    res["table3"] = perf_points(pub["table3"], ours["table3"], "989")
    res["table3.ci"] = block(perf_cis(pub["table3"], ours["table3"]))
    res["table4"] = perf_points(pub["table4"], ours["table4"], "297")
    res["table4.ci"] = block(perf_cis(pub["table4"], ours["table4"]))
    gc = {"oncogenes": {}, "tsg": {}}
    for cls in gc:
        rows = {p: {k: [x.rstrip("%") for x in v] for k, v in r.items()} for p, r in pub["af16"][cls].items()}
        gc[cls] = rows
    res["af16"] = block(perf_points(gc["oncogenes"], ours["gene_classes"]["oncogenes"], "")["fields"]
                        + perf_points(gc["tsg"], ours["gene_classes"]["tsg"], "")["fields"])
    for f, cls in zip(res["af16"]["fields"], ["oncogenes"] * 90 + ["TSGs"] * 90):
        f["name"] = f"{cls}: {f['name']}"
    res["af16.ci"] = block([dict(f, name="oncogenes: " + f["name"]) for f in perf_cis(gc["oncogenes"], ours["gene_classes"]["oncogenes"])]
                           + [dict(f, name="TSGs: " + f["name"]) for f in perf_cis(gc["tsg"], ours["gene_classes"]["tsg"])])
    for key, sets in (("af3", ("all", "non_cosmic")), ("af5", ("labelled", "labelled_non_cosmic")),
                      ("af11", ("all", "non_cosmic")), ("af13", ("labelled", "labelled_non_cosmic"))):
        src = ours["kappa_low_confidence"] if key in ("af11", "af13") else ours["kappa"]
        fields = []
        for part, s in zip(("first", "second"), sets):
            fields += [dict(f, name=f"{s}: {f['name']}") for f in kappa_cmp(pub[key][part], src[s])]
        res[key] = block(fields)
    # Additional file 8: three-category call table.
    f8 = []
    for s in ("all", "non_cosmic"):
        for p, classes in pub["af8"][s].items():
            for cls, vals in classes.items():
                key = "Low confidence" if "Low confidence" in cls else cls
                o = ours["low_confidence_table"][s][p].get(_class_key(p, key), [0, 0, 0, 0])
                for col, e, ov in zip(("neutral", "non-neutral", "uncertain", "total"), vals, o):
                    f8.append(field(f"{s}: {p} {cls} {col}", e, ov))
    res["af8"] = block(f8)
    f9 = []
    sets = ("all", "non_cosmic", "labelled", "labelled_non_cosmic")
    for cnt, vals in pub["af9"]["by_count"].items():
        for s, e in zip(sets, vals):
            f9.append(field(f"{s}: {cnt} low-confidence calls", e, ours["low_confidence"][s]["by_count"][int(cnt)]))
    for (s, lst) in zip(sets, pub["af9"]["majority"].values()):
        e = "; ".join(f"{g} ({', '.join(sorted(v))})" for g, v in sorted(lst.items()))
        o = "; ".join(f"{g} ({', '.join(sorted(v))})" for g, v in sorted(ours["low_confidence"][s]["majority"].items()))
        f9.append(field(f"{s}: majority vote of low confidence", e, o))
    res["af9"] = block(f9)
    res["af6"] = block([field(f"{g} {col}", e, o) for g, v in pub["af6"].items()
                        for col, e, o in zip(("total", "neutral", "non-neutral", "uncertain"), v, ours["table1_non_cosmic"][g])])
    res["af7"] = block(class_fields(pub["af7"], ours["table2_non_cosmic"], ("neutral", "non-neutral", "uncertain", "total"), ours["table2"]))
    res["af14"] = block([dict(f, name=f"{cls}: {f['name']}") for cls in ("oncogenes", "tsg", "new")
                         for f in class_fields(pub["af14"][cls], ours["table2_by_class"][cls], ("neutral", "non-neutral"), ours["table2"])])
    res["af28"] = block([field(f"{p} {col}", e, o) for p, v in pub["af28"].items()
                         for col, e, o in zip(("989", "297"), v, ours["training_sets"][p])])
    # Combinations.
    res["af17"] = af17(pub_comb["af17"], arr, "all")
    res["af18"] = af17(pub_comb["af18"], arr, "non_cosmic")
    res["af17"]["control_other_set"] = af17_control(pub_comb["af17"], arr, "non_cosmic")
    res["af18"]["control_other_set"] = af17_control(pub_comb["af18"], arr, "all")
    res["af19"] = block(af19(pub, ours, "all", 0) + [dict(f, name="non-COSMIC: " + f["name"]) for f in af19(pub, ours, "non_cosmic", 3)])
    res["af19"]["second_run"] = hits(af19(pub, ours, "all", 0, "run2") + af19(pub, ours, "non_cosmic", 3, "run2"))
    res["af19"]["arithmetic"] = {"all": af19_arith(pub, pub_comb, "af17", "table3", 0), "non_cosmic": af19_arith(pub, pub_comb, "af18", "table4", 3)}
    res["af21"] = block(top_tables(pub["af21"], ours, "all", ours["table3"], arr))
    res["af22"] = block(top_tables(pub["af22"], ours, "non_cosmic", ours["table4"], arr))
    res["af25"] = block(optimal_fields(pub["af25"], ours, "all"))
    res["af27"] = block(optimal_fields(pub["af27"], ours, "non_cosmic"))
    # Figures.
    draw_tol = 0.0005
    res["fig1a"] = block(fig1_calls(reading["a"], figs["fig1"]["a"], ours["clustering"]["all"], 0.01))
    res["fig1c"] = block(fig1_calls(reading["c"], figs["fig1"]["c"], ours["clustering"]["non_cosmic"], 0.01))
    res["fig1b"] = block(fig1_kappa(figs["fig1"]["b"]["cells"], reading["a"]["rows"], ours["kappa"]["all"]))
    res["fig1d"] = block(fig1_kappa(figs["fig1"]["d"]["cells"], reading["c"]["rows"], ours["kappa"]["non_cosmic"]))
    res["fig2a"] = block(fig2_fields(figs["fig2"]["a"], ours["table3"], draw_tol))
    res["fig2a.ci"] = block(fig2_fields(figs["fig2"]["a"], ours["table3"], draw_tol, mc=True))
    res["fig2b"] = block(fig2_fields(figs["fig2"]["b"], ours["table4"], draw_tol))
    res["fig2b.ci"] = block(fig2_fields(figs["fig2"]["b"], ours["table4"], draw_tol, mc=True))
    for panel, key, sub, perf in (("a", "all", "subset1", ours["table3"]), ("b", "all", "subset2", ours["table3"]),
                                  ("c", "non_cosmic", "subset1", ours["table4"]), ("d", "non_cosmic", "subset2", ours["table4"])):
        res[f"fig3{panel}"] = block(fig3_fields(figs["fig3"][panel], ours, key, sub, arr, perf, draw_tol))
    for panel, cls in (("a", "oncogenes"), ("b", "tsg")):
        res[f"af15{panel}"] = block(fig2_fields(figs["af15"][panel], ours["gene_classes"][cls], draw_tol))
        res[f"af15{panel}.ci"] = block(fig2_fields(figs["af15"][panel], ours["gene_classes"][cls], draw_tol, mc=True))
    for panel, key, sub, perf in (("a", "all", "subset1", ours["table3"]), ("b", "all", "subset2", ours["table3"]),
                                  ("c", "non_cosmic", "subset1", ours["table4"]), ("d", "non_cosmic", "subset2", ours["table4"])):
        res[f"af20{panel}"] = block(fig3_fields(figs["af20"][panel], ours, key, sub, arr, perf, draw_tol, by="accuracy"))
    res["fig4a"] = block(recurrence_fields(figs["fig4"]["a"], ours, "all"))
    res["fig4b"] = block(recurrence_fields(figs["fig4"]["b"], ours, "non_cosmic"))
    for n, src, sets in ((4, "kappa", ("labelled", "labelled_non_cosmic")), (10, "kappa_low_confidence", ("all", "non_cosmic")),
                         (12, "kappa_low_confidence", ("labelled", "labelled_non_cosmic"))):
        f = []
        for part, st in zip(("first", "second"), sets):
            g = figs[f"af{n}"][part]
            f += [dict(x, name=f"{st}: {x['name']}") for x in fig1_kappa([[{"bin": b} for b in row] for row in g["bins"]], g["rows"], ours[src][st])]
        res[f"af{n}"] = block(f)
    src29 = {"all": ours["table3"], "non_cosmic": ours["table4"], "excluding_training": ours["training_excluded"]}
    f29, c29 = [], []
    for pred, panel in figs["af29"].items():
        for series, stats in panel["bars"].items():
            for k in STATS:
                b = stats[k]
                r = src29[series][pred][k]
                dt = draw_tol * (4 if k == "composite" else 1)
                f29.append(field(f"{pred}, {series.replace('_', ' ')}, {SHORT[k]}", f"{b['value']:.4f}", r["value"], {"abs": dt}))
                for end, j in (("low", 0), ("high", 1)):
                    if end in b:
                        sd = r["mc_sd"][j]
                        c29.append(field(f"{pred}, {series.replace('_', ' ')}, {SHORT[k]} {end}", f"{b[end]:.4f}", r[end],
                                         {"abs": round(dt + 3 * math.sqrt(2) * (0 if math.isnan(sd) else sd), 6)}))
    res["af29"] = block(f29)
    res["af29.ci"] = block(c29)
    res["af24"] = block(boxplot_fields(figs["af24"], arr, "all"))
    res["af26"] = block(boxplot_fields(figs["af26"], arr, "non_cosmic"))
    res["af23a"] = block(recurrence_fields(figs["af23"]["a"], ours, "all", by="accuracy"))
    res["af23b"] = block(recurrence_fields(figs["af23"]["b"], ours, "non_cosmic", by="accuracy"))
    res["fig4a"]["second_run"] = hits(recurrence_fields_run(figs["fig4"]["a"], ours, "all", "run2"))
    res["fig4b"]["second_run"] = hits(recurrence_fields_run(figs["fig4"]["b"], ours, "non_cosmic", "run2"))
    res["fig4_arithmetic"] = fig4_arithmetic(figs, pub_comb)
    res["af23_arithmetic"] = fig4_arithmetic(figs, pub_comb, "af23", "accuracy")
    res["controls"] = controls(pub, figs, reading, ours)
    # Top-level keys without dots: the repository's results check reads key paths split at dots.
    res = {k.replace(".", "_"): v for k, v in res.items()}
    with open(out, "w") as fh:
        json.dump(res, fh, indent=1, default=lambda v: v.item() if hasattr(v, "item") else str(v))
        fh.write("\n")
    for k, v in res.items():
        if isinstance(v, dict) and "summary" in v:
            print(f"{k:10s} {v['summary']}", file=sys.stderr)


def fivenum(v):
    """Tukey's five numbers (R's fivenum, the hinges of boxplot)."""
    v = np.sort(np.asarray(v, dtype=float))
    n = len(v)
    n4 = math.floor((n + 3) / 2) / 2
    d = [1, n4, (n + 1) / 2, n + 1 - n4, n]
    return [0.5 * (v[math.floor(x) - 1] + v[math.ceil(x) - 1]) for x in d]


def boxplot_fields(panels, arr, key):
    """Additional files 24 and 26. The panels titled 'n=k' hold the combinations with p = k (the file
    names p 'n'), one box per n; those titled 'p=k' the combinations with n = k, one box per p. The
    boxes are of the combinations' mean accuracy in subset 1 (percent), in increasing order of the
    other parameter. Tolerance: the reading precision (0.01 point) plus three times the run-to-run RMS
    difference of a combination's mean accuracy."""
    names = list(arr[f"{key}|names"])
    acc = 100 * arr[f"{key}|run1|subset1|accuracy|mean"]
    tol = round(0.01 + 3 * 100 * mc_spread(arr, key)[("subset1", "accuracy", "mean")], 4)
    pn = [(int(nm.split(" of ")[0].split()[-1]), len(nm.split(" of ", 1)[1].split(", "))) for nm in names]
    f = []
    for panel in panels:
        var, k = panel["title"]
        if var == "n":   # p = k, boxes for n = max(2, k) .. 11
            others = list(range(max(2, k), 12))
            group = lambda o: [i for i, (pp, nn) in enumerate(pn) if pp == k and nn == o]
            lab = lambda o: f"p = {k}, n = {o}"
        else:            # n = k, boxes for p = 1 .. k
            others = list(range(1, k + 1))
            group = lambda o: [i for i, (pp, nn) in enumerate(pn) if nn == k and pp == o]
            lab = lambda o: f"n = {k}, p = {o}"
        if len(panel["groups"]) != len(others):
            raise ValueError(f"box plot panel {panel['title']}: {len(panel['groups'])} boxes, {len(others)} groups")
        for g, o in zip(panel["groups"], others):
            q = fivenum(acc[group(o)])
            for part, j in (("lower hinge", 1), ("median", 2), ("upper hinge", 3)):
                if g.get(part.split()[0] if part != "median" else "median") is None:
                    continue
                e = g["median"] if part == "median" else g["lower" if part.startswith("lower") else "upper"]
                f.append(field(f"{lab(o)}, {part}", f"{e:.3f}", q[j], {"abs": tol}))
    return f


def fig4_arithmetic(figs, pub_comb, key="fig4", by="composite"):
    """Fig. 4 recomputed from the composite means printed in Additional files 17 and 18 (ranked, ties in
    the order of the file): is the figure what the paper's own table gives?"""
    fields = []
    for af, panel in (("af17", "a"), ("af18", "b")):
        names = list(pub_comb[af])
        for sub in ("subset1", "subset2"):
            v = np.array([num(pub_comb[af][n][sub][by][0]) for n in names])
            order = np.argsort(-v, kind="stable")
            for j, t in enumerate((10, 20, 50, 100)):
                top = [names[i].split(" of ", 1)[1].split(", ") for i in order[:t]]
                for p in SINGLE:
                    e = figs[key][panel][sub]["series"][p][j]
                    if e is None:
                        continue
                    fields.append(field(f"{panel} {sub} top {t} {p}", f"{round(e):d}", 100 * sum(p in m for m in top) / t, {"abs": 0.5}))
    return {"fields": len(fields), "match": hits(fields)}


def recurrence_fields_run(fig, ours, key, run):
    alt = json.loads(json.dumps(ours))
    alt["combinations"][key]["run1"] = alt["combinations"][key][run]
    return recurrence_fields(fig, alt, key)


def _class_key(p, cls):
    """Additional file 8's class names to ours (case and the 'No weights/' and 'No-call/' prefixes)."""
    m = {"high": "High", "medium": "Medium", "neutral": "Neutral", "functional": "Functional",
         "disease_causing": "Disease_causing", "disease_causing_automatic": "Disease_causing_automatic",
         "polymorphism": "Polymorphism", "polymorphism_automatic": "Polymorphism_automatic",
         "probably damaging": "Probably damaging", "benign": "Benign"}
    return m.get(cls, cls)


def controls(pub, figs, reading, ours):
    """Wrong-input controls for the comparisons that could pass by accident: the other data set's
    numbers scored against each published block with the same tolerances."""
    out = {}
    out["table3_with_table4_values"] = hits(perf_points(pub["table3"], ours["table4"], "")["fields"])
    out["table4_with_table3_values"] = hits(perf_points(pub["table4"], ours["table3"], "")["fields"])
    out["fig1b_with_non_cosmic_kappa"] = hits(fig1_kappa(figs["fig1"]["b"]["cells"], reading["a"]["rows"], ours["kappa"]["non_cosmic"]))
    out["fig1d_with_all_kappa"] = hits(fig1_kappa(figs["fig1"]["d"]["cells"], reading["c"]["rows"], ours["kappa"]["all"]))
    out["fig1a_shares_with_non_cosmic"] = hits(fig1_calls(reading["a"], figs["fig1"]["a"], ours["clustering"]["non_cosmic"], 0.01)[26:])
    out["fig2a_with_table4_values"] = hits(fig2_fields(figs["fig2"]["a"], ours["table4"], 0.0005))
    out["fig4a_with_non_cosmic"] = hits(recurrence_fields(figs["fig4"]["a"], {"combinations": {"all": ours["combinations"]["non_cosmic"]}}, "all"))
    return out


if __name__ == "__main__":
    main()

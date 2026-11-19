"""Compare our simulation and our OIS with every printed cell of Tables 1-4, S3 and S4.

Usage: tables.py PUBLISHED_VALUES.json SIMULATION.json OUT.json

1. Read-off settings the paper does not state: the binning rule (an estimate counts at the point its
   cumulative count rounds to, or in the interval it falls in, or once per meta-analysis at an edge), the read-off rule (the first
   point below the level, or the point after which the curve stays below) and the interval width of each
   table. Every combination is scored against Tables 1, S3 and S4 together, and the one that matches most
   printed cells is used (a search, so every simulation table carries a found_by_search assumption).
2. Tables 1, S3, S4: our required numbers of patients and events, per cell, with the chosen settings; the
   same with our second run (other seeds), to measure how far chance alone moves a read-off; and the
   hypothesis variants (zero-cell rule, binomial on the whole trial).
3. Table 2: the 72 OIS values of the formula, rounded as Table 2's cells are (and as its footnote says).
4. Tables 3 and 4: the OIS columns from our Table 2 (min to max over I^2); the simulation columns against
   every range rule tried on the paper's own Tables 1, S3 and S4.
"""
import itertools
import json
import sys

import numpy as np

from oisim.core import PC_MIDPOINTS, format_required, ois, required_number, round_ois, round_ois_footnote

CAPS = {"patients": 50000, "events": 5000}
LEVELS = ("10", "5", "1")
TAUS = ("0.05", "0.15", "0.25")
# Which simulated scenarios each table reports.
TABLE_SCENARIOS = {"table1": ("cochrane", ("1-5", "5-15")), "tableS4": ("common", ("1-5", "5-15")),
                   "tableS3": ("common", ("15-40", "40-80"))}
WIDTHS = {"patients": (100, 200, 500), "events": (10, 20, 50)}


def key_of(sizes, pc, tau, rrr):
    return f"{sizes}_pc{pc}_tau{float(tau):.2f}_rrr{int(rrr)}"


def curve(run, rule, axis, width, th):
    """Proportion above the threshold at each point of the given spacing."""
    c = run["curves"][rule][axis][str(width)]
    n = np.array(c["n"], float)
    h = np.array(c[f"over{th}"], float)
    x = np.arange(1, len(n) + 1) * width
    with np.errstate(invalid="ignore", divide="ignore"):
        p = np.where(n > 0, h / np.maximum(n, 1), np.nan)
    return x, p, n


def read_off(run, rule, read, axis, width, th, level):
    x, p, _ = curve(run, rule, axis, width, th)
    v = required_number(x, p, int(level) / 100, rule=read)
    if v is not None and v == x[0] and p[0] < int(level) / 100 and axis == "patients" and width == 100:
        return f"<{int(x[0])}"  # S3 prints '<100' for a curve already below the level at its first point
    return format_required(v, CAPS[axis])


def table_cells(runs, table, rule, read, pw, ew):
    sizes, pcs = TABLE_SCENARIOS[table]
    out = {}
    for rrr in ("0", "10"):
        for th in ("30", "20"):
            for pc in pcs:
                for tau in TAUS:
                    run = runs[key_of(sizes, pc, tau, rrr)]
                    out[f"{rrr}|{th}|{pc}|{tau}"] = [read_off(run, rule, read, "patients", pw, th, lv) for lv in LEVELS] + \
                                                   [read_off(run, rule, read, "events", ew, th, lv) for lv in LEVELS]
    return out


def num(s):
    try:
        return float(str(s).lstrip("<>"))
    except ValueError:
        return None


def fields_of(table, published, ours, second=None, widths=None):
    fields = []
    for k, exp_row in published.items():
        rrr, th, pc, tau = k.split("|")
        for j, exp in enumerate(exp_row):
            axis = "patients" if j < 3 else "events"
            name = f"RRR {rrr}%, RRR>{th}%, PC {pc}%, tau2 {tau}, {axis} for {LEVELS[j % 3]}%"
            f = {"name": name, "expected": exp, "observed": ours[k][j]}
            if second is not None:
                f["second_run"] = second[k][j]
            a, b = num(exp), num(ours[k][j])
            if widths and a is not None and b is not None:
                f["bins_off"] = round(abs(a - b) / widths[axis], 2)
            fields.append(f)
    return fields


def count(fields, key="observed"):
    return sum(f[key] == f["expected"] for f in fields)


def summary(fields, widths):
    n = len(fields)
    exact = count(fields)
    one = sum(1 for f in fields if f["observed"] == f["expected"] or (f.get("bins_off") is not None and f["bins_off"] <= 1))
    two = sum(1 for f in fields if f["observed"] == f["expected"] or (f.get("bins_off") is not None and f["bins_off"] <= 2))
    s = {"fields": n, "exact": exact, "within_one_bin": one, "within_two_bins": two}
    if fields and "second_run" in fields[0]:
        s["second_run_exact"] = count(fields, "second_run")
        s["runs_agree"] = sum(f["observed"] == f["second_run"] for f in fields)
    lo = sum(1 for f in fields if num(f["observed"]) is not None and num(f["expected"]) is not None
             and f["observed"] != f["expected"] and num(f["observed"]) < num(f["expected"]))
    hi = sum(1 for f in fields if num(f["observed"]) is not None and num(f["expected"]) is not None
             and f["observed"] != f["expected"] and num(f["observed"]) > num(f["expected"]))
    s["ours_lower"], s["ours_higher"] = lo, hi
    return s


def search(pub, runs):
    """Every combination of binning rule, read-off rule and widths, scored against Tables 1, S3 and S4."""
    grid = []
    for rule, read in itertools.product(("nearest", "interval", "edge_last", "edge_first"), ("first", "stays")):
        per_table = {}
        for table in TABLE_SCENARIOS:
            best = None
            for pw, ew in itertools.product(WIDTHS["patients"], WIDTHS["events"]):
                ours = table_cells(runs, table, rule, read, pw, ew)
                fl = fields_of(table, pub[table], ours)
                score = {"patients_width": pw, "events_width": ew, "exact": count(fl)}
                per_table.setdefault("all", []).append(dict(score, table=table))
                if best is None or score["exact"] > best["exact"]:
                    best = score
            per_table[table] = best
        grid.append({"bin_rule": rule, "read_rule": read, "tables": {t: per_table[t] for t in TABLE_SCENARIOS},
                     "exact": sum(per_table[t]["exact"] for t in TABLE_SCENARIOS), "by_width": per_table["all"]})
    grid.sort(key=lambda g: -g["exact"])
    return grid


def range_text(vals):
    """'a–b' (or 'a' when equal), as Tables 3 and 4 print a range."""
    lo, hi = min(vals), max(vals)
    return str(lo) if lo == hi else f"{lo}–{hi}"


def ois_columns(pub_t, pcs_map):
    """OIS patients and events of Tables 3 and 4: the min-max over I^2 of Table 2 (ours and the paper's)."""
    fields, arith = [], []
    for k, row in pub_t.items():
        pc, th, acc = k.split("|")
        beta = {"good": 0.20, "very_good": 0.10, "excellent": 0.05}[acc]
        pcv = PC_MIDPOINTS[pc]
        o = [round_ois(**{kk: ois(pcv, int(th) / 100, i2, beta=beta)[kk] for kk in ("patients", "events")}, pc=pcv)
             for i2 in (0.0, 0.25, 0.50)]
        for what in ("patients", "events"):
            fields.append({"name": f"PC {pc}%, RRR {th}%, power {row['ois_power']}%, OIS {what}",
                           "expected": row[f"ois_{what}"], "observed": range_text([x[what] for x in o])})
    return fields


def main():
    pub_path, sim_path, out = sys.argv[1:4]
    pub = json.load(open(pub_path))
    sim = json.load(open(sim_path))
    runs, second = sim["runs"]["main"], sim["runs"]["replicate"]
    grid = search(pub, runs)
    best = grid[0]
    rule, read = best["bin_rule"], best["read_rule"]
    res = {"search": [{k: g[k] for k in ("bin_rule", "read_rule", "exact", "tables")} for g in grid],
           "search_by_width": grid[0]["by_width"],
           "chosen": {"bin_rule": rule, "read_rule": read,
                      "widths": {t: {"patients": best["tables"][t]["patients_width"], "events": best["tables"][t]["events_width"]}
                                 for t in TABLE_SCENARIOS}},
           "tables": {}, "hypotheses": {}}
    for table in TABLE_SCENARIOS:
        w = res["chosen"]["widths"][table]
        ours = table_cells(runs, table, rule, read, w["patients"], w["events"])
        sec = table_cells(second, table, rule, read, w["patients"], w["events"])
        fl = fields_of(table, pub[table], ours, sec, widths=w)
        res["tables"][table] = {"fields": fl, "summary": summary(fl, w), "widths": w, "ours": ours}
        if table == "table1":
            for v in ("correct_all", "binomial_total"):
                alt = table_cells(sim["runs"][v], table, rule, read, w["patients"], w["events"])
                fv = fields_of(table, pub[table], alt, widths=w)
                res["hypotheses"][v] = {"table1": summary(fv, w),
                                        "events_ratio_to_main": round(float(np.mean(
                                            [sim["runs"][v][k]["mean_total_events"] / runs[k]["mean_total_events"] for k in runs
                                             if k in sim["runs"][v]])), 3)}
    # Table 2
    t2, foot = [], []
    for k, row in pub["table2"].items():
        rrr, pc, i2 = k.split("|")
        for j, beta in enumerate((0.20, 0.10, 0.05)):
            o = ois(float(pc) / 100, int(rrr) / 100, int(i2) / 100, beta=beta)
            r = round_ois(o["patients"], o["events"], float(pc) / 100)
            fr = round_ois_footnote(o["patients"], o["events"], float(pc) / 100)
            for what, idx in (("patients", j), ("events", 3 + j)):
                t2.append({"name": f"RRR {rrr}%, PC {pc}%, I2 {i2}%, beta {int(beta * 100)}%, {what}",
                           "expected": row[idx], "observed": str(r[what]), "unrounded": round(o[what], 1),
                           "footnote_rule": str(fr[what])})
    res["tables"]["table2"] = {"fields": t2, "summary": {
        "fields": len(t2), "exact": count(t2), "footnote_rule_exact": sum(f["footnote_rule"] == f["expected"] for f in t2),
        "patients_exact": sum(f["observed"] == f["expected"] for f in t2 if f["name"].endswith("patients")),
        "events_exact": sum(f["observed"] == f["expected"] for f in t2 if f["name"].endswith("events")),
        "within_one_step": sum(abs(f["unrounded"] - float(f["expected"])) <= (50 if f["name"].endswith("events")
                                                                              else (500 if float(f["expected"]) > 10000 or f["unrounded"] > 10000 else 100))
                               for f in t2)}}
    # Tables 3 and 4: OIS columns
    for t in ("table3", "table4"):
        fl = ois_columns(pub[t], None)
        near = 0
        for f in fl:
            if f["observed"] == f["expected"]:
                continue
            e, o = f["expected"].split("–"), f["observed"].split("–")
            if len(e) == len(o) == 2:
                e0 = float(e[0]) * (1000 if float(e[0]) < 100 and float(e[1]) > 1000 else 1)  # '10–20000' is 10000–20000
                step = 50 if f["name"].endswith("events") else 1000
                near += abs(e0 - float(o[0])) <= step and abs(float(e[1]) - float(o[1])) <= step
        res["tables"][f"{t}_ois"] = {"fields": fl, "summary": {"fields": len(fl), "exact": count(fl),
                                                               "misses_within_one_rounding_step": near}}
    # Tables 3 and 4: simulation columns against range rules on the paper's own tables
    src = {"table3": {"1-5": ("table1", "1-5"), "5-15": ("table1", "5-15")},
           "table4": {"1-5": ("tableS4", "1-5"), "5-15": ("tableS4", "5-15"), "15-40": ("tableS3", "15-40"),
                      "40-80": ("tableS3", "40-80")}}
    lv = {"10": 0, "5": 1, "1": 2}
    rules_tried, recovered = 0, {}
    cells = 0
    for t in ("table3", "table4"):
        for k, row in pub[t].items():
            pc, th, acc = k.split("|")
            tab, pcs = src[t][pc]
            for what, off in (("sim_patients", 0), ("sim_events", 3)):
                cells += 1
                exp = row[what].replace(">", "").split("–")
                lo, hi = num(exp[0]), num(exp[-1])
                for ths in (("30",), ("20",), ("30", "20")):
                    for rrrs in (("0",), ("10",), ("0", "10")):
                        for lvs in [c for r in (1, 2) for c in itertools.combinations(LEVELS, r)]:
                            name = f"thresholds {'/'.join(ths)}, true RRR {'/'.join(rrrs)}, levels {'/'.join(lvs)}"
                            vals = [num(pub[tab][f"{r}|{tt}|{pcs}|{tau}"][off + lv[l]]) for r in rrrs for tt in ths
                                    for l in lvs for tau in TAUS]
                            if min(vals) == lo and max(vals) == hi:
                                recovered.setdefault(name, []).append(f"{t} {k} {what}")
    # The Methods' definitions: good = P(>20%) < 10% and P(>30%) < 5%; very good = P(>20%) < 5% and
    # P(>30%) < 1%; excellent = P(>20%) < 1%. The number for a scenario is the larger of the two read-offs;
    # a range is min-max over tau2 (true RRR 0%, 10% or both).
    need = {"good": (("20", "10"), ("30", "5")), "very_good": (("20", "5"), ("30", "1")), "excellent": (("20", "1"),)}
    definition = {"0": 0, "10": 0, "0/10": 0}
    for t in ("table3", "table4"):
        for k, row in pub[t].items():
            pc, th, acc = k.split("|")
            tab, pcs = src[t][pc]
            for what, off in (("sim_patients", 0), ("sim_events", 3)):
                exp = row[what].replace(">", "").split("–")
                lo, hi = num(exp[0]), num(exp[-1])
                for rr in definition:
                    vals = [max(num(pub[tab][f"{r}|{tt}|{pcs}|{tau}"][off + lv[l]]) for tt, l in need[acc])
                            for r in rr.split("/") for tau in TAUS]
                    definition[rr] += (min(vals) == lo and max(vals) == hi)
    rules_tried = 3 * 3 * 6
    best_rule = max(recovered.items(), key=lambda kv: len(kv[1])) if recovered else (None, [])
    res["tables"]["table34_sim"] = {"cells": cells, "rules_tried": rules_tried, "best_rule": best_rule[0],
                                    "best_rule_cells": len(best_rule[1]),
                                    "cells_any_rule": len({c for v in recovered.values() for c in v}),
                                    "methods_definition_cells": definition}
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
        f.write("\n")
    for t in ("table1", "tableS4", "tableS3", "table2", "table3_ois", "table4_ois"):
        print(t, res["tables"][t]["summary"], file=sys.stderr)
    print("chosen", res["chosen"], file=sys.stderr)
    print("table34_sim", res["tables"]["table34_sim"], file=sys.stderr)
    print("hypotheses", res["hypotheses"], file=sys.stderr)


if __name__ == "__main__":
    main()

"""Compare the simulation with every printed cell of Tables 2-4 and S1-S7, and Figs 1-4's bars.

Usage: compare.py PUBLISHED.json FIGURE_VALUES.json SIMULATION.json OUT.json

Tolerance, fixed before looking at the comparison: half a unit of the last printed digit plus
3 combined Monte Carlo standard errors, 3 x sqrt(2) x SE, where SE is the standard error of one
1,000-pair estimate (ours stands in for the paper's, which is not printed):

* relative bias: sd(estimates) / sqrt(n) / true ESR (x 100 for %); absolute bias: sd / sqrt(n)
* coverage: sqrt(p (1 - p) / n), p the mean of ours and the paper's, n the defined intervals
* expected length given coverage: sd of the covering lengths / sqrt(their number)
* empirical CI length: bootstrap standard error (200 resamples)
* figure bars also get one pixel of the published figure (0.00075).

The same comparison is run for a second run of our own with another seed (how often two runs of
one design miss the tolerance), for wrong inputs (controls), and for each hypothesis variant.
"""
import json
import math
import sys

import numpy as np

from simulate import RRS, SCENARIOS, SIZES

Z = 3.0
TABLES = {  # table: (estimator block, measure, scale, printed as)
    "S1": ("esr_s", "relative_bias", 100), "S2": ("esr_r", "relative_bias", 100),
    "S3": ("esr_s", "absolute_bias", 1), "S4": ("esr_r", "absolute_bias", 1),
    "S5": ("ci_s_log", "coverage", 100), "S6": ("ci_r_log", "coverage", 100), "S7": ("ci_r_binomial", "coverage", 100),
}
LABEL = {"S1": "relative bias of ESR_S (%)", "S2": "relative bias of ESR_R (%)", "S3": "absolute bias of ESR_S",
         "S4": "absolute bias of ESR_R", "S5": "coverage of the log CI of ESR_S (%)",
         "S6": "coverage of the log CI of ESR_R (%)", "S7": "coverage of the binomial CI of ESR_R (%)"}
FIG_SERIES = {"esr_s_log": ("ci_s_log", "expected_length_given_coverage", "length_se"),
              "esr_r_log": ("ci_r_log", "expected_length_given_coverage", "length_se"),
              "esr_r_binomial": ("ci_r_binomial", "expected_length_given_coverage", "length_se"),
              "empirical": ("esr_r", "empirical_length", "empirical_length_se")}


def printed_half(s):
    s = str(s).strip()
    return 0.5 * 10 ** -(len(s.split(".")[1]) if "." in s else 0)


def true_esr(cell):
    s, size, rr = cell.split("|")
    return float(rr) * SCENARIOS[int(s[1])][1]


def ours_and_se(table, block, expected=None):
    est, meas, scale = TABLES[table]
    b = block[est]
    v = b[meas]
    if v is None:
        return None, None
    if meas == "coverage":
        p = (v + float(expected) / 100) / 2 if expected is not None else v
        n = b["n_defined"] or 1
        se = math.sqrt(max(p * (1 - p), 0.0) / n)
    else:
        se = b["sd"] / math.sqrt(b["n"])
    return v * scale, se * scale


def table_fields(table, cells, sim, tl_true=None):
    """Fields for one printed table against one simulation (dict of setting -> summary)."""
    est, meas, scale = TABLES[table]
    fields = []
    for cell, printed in cells.items():
        s, size, rr = cell.split("|")[:3]
        k = f"{s}|{size}|{rr}"
        block = sim[k]
        ours, se = ours_and_se(table, block, printed if meas == "coverage" else None)
        if meas == "relative_bias":
            se = se / true_esr(k) if se is not None else None
        if ours is not None and meas == "relative_bias":
            pass  # summary already holds (mean - true) / true
        tol = printed_half(printed) + Z * math.sqrt(2) * (se or 0.0)
        fields.append({"name": f"Scenario {s[1]}, {size}, RR {rr}" + (f", ESR_{cell.split('|')[3]}" if cell.count('|') == 3 else ""),
                       "cell": cell, "expected": printed, "observed": None if ours is None else round(ours, 4),
                       "tolerance": {"abs": round(tol, 6)},
                       "z": None if ours is None or not se else round((ours - float(printed)) / (math.sqrt(2) * se), 3)})
    return fields


def summarize(fields):
    hits = [f for f in fields if f["observed"] is not None and abs(f["observed"] - float(f["expected"])) <= f["tolerance"]["abs"] + 1e-12]
    zs = np.array([f["z"] for f in fields if f["z"] is not None])
    return {"fields": len(fields), "within": len(hits),
            "rms_z": round(float(np.sqrt(np.mean(zs ** 2))), 3) if zs.size else None,
            "mean_z": round(float(np.mean(zs)), 3) if zs.size else None}


def split_key(table, cell):
    """Tables 2 and 3 cells carry the estimator; map them to the S table they restate."""
    if table in ("table2", "table3"):
        s, size, rr, e = cell.split("|")
        t = {"table2": {"S": "S1", "R": "S2"}, "table3": {"S": "S5", "R": "S6"}}[table][e]
        return t, f"{s}|{size}|{rr}"
    if table == "table4":
        return "S7", cell
    return table, cell


def compare_table(name, cells, sim):
    groups = {}
    for cell, printed in cells.items():
        t, k = split_key(name, cell)
        groups.setdefault(t, {})[cell] = printed
    fields = []
    for t, cs in groups.items():
        fields += table_fields(t, cs, sim)
    order = {c: i for i, c in enumerate(cells)}
    fields.sort(key=lambda f: order[f["cell"]])
    return fields


def rotate(sim, how):
    """Wrong inputs: our values from another setting, put in place of the right one."""
    out = {}
    for k in sim:
        s, size, rr = k.split("|")
        if how == "scenario":
            s2 = {"S1": "S2", "S2": "S1", "S3": "S4", "S4": "S3"}[s]
            k2 = f"{s2}|{size}|{rr}"
        elif how == "sizes":
            size2 = {"1000/1000": "5000/5000", "5000/5000": "1000/1000", "1000/5000": "5000/1000",
                     "5000/1000": "1000/5000", "250/250": "250/250"}[size]
            k2 = f"{s}|{size2}|{rr}"
        out[k] = sim.get(k2, sim[k])
    return out


def with_variant(sim, variants, name):
    out = {}
    for k, v in sim.items():
        b = dict(v)
        b.update(variants[k][name])
        out[k] = b
    return out


def figure_fields(fig, figvals, sim, px):
    fields = []
    bars = figvals[fig]["bars"]
    s = int(fig[-1])
    for key_, bar in bars.items():
        rr, ser = key_.split("|")
        block, meas, se_key = FIG_SERIES[ser]
        b = sim[f"S{s}|5000/5000|{rr}"][block]
        ours, se = b.get(meas), b.get(se_key)
        if bar["value"] is None:
            continue  # no bar printed (Fig. 4, ESR_S at RR 5.0: coverage 0, so no length)
        tol = px + Z * math.sqrt(2) * (se or 0.0)
        fields.append({"name": f"RR {rr}, {ser}", "bar": key_, "expected": f"{bar['value']:.4f}",
                       "observed": None if ours is None else round(ours, 5), "tolerance": {"abs": round(tol, 6)},
                       "z": None if ours is None or not se else round((ours - bar["value"]) / math.sqrt(2 * se ** 2 + px ** 2 / 3), 3)})
    return fields


def main():
    pub_p, fig_p, sim_p, out_p = sys.argv[1:5]
    pub = json.load(open(pub_p))
    figv = json.load(open(fig_p))
    S = json.load(open(sim_p))
    main_, rep, var, popx = S["main"], S["replicate"], S["variants"], S["exact_population"]
    res = {"tolerance": "half a printed unit + 3 x sqrt(2) x SE (figures: + 1 px)", "tables": {}, "figures": {},
           "controls": {}, "hypotheses": {}, "replicate": {}}
    names = ["table2", "table3", "table4"] + list(TABLES)
    for name in names:
        fields = compare_table(name, pub[name], main_)
        res["tables"][name] = {"summary": summarize(fields), "fields": fields}
        res["replicate"][name] = summarize(compare_table(name, pub[name], rep))
        res["controls"][name] = {
            "scenario_swapped": summarize(compare_table(name, pub[name], rotate(main_, "scenario"))),
            "sizes_swapped": summarize(compare_table(name, pub[name], rotate(main_, "sizes"))),
        }
    # Two runs of our own design against each other: the false-miss rate of the tolerance.
    own = []
    for t in TABLES:
        for k in pub[t]:
            a, se = ours_and_se(t, main_[k])
            b, _ = ours_and_se(t, rep[k])
            if a is None or b is None or se is None:
                continue
            if TABLES[t][1] == "relative_bias":
                se = se / true_esr(k)
            own.append(abs(a - b) <= Z * math.sqrt(2) * se + 1e-12)
    res["replicate"]["own_runs_within"] = {"cells": len(own), "within": int(sum(own))}
    # Hypotheses: the same samples analysed another way; the tables each one bears on.
    hyp = {
        "zero_missing": ["S5", "S6"], "zero_not_covered": ["S5", "S6"], "zero_half": ["S1", "S2", "S5", "S6", "S7"],
        "true_esr_label": ["S1", "S2", "S5", "S6", "S7"], "true_esr_realized": ["S1", "S2", "S5", "S6", "S7"],
        "eq10_no_first_term": ["S6"], "eq10_var_not_log": ["S6"], "eq10_n2_for_n1": ["S6"], "eq10_p1d_for_p1u": ["S6"],
    }
    for h, tabs in hyp.items():
        sim = with_variant(main_, var, h)
        res["hypotheses"][h] = {t: summarize(compare_table(t, pub[t], sim)) for t in tabs}
    res["hypotheses"]["eq10_as_printed"] = {"S6": res["tables"]["S6"]["summary"]}
    res["hypotheses"]["exact_population"] = {t: summarize(compare_table(t, pub[t], popx)) for t in ("S1", "S2", "S5", "S7")}
    # Figures: bars read off the published JPEGs against the 5000/5000 runs.
    for fig in ("fig1", "fig2", "fig3", "fig4"):
        px = figv[fig]["value_per_px"]
        fields = figure_fields(fig, figv, main_, px)
        alt = with_variant(main_, var, "eq10_no_first_term")
        res["figures"][fig] = {"summary": summarize(fields), "fields": fields,
                               "eq10_no_first_term": summarize(figure_fields(fig, figv, alt, px)),
                               "replicate": summarize(figure_fields(fig, figv, rep, px))}
    json.dump(res, open(out_p, "w"), indent=1)
    for name in names:
        s = res["tables"][name]["summary"]
        c = res["controls"][name]
        print(f"{name}: {s['within']}/{s['fields']} within (rms z {s['rms_z']}); second run {res['replicate'][name]['within']}; "
              f"controls {c['scenario_swapped']['within']}, {c['sizes_swapped']['within']}", file=sys.stderr)
    for fig in res["figures"]:
        f = res["figures"][fig]
        print(f"{fig}: {f['summary']['within']}/{f['summary']['fields']} bars (rms z {f['summary']['rms_z']}); "
              f"without eq. 10's first term {f['eq10_no_first_term']['within']}", file=sys.stderr)
    print("own runs:", res["replicate"]["own_runs_within"], file=sys.stderr)
    for h, v in res["hypotheses"].items():
        print(h, {t: (x["within"], x["rms_z"]) for t, x in v.items()}, file=sys.stderr)


if __name__ == "__main__":
    main()

"""The paper's statements about its results, checked on its own tables and on our run.

Usage: claims.py PUBLISHED_VALUES.json TABLES.json FIGURES_SIMULATION.json OUT.json

Each claim is a set of fields with the paper's statement as the expected value ("yes"). For each field:
  arithmetic  the same computation on the paper's own Tables 1, S3, S4 and 2 (does the paper's text follow
              from the paper's tables?)
  observed    the computation on our run (our Tables 1, S3, S4, our OIS, our curves)
A statement holds ("yes") when it holds in most of the cases it covers (the paper says "generally").
"""
import json
import sys

import numpy as np

from oisim.core import PC_MIDPOINTS, ois

TAUS = ("0.05", "0.15", "0.25")
I2_OF_TAU = {"0.05": 0.0, "0.15": 0.25, "0.25": 0.50}  # the paper's example: tau2 0.15 with I2 25%


def num(s):
    s = str(s)
    if s.startswith(">"):
        return float("inf")
    return float(s.lstrip("<"))


def rows(tabs):
    """(table, rrr, th, pc, tau, values) for every row of Tables 1, S4, S3."""
    for t, d in tabs.items():
        for k, v in d.items():
            rrr, th, pc, tau = k.split("|")
            yield t, rrr, th, pc, tau, [num(x) for x in v]


def share(pairs):
    pairs = list(pairs)
    return sum(pairs) / len(pairs) if pairs else float("nan"), len(pairs)


def yes(sh):
    return "yes" if sh[0] > 0.5 else "no"


def claims_of(tabs, curves=None):
    """Every claim's shares, on one set of tables (the paper's or ours)."""
    out = {}
    by = {(t, rrr, th, pc, tau): v for t, rrr, th, pc, tau, v in rows(tabs)}
    # 1. The larger the overestimation, the fewer patients and events needed (>30% needs no more than >20%).
    out["larger_overestimation"] = share(by[(t, r, "30", pc, tau)][j] <= by[(t, r, "20", pc, tau)][j]
                                         for (t, r, th, pc, tau) in by if th == "30" for j in range(6))
    # 2. Low control risk (1-5%) needs more patients but fewer events than 5-15% (Tables 1 and S4).
    pat, ev = [], []
    for (t, r, th, pc, tau), v in by.items():
        if pc == "1-5":
            w = by[(t, r, th, "5-15", tau)]
            pat += [v[j] > w[j] for j in range(3)]
            ev += [v[j] < w[j] for j in range(3, 6)]
    out["low_pc_more_patients"] = share(pat)
    out["low_pc_fewer_events"] = share(ev)
    # 3. tau2 0.05 needs fewer than tau2 0.25, except 'common' sizes with PC 1-5% (Table S4), where it needs more.
    gen, rev = [], []
    for (t, r, th, pc, tau), v in by.items():
        if tau != "0.05":
            continue
        w = by[(t, r, th, pc, "0.25")]
        cmp = [v[j] < w[j] for j in range(6) if v[j] != w[j]]
        if t == "tableS4" and pc == "1-5":
            rev += [not c for c in cmp]
        else:
            gen += cmp
    out["low_tau_fewer"] = share(gen)
    out["common_low_pc_reversed"] = share(rev)
    # 4. Surpassing the OIS protects: P(RRR > T) drops below 5% before the OIS for RRR T at 90% power
    #    (OIS control risk the range's midpoint, I2 matched to tau2 as in the paper's example).
    prot = []
    for (t, r, th, pc, tau), v in by.items():
        o = ois(PC_MIDPOINTS[pc], int(th) / 100, I2_OF_TAU[tau], beta=0.10)
        prot.append(v[1] <= o["patients"])
    out["ois_protects"] = share(prot)
    if curves is not None:
        # 5. In most scenarios the probability of overestimation was above 25% when patients were few.
        out["early_above_25"] = share(c > 0.25 for c in curves)
    return out


def main():
    pub_path, tables_path, sim_path, out = sys.argv[1:5]
    pub = json.load(open(pub_path))
    tab = json.load(open(tables_path))
    sim = json.load(open(sim_path))
    paper = {t: pub[t] for t in ("table1", "tableS4", "tableS3")}
    ours = {t: tab["tables"][t]["ours"] for t in ("table1", "tableS4", "tableS3")}
    # First point of each scenario's RRR > 20% patients curve (the rule and spacing the figures use).
    first = []
    for k, run in sim["runs"]["main"].items():
        w = "200" if ("pc15-40" in k or "pc40-80" in k) else "500"
        c = run["curves"]["nearest"]["patients"][w]
        first.append(c["over20"][0] / c["n"][0])
    a = claims_of(paper)
    o = claims_of(ours, first)
    spec = {
        "text.larger_overestimation": ("The larger the overestimation, the smaller the number of patients and events required",
                                       [("larger_overestimation", ">30% needs no more than >20% (all three tables)")]),
        "text.control_risk": ("A larger number of patients, but a smaller number of events, were required when the control group risk was low",
                              [("low_pc_more_patients", "PC 1-5% needs more patients than 5-15% (Tables 1, S4)"),
                               ("low_pc_fewer_events", "PC 1-5% needs fewer events than 5-15% (Tables 1, S4)")]),
        "text.heterogeneity": ("Generally smaller numbers with tau2 = 0.05 than 0.25; reversed with 'common' sizes and PC 1-5%",
                               [("low_tau_fewer", "tau2 0.05 needs fewer than 0.25 (except common sizes, PC 1-5%)"),
                                ("common_low_pc_reversed", "common sizes, PC 1-5%: tau2 0.05 needs more than 0.25")]),
        "text.ois_protects": ("Surpassing the optimal information size generally provided sufficient protection against overestimation",
                              [("ois_protects", "P(RRR > T) below 5% at or before the OIS for RRR = T, 90% power")]),
        "text.early_above_25": ("In most scenarios, the probability of overestimation was higher than 25% when the number of patients was small",
                                [("early_above_25", "first point of the RRR > 20% patient curve above 25% (36 scenarios)")]),
    }
    res = {"claims": []}
    for cid, (statement, fl) in spec.items():
        fields = []
        for key, name in fl:
            f = {"name": name, "expected": "yes", "observed": yes(o[key]),
                 "observed_share": round(o[key][0], 4), "cases": o[key][1]}
            if key in a:
                f["arithmetic"] = yes(a[key])
                f["arithmetic_share"] = round(a[key][0], 4)
            fields.append(f)
        res["claims"].append({"id": cid, "statement": statement, "fields": fields})
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
        f.write("\n")
    for c in res["claims"]:
        print(c["id"], [(f["observed"], f["observed_share"], f.get("arithmetic"), f.get("arithmetic_share")) for f in c["fields"]],
              file=sys.stderr)


if __name__ == "__main__":
    main()

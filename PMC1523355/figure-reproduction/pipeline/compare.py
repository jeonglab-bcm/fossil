"""Compare our run with every printed value of Tables 1-5 and Fig. 1B.

Usage: compare.py PUBLISHED_VALUES SIMULATION_JSON OUT.json

Tolerances, fixed before the comparison:
  * a power: half a printed unit plus 3 combined Monte Carlo standard errors, the paper's (2,000 trials,
    at its printed value) and ours (20,000 trials): .005 + 3 sqrt(p(1-p)/2000 + q(1-q)/20000);
  * everything else (shares, CERs, RRRs, NNTs, AUROCs): the printed precision, half a unit of the last digit.
The hypothesis variants are compared with the same rules and counted, never merged into our values.
"""
import json
import math
import sys

P_ITER = 2000


def tol_power(p_pub, q_ours, n_ours, scale=1.0):
    """Half a printed unit plus 3 combined Monte Carlo SEs; scale 100 for powers printed in percent."""
    p = float(p_pub) / scale
    return 0.5 * 10 ** -decimals(p_pub) + 3 * scale * math.sqrt(p * (1 - p) / P_ITER + q_ours * (1 - q_ours) / n_ours)


def decimals(s):
    s = str(s)
    return len(s.split(".")[1]) if "." in s else 0


def within(f):
    tol = f.get("tolerance")
    exp = float(f["expected"])
    allowed = tol["abs"] if tol else 0.5 * 10 ** -decimals(f["expected"]) + 1e-12
    return abs(f["observed"] - exp) <= allowed + 1e-12


def power_field(name, pub, entry, n_iter, pct=False):
    if entry is None:
        return {"name": name, "expected": pub, "observed": None}
    q = entry["power"]
    scale = 100.0 if pct else 1.0
    t = tol_power(pub, q, n_iter, scale)
    obs = q * scale
    return {"name": name, "expected": pub, "observed": round(obs, 6), "tolerance": {"abs": round(t, 6)},
            "z": round((obs - float(pub)) / (scale * math.sqrt(float(pub) / scale * (1 - float(pub) / scale) / P_ITER + q * (1 - q) / n_iter) or 1), 3)}


def value_field(name, pub, obs, ndigits=6):
    return {"name": name, "expected": pub, "observed": None if obs is None else round(obs, ndigits)}


LABELS = {"rf_absent": "risk factor absent (75%)", "rf_present": "risk factor present (25%)",
          "idx_0_1": "0-1 RFs", "idx_ge2": "2 or more RFs", "k0": "0 RFs", "k1": "1 RF", "k2": "2 RFs",
          "k3": "3 RFs", "k_ge4": "4 or more RFs"}


def table1_true(pv, det):
    fields = []
    for g, row in pv["table1"]["groups"].items():
        d = det[g]
        fields.append(value_field(f"{LABELS[g]}, % of population", row["share"], 100 * d["share"]))
        fields.append(value_field(f"{LABELS[g]}, CER (%)", row["cer"], 100 * d["cer"]))
        fields.append(value_field(f"{LABELS[g]}, net RRR", row["rrr"], d["rrr"]))
        fields.append(value_field(f"{LABELS[g]}, NNT", row["nnt"], d["nnt"] if d["nnt"] is not None else 1e12))
    return fields


def items_of(pv, run, n_iter, det=None):
    """Every compared field of one run, by item."""
    t1 = run["table1"]
    out = {}
    if det is not None:
        out["table1_true"] = table1_true(pv, det)
    out["table1_power"] = [
        power_field("conventional (one RF)", pv["table1"]["power"]["conventional"], t1["conventional"], n_iter),
        power_field("risk index, dichotomized (0-1 vs 2 or more RFs)", pv["table1"]["power"]["dichotomized"], t1["dichotomized"], n_iter),
        power_field("risk index, continuous (RF count)", pv["table1"]["power"]["continuous"], t1["continuous"], n_iter),
        value_field("AUROC of the risk index", pv["table1"]["auroc_continuous"], t1["continuous"]["auroc"]),
    ]
    out["table2"] = [power_field(f"OR {eff}, prevalence {prev}", v, (run[f"table2/{eff}/{prev}"] or {}).get("conventional"), n_iter)
                     for eff, row in pv["table2"].items() for prev, v in row.items()]
    t3 = []
    for eff, row in pv["table3"].items():
        for nk, v in row.items():
            e = run[f"table3/{eff}/{nk}"]
            t3.append(power_field(f"OR {eff}, {nk} RF{'s' if nk != '1' else ''}, power", v["power"], e and e["index"], n_iter))
            t3.append(value_field(f"OR {eff}, {nk} RF{'s' if nk != '1' else ''}, AUROC", v["auroc"], e and e["index"]["auroc"]))
    out["table3"] = t3
    t4 = []
    for w, v in pv["table4"].items():
        e = run["table4"][w]
        name = w.replace("_", " ")
        t4.append(value_field(f"{name} weighting, AUROC", v["auroc"], e["auroc"]))
        t4.append(power_field(f"{name} weighting, power", v["power"], e, n_iter))
    out["table4"] = t4
    out["table5"] = [power_field(f"{h} per 1,000 patient-years, {a.replace('_', '-')} (%)", v[a], run[f"table5/{h}"][a], n_iter, pct=True)
                     for h, v in pv["table5"].items() for a in ("conventional", "risk_stratified")]
    f1 = []
    for row, v in pv["fig1b"].items():
        e = run[f"fig1b/{row}"]
        for col, label in (("one_rf", "one RF"), ("four_rf", "4-RF score")):
            f1.append(power_field(f"average CER {row}, {label}, power", v[col][0], e[col], n_iter))
            f1.append(value_field(f"average CER {row}, {label}, AUROC", v[col][1], e[col]["auroc"]))
    out["fig1b"] = f1
    return out


def summary(fields):
    got = [f for f in fields if f["observed"] is not None]
    w = sum(within(f) for f in got)
    zs = [f["z"] for f in got if "z" in f]
    return {"fields": len(fields), "compared": len(got), "within": w,
            "rms_z_power": round(math.sqrt(sum(z * z for z in zs) / len(zs)), 3) if zs else None,
            "mean_z_power": round(sum(zs) / len(zs), 3) if zs else None}


def auroc_control(pv, run):
    """AUROC hypothesis: the index's AUROC in the control arm only (pre-treatment risk)."""
    alt = json.loads(json.dumps(run))
    for k, e in alt.items():
        if isinstance(e, dict):
            for n, v in e.items():
                if isinstance(v, dict) and "auroc_control" in v:
                    v["auroc"] = v["auroc_control"]
    return alt


def main(pv_path, sim_path, out):
    pv = json.load(open(pv_path, encoding="utf-8"))
    sim = json.load(open(sim_path))
    it, itv = sim["settings"]["iterations"], sim["settings"]["iterations_variants"]
    det = sim["deterministic"]
    ours = items_of(pv, sim["primary"], it, det["table1_or"])
    second = items_of(pv, sim["second_run"], it, det["table1_or"])
    res = {"tolerance_rule": "power: .005 + 3 sqrt(p(1-p)/2000 + q(1-q)/n_ours); other values: printed precision",
           "items": {k: {"fields": v, "summary": summary(v)} for k, v in ours.items()},
           "second_run": {k: summary(v) for k, v in second.items()}}
    # our two runs against each other, at the same rule (q from one run, 'expected' the other at 3 decimals)
    agree = cells = 0
    for k in ("table1_power", "table2", "table3", "table4", "table5", "fig1b"):
        for a, b in zip(ours[k], second[k]):
            if "tolerance" in a and a["observed"] is not None:
                cells += 1
                agree += abs(a["observed"] - b["observed"]) <= a["tolerance"]["abs"]
    res["own_runs"] = {"cells": cells, "within": agree}
    hyp = {}
    for name, run in sim["hypotheses"].items():
        full = {**sim["primary"], **run}
        n = itv if name != "paper_iterations" else 2000
        h = items_of(pv, full, n, det["table1_rr"] if name == "rr_scale" else det["table1_or"])
        keys = {"table2_others_same_or": ["table2"], "table3_only_index_rfs": ["table3"]}.get(name, list(h))
        hyp[name] = {k: summary(h[k]) for k in keys}
    hyp["auroc_control_arm"] = {k: summary(v) for k, v in items_of(pv, auroc_control(pv, sim["primary"]), it).items()}
    res["hypotheses"] = hyp
    fp = sim["finite_population"]
    res["finite_population"] = {size: {k: {n: {"mean": round(v["mean"], 4), "sd": round(v["sd"], 4)} for n, v in d.items()}
                                       for k, d in blk.items()} for size, blk in fp.items()}
    json.dump(res, open(out, "w"), indent=1)
    for k, v in res["items"].items():
        print(f"{k:14s} {v['summary']['within']:3d} of {v['summary']['compared']:3d}  rms z {v['summary']['rms_z_power']}", file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:4])

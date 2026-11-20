"""Merge results_notes.json (written by hand: labels, assumptions, causes) with the numbers of a run into
results.json, then let check_results.py compute every verdict and the summary.

Usage: build_results.py RUN_DIR OUT.json [--environment ENV.json]

Notes items take their numbers from the run folder:
  "fields_from": "comparison.json:items/table2"   values.fields from that file and key path
  "pixels_from": "figures.json:figures/fig1a"     the pixel scores and controls, with the item's threshold
  "check_from": "package.json" | "claims.json"    the package check, or the claims recomputed from the paper
  "assumptions_from": [...], "cause_from": "..."  shared assumption sets and causes of the notes
A cause is attached only when the item has fields outside their tolerance. Every {fact} in the prose is a
number from the run (facts_of), so the prose cannot drift from it. The skill and session blocks travel
with the notes unchanged.
"""
import copy
import json
import math
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTES = HERE.parent / "results_notes.json"
sys.path.insert(0, str(HERE))
from check_results import field_matches  # noqa: E402

POWER_ITEMS = ("table1_power", "table2", "table3", "table4", "table5", "fig1b")


def get(run, ref):
    f, _, key = ref.partition(":")
    d = json.load(open(Path(run) / f))
    for k in key.split("/") if key else []:
        d = d[k]
    return d


def facts_of(run):
    run = Path(run)
    c = json.load(open(run / "comparison.json"))
    s = json.load(open(run / "simulation.json"))
    fig = json.load(open(run / "figures.json"))
    cl = json.load(open(run / "claims.json"))
    tot = lambda block, key: sum(block[k][key] for k in POWER_ITEMS if k in block)
    prim = {k: c["items"][k]["summary"] for k in c["items"]}
    gaps = [abs(f["observed"] - float(f["expected"])) * (0.01 if k == "table5" else 1)
            for k in POWER_ITEMS for f in c["items"][k]["fields"] if "tolerance" in f and f["observed"] is not None]
    fp = c["finite_population"]
    sd = lambda size: [v["sd"] for blk in fp[size].values() for v in blk.values()]
    ar = cl["_table1_arithmetic"]
    t1_ok = 0
    for r in ar:
        t1_ok += field_matches({"expected": r["rrr_printed"], "observed": r["rrr_from_cer"]}, {"printed": True})
        n = r["nnt_from_cer"]
        t1_ok += n is not None and field_matches({"expected": r["nnt_printed"], "observed": n}, {"printed": True})
    h = c["hypotheses"]
    f1a = fig["figures"]["fig1a"]
    return {
        "or_within": tot(prim, "within"), "or_compared": tot(prim, "compared"),
        "rr_within": tot(h["rr_scale"], "within"), "rr_compared": tot(h["rr_scale"], "compared"),
        "harm_within": tot(h["harm_independent"], "within"), "lr_within": tot(h["lr_test"], "within"),
        "paper_it_within": tot(h["paper_iterations"], "within"), "auroc_ctrl_within": tot(h["auroc_control_arm"], "within"),
        "t2_same_within": h["table2_others_same_or"]["table2"]["within"],
        "t3_only_within": h["table3_only_index_rfs"]["table3"]["within"],
        "own_within": c["own_runs"]["within"], "own_cells": c["own_runs"]["cells"],
        "max_gap": f"{100 * max(gaps):.0f}",
        "fp100k_sd": f"{min(sd('100000')):.2f} to {max(sd('100000')):.2f}",
        "fp8800_sd": f"{min(sd('8800')):.2f} to {max(sd('8800')):.2f}",
        "or_true_within": prim["table1_true"]["within"], "rr_true_within": h["rr_scale"]["table1_true"]["within"],
        "t1_arith_ok": int(t1_ok),
        "t1_mean_cer": f"{100 * s['design_power']['table1_population']['cer']:.2f}",
        "design_power": f"{s['design_power']['table1_population']['power']:.2f}",
        "cer_80": f"{100 * s['design_power']['cer_for_80pct']:.1f}",
        "f1b_cer0": ", ".join(f"{100 * s['primary'][f'fig1b/{r}']['cer0']:.3f}%" for r in ("1.5%", "3%", "6%", "9%")),
        "curve_lo": f"{f1a['curve_cer_range'][0]:g}", "curve_hi": f"{f1a['curve_cer_range'][1]:g}",
    }


def fill(obj, facts):
    if isinstance(obj, str):
        def rep(m):
            if m.group(1) not in facts:
                raise KeyError(f"results_notes.json cites an unknown fact {{{m.group(1)}}}")
            return str(facts[m.group(1)])
        return re.sub(r"\{([a-z0-9_]+)\}", rep, obj)
    if isinstance(obj, list):
        return [fill(x, facts) for x in obj]
    if isinstance(obj, dict):
        return {k: fill(v, facts) for k, v in obj.items()}
    return obj


def arithmetic(claims):
    """text.arithmetic: each claim recomputed from the paper's own tables, and Table 1's own columns."""
    back, missed = [], []
    for cid, c in claims.items():
        if cid.startswith("_"):
            continue
        for f in c["fields"]:
            a = f.get("arithmetic")
            if a is None:
                continue
            g = {"expected": f["expected"], "observed": a}
            (back if field_matches(g, {"printed": True}) else missed).append(f"{cid}: {f['name']} ({f['expected']} against {a})")
    t1 = []
    for r in claims["_table1_arithmetic"]:
        n = r["nnt_from_cer"]
        ok_r = field_matches({"expected": r["rrr_printed"], "observed": r["rrr_from_cer"]}, {"printed": True})
        ok_n = n is not None and field_matches({"expected": r["nnt_printed"], "observed": n}, {"printed": True})
        if not (ok_r and ok_n):
            t1.append(f"{r['group']} RRR {r['rrr_printed']} against {r['rrr_from_cer']:.3f}, NNT {r['nnt_printed']} against "
                      + (f"{n:.0f}" if n is not None else "infinite"))
    detail = (f"{len(back)} of {len(back) + len(missed)} statements follow from the paper's own tables and Fig. 1A's formula"
              + (". Not: " + "; ".join(missed) if missed else "")
              + f". Table 1's RRR and NNT recomputed from its own CER column with Fig. 1A's formula: "
              f"{len(claims['_table1_arithmetic']) - len(t1)} of {len(claims['_table1_arithmetic'])} rows come back; not: " + "; ".join(t1))
    return not missed, detail


def main():
    args = sys.argv[1:]
    env = None
    if "--environment" in args:
        i = args.index("--environment")
        env = json.load(open(args[i + 1]))
        del args[i:i + 2]
    run, out = args
    notes = json.load(open(NOTES))
    facts = facts_of(run)
    notes = {k: (fill(v, facts) if k in ("items", "causes", "assumption_sets") else v) for k, v in notes.items()}
    run_block = copy.deepcopy(notes["run"])
    if env:
        run_block["environment"] = env
    res = {"schema": "paper2repro/results/v1", "paper": notes["paper"], "run": run_block,
           "session": notes["session"], "skill": notes["skill"], "items": []}
    for it in notes["items"]:
        it = copy.deepcopy(it)
        sets = it.pop("assumptions_from", [])
        if sets:
            it["assumptions"] = [a for s in sets for a in notes["assumption_sets"][s]] + it.get("assumptions", [])
        cause = it.pop("cause_from", None)
        src = it.pop("fields_from", None)
        if src:
            fields = [{k: f[k] for k in ("name", "expected", "observed", "tolerance", "z", "arithmetic") if k in f}
                      for f in get(run, src)["fields"] if f.get("observed") is not None]
            it["values"] = {"fields": fields, "tolerance": {"printed": True}}
            misses = [f for f in fields if not field_matches(f, {"printed": True})]
            if misses and cause and "cause" not in it:
                it["cause"] = copy.deepcopy(notes["causes"][cause])
        pix = it.pop("pixels_from", None)
        if pix:
            d = get(run, pix)
            it["pixels"] = {"tolerance_px": d["tolerance_px"], "dpi": 282, "published_near_ours": d["published_near_ours"],
                            "ours_near_published": d["ours_near_published"], "threshold": it.pop("threshold"),
                            "controls": d["controls"]}
        chk = it.pop("check_from", None)
        if chk == "package.json":
            p = Path(run) / chk
            d = json.load(open(p)) if p.exists() else {"passed": False, "detail": "package check not run"}
            it["check"] = {"passed": bool(d["passed"]), "detail": d.get("detail", "")}
        elif chk == "claims.json":
            passed, detail = arithmetic(json.load(open(Path(run) / chk)))
            it["check"] = {"passed": passed, "detail": detail}
        res["items"].append(it)
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
        f.write("\n")
    r = subprocess.run([sys.executable, str(HERE / "check_results.py"), out, "--write", "--skip-files"])
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()

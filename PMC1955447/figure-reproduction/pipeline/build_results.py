"""Merge results_notes.json (written by hand: labels, assumptions, causes) with the numbers of a run into
results.json, then let check_results.py compute every verdict and the summary.

Usage: build_results.py RUN_OUTPUT_DIR OUT.json [--environment ENV.json]

Notes items take their numbers from the run folder:
  "fields_from": "comparison.json:tables/table1_stable"   values.fields from that file and key path
  "check_from": "package.json" | "crosscheck.json" | "claims.json"   check.passed and detail
  "assumptions_from": [...]                    shared assumption sets of the notes
  "expect_misses": [...] or "any"              the fields the item's cause explains; the build fails when the
                                               run's misses differ, so a stale cause cannot reach the page
Every {name} in the notes' prose is filled from the run (facts_of), so no number in the prose is typed.
The skill block and the session pointer travel with the notes, unchanged.
"""
import copy
import os
import json
import math
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTES = Path(os.environ.get("RESULTS_NOTES", HERE.parent / "results_notes.json"))  # override: tests only
FIELD_KEYS = ("name", "expected", "observed", "tolerance", "arithmetic", "arithmetic_tolerance", "second_run")


def get(run, ref):
    f, _, key = ref.partition(":")
    d = json.load(open(Path(run) / f))
    for k in key.split("/") if key else []:
        d = d[k]
    return d


def matches(f, tol=None):
    sys.path.insert(0, str(HERE))
    from check_results import field_matches
    return field_matches(f, tol)


def f1(x):
    return f"{x:.1f}"


def f2(x):
    return f"{x:.2f}"


def misses_of(fields):
    return [f for f in fields if not matches(f, {"printed": True})]


def facts_of(run):
    """Numbers the hand-written notes cite, taken from the run so the prose cannot drift from it."""
    run = Path(run)
    c = json.load(open(run / "comparison.json"))
    sim = json.load(open(run / "simulation.json"))
    cl = json.load(open(run / "claims.json"))
    rt = json.load(open(run / "record_tests.json"))
    T, H, C = c["tables"], c["hypotheses"], c["controls"]
    R = sim["runs"]["main"]
    f = {}
    for k, v in T.items():
        f[f"{k}_within"], f[f"{k}_fields"] = v["summary"]["within"], v["summary"]["fields"]
        f[f"{k}_rms"] = f2(v["summary"]["rms_z"]) if v["summary"]["rms_z"] is not None else "n/a"
        if "second_within" in v["summary"]:
            f[f"{k}_second"] = v["summary"]["second_within"]
    for k, v in c["replicate"].items():
        f[f"{k}_replicate"] = v["within"]
    sim_tables = [k for k in T if k != "table2_pvalues"]
    f["cells_within"] = sum(T[k]["summary"]["within"] for k in sim_tables)
    f["cells_total"] = sum(T[k]["summary"]["fields"] for k in sim_tables)
    f["main_cells_within"] = sum(T[k]["summary"]["within"] for k in ("table1_converged", "table1_stable", "table1_lowconv", "table2_rates", "table3_stable", "table3_lowconv"))
    f["main_cells_total"] = sum(T[k]["summary"]["fields"] for k in ("table1_converged", "table1_stable", "table1_lowconv", "table2_rates", "table3_stable", "table3_lowconv"))
    for k in ("table1_stable", "table3_stable", "table1_lowconv", "table3_lowconv", "table1_converged"):
        f[f"{k}_pct"] = f"{100 * T[k]['summary']['within'] / T[k]['summary']['fields']:.0f}"
    # controls: the best wrong cell
    for k in ("table1_stable", "table3_stable", "table1_converged", "table1_lowconv"):
        f[f"{k}_ctrl_max"] = max(v[k]["within"] for kk, v in C.items() if k in v)
    f["table4_ctrl"] = C["table4: another prevalence"]["table4"]["within"]
    for k in ("table5_converged", "table5_bias", "table5_noncoverage"):
        f[f"{k}_ctrl"] = C["table5: the next model"][k]["within"]
    # hypotheses
    for h, v in H.items():
        for k, s in v.items():
            if isinstance(s, dict) and "within" in s:
                f[f"h_{h}_{k}"] = s["within"]
        if "mean_abs_converged_gap" in v:
            f[f"h_{h}_gap"] = f1(v["mean_abs_converged_gap"])
    # convergence
    f["conv_low"], f["conv_high"] = f"{R['converged_range'][0]:.1f}", f"{R['converged_range'][1]:.1f}"
    cells = R["cells"]
    f["conv_30x5"] = ", ".join(f"{cells[f'J30_n5_icc{i}']['converged_pct']:.0f}" for i in ("0.04", "0.17", "0.38"))
    f["sigma0_30x5_004"] = f1(cells["J30_n5_icc0.04"]["sigma0"]["bias_pct"])
    f["status_absxconv"] = f"{R['status_counts'].get('absxconv', 0):,}"
    f["status_failed"] = f"{sum(v for k, v in R['status_counts'].items() if k in ('linesearch', 'maxfunc', 'maxiter')):,}"
    f["qpoints"] = ", ".join(f"{q} ({n:,})" for q, n in R["qpoints_counts"].items())
    f["prev_main"] = f1(100 * claim_obs(cl, "methods_prevalence", 0))
    f["prev_icc04_conv"] = f1(100 * R["converged_vs_not_icc0.04"]["prevalence"]["converged"])
    f["prev_icc04_not"] = f1(100 * R["converged_vs_not_icc0.04"]["prevalence"]["not_converged"])
    f["prev_conv"] = f1(100 * R["converged_vs_not"]["prevalence"]["converged"])
    f["prev_not"] = f1(100 * R["converged_vs_not"]["prevalence"]["not_converged"])
    nc = rt["nonconverged"]
    f["nc_datasets"] = nc["datasets"]
    f["nc_both"] = f1(nc["lrt"]["both_significant_pct"])
    f["nc_int"] = f"{nc['intercept_significant_pct']:.0f}"
    f["nc_slope"] = f"{nc['slope_significant_pct']:.0f}"
    # pooled text numbers
    pb = R["pooled_bias"]
    f.update({f"overall_{p}": f1(pb[p]) for p in pb})
    # Table 4 hypotheses
    P = sim["prevalence"]["pooled"]
    for k in ("all_cells", "size5", "groups30"):
        f[f"t4_conv_{k}"] = ", ".join(f"{P[k][x]['converged_pct']:.0f}" for x in ("0.10", "0.34", "0.45"))
    f["t4_prev"] = ", ".join(f"{P['all_cells'][x]['prevalence_observed']:.3f}" for x in ("0.10", "0.34", "0.45"))
    # interval hypotheses (Table 3)
    for v in ("variance", "sd_scale", "log_scale", "boundary_as_miss"):
        h = H[f"table3_interval_{v}"]
        f[f"ci_{v}_stable"] = h["table3_stable_sigma"]["within"]
        f[f"ci_{v}_low"] = h["table3_lowconv_sigma"]["within"]
        f[f"ci_{v}_cell"] = f"{h['cell_30x5_icc0.04_sigma0']:.3f}"
    f["ci_stable_n"] = H["table3_interval_variance"]["table3_stable_sigma"]["fields"]
    f["ci_low_n"] = H["table3_interval_variance"]["table3_lowconv_sigma"]["fields"]
    f["t2_trend"] = H["table2_pvalues_trend_1df"]["table2_pvalues"]["within"]
    sd = H["table5_sd_scale"]["by_model"]
    for m in ("6", "7"):
        f[f"t5_m{m}_sd"], f[f"t5_m{m}_var"] = sd[m]["sd_scale"]["within"], sd[m]["variance_scale"]["within"]
    t5miss = [x["name"] for x in T["table5_bias"]["fields"] + T["table5_noncoverage"]["fields"] if not x["within"]]
    f["t5_miss_m67"] = sum(1 for x in t5miss if x.startswith(("Model 6,", "Model 7,")))
    f["t5_miss_total"] = len(t5miss)
    f["t5_miss_m15"] = sum(1 for x in t5miss if x.startswith(("Model 1,", "Model 2,", "Model 3,", "Model 4,", "Model 5,")))
    f["t2_pv_second"] = T["table2_pvalues"]["summary"].get("second_within", "n/a")
    f["t2_pv_flips"] = sum(1 for x in T["table2_pvalues"]["fields"] if x.get("second_run") != x["observed"])
    f["s0_nc_30x5_004"] = f"{R['cells']['J30_n5_icc0.04']['sigma0']['noncoverage']:.3f}"
    f["s0_nc_100x5_004"] = f"{R['cells']['J100_n5_icc0.04']['sigma0']['noncoverage']:.3f}"
    f["s1_30x5"] = ", ".join(f"{R['cells'][f'J30_n5_icc{i}']['sigma1']['bias_pct']:.1f}" for i in ("0.04", "0.17", "0.38"))
    f["s1_30x5_second"] = ", ".join(f"{sim['runs']['second']['cells'][f'J30_n5_icc{i}']['sigma1']['bias_pct']:.1f}" for i in ("0.04", "0.17", "0.38"))
    f["s1_30x5_interior"] = ", ".join(f"{R['interior'][f'J30_n5_icc{i}']['sigma1']['bias_pct']:.1f}" for i in ("0.04", "0.17", "0.38"))
    f["conv_30x5_interior"] = ", ".join(f"{R['interior'][f'J30_n5_icc{i}']['converged_pct']:.0f}" for i in ("0.04", "0.17", "0.38"))
    pp = sim["prevalence"]["pooled"]
    f["t4_s1_010"] = f1(pp["all_cells"]["0.10"]["sigma1"]["bias_pct"])
    f["t4_best_subset"] = "30 groups of 5 and of 50"
    for cid, c in cl.items():
        if cid.startswith("_"):
            continue
        for i, fl in enumerate(c["fields"]):
            for key, pre in (("observed", "c"), ("second_run", "s")):
                v = fl.get(key)
                f[f"{pre}_{cid}_{i}"] = (f"{v:.2f}" if abs(v) < 10 else f"{v:.1f}") if isinstance(v, float) else v
    rtc = rt["robustness_tests"]["convergence"]
    f["rt_m2_5"] = f"{rtc['5']['2']['pct']:.0f}"
    f["rt_m1_5"] = f"{rtc['5']['1' if '1' in rtc['5'] else '2']['model1_pct']:.0f}"
    f["rt_m2_p"] = f"{rtc['5']['2']['p']:.3f}"
    f["rt_m4_30"] = f"{rtc['30']['4']['pct']:.0f}"
    f["rt_m5_30"] = f"{rtc['30']['5']['pct']:.0f}"
    PL = {"g00": "γ00", "g01": "γ01", "g10": "γ10", "g11": "γ11", "sigma0": "σ0", "sigma1": "σ1"}
    worst50 = max(((c, p) for c in cells if c.startswith("J50_n30_") for p in ("g00", "g01", "g10", "g11")),
                  key=lambda cp: abs(cells[cp[0]][cp[1]]["bias_pct"]))
    f["fix50x30_par"] = PL[worst50[1]]
    f["fix50x30_icc"] = worst50[0].split("icc")[1]
    f["fix50x30_val"] = f1(cells[worst50[0]][worst50[1]]["bias_pct"])
    f["fix50x30_se"] = f1(cells[worst50[0]][worst50[1]]["bias_mcse"])
    worst100 = max(((c, p) for c in cells if c.startswith("J100_n50_") for p in ("sigma0", "sigma1")),
                   key=lambda cp: abs(cells[cp[0]][cp[1]]["bias_pct"]))
    f["var100x50_par"] = PL[worst100[1]]
    f["var100x50_icc"] = worst100[0].split("icc")[1]
    f["var100x50_val"] = f1(cells[worst100[0]][worst100[1]]["bias_pct"])
    f["var100x50_se"] = f1(cells[worst100[0]][worst100[1]]["bias_mcse"])
    f["fixnc_min"] = f1(100 * min(cells[c][p]["noncoverage"] for c in cells for p in ("g00", "g01", "g10", "g11")))
    f["conv_30x5_004"] = f"{cells['J30_n5_icc0.04']['converged_pct']:.0f}"
    rob = sim["robustness"]["cells"]
    f["t5_m1_conv5"] = f"{sum(rob[f'm1_J{J}_n5']['converged_pct'] for J in (30, 50, 100)) / 3:.0f}"
    nm = rt["normality"]
    for key, g, nn in (("100x5", 100, 5), ("100x50", 100, 50)):
        f[f"norm01_{key}"] = sum(nm[f"J{g}_n{nn}_icc{i}"][p]["p"] < 0.01 for i in ("0.04", "0.17", "0.38")
                                 for p in ("g00", "g01", "g10", "g11"))
    cn = cl["text_normality"]["counts"]
    f.update({"norm_100x5": cn["100x5"][0], "norm_50x30": cn["50x30"][0], "norm_100x50": cn["100x50"][0]})
    f["nc_wald_both"] = f1(nc["both_significant_pct"])
    f["nc_lrt_both"] = f1(nc["lrt"]["both_significant_pct"])
    f["nc_by_cell"] = ", ".join(str(v["datasets"]) for v in nc["by_cell"].values())
    t4bn = [x for x in T["table4"]["fields"] if "converged" not in x["name"]]
    f["t4_bnc_within"], f["t4_bnc_total"] = sum(x["within"] for x in t4bn), len(t4bn)
    mc = cl["text_main_claim"]["fields"]
    f["mc_hold"] = sum(x["observed"] == x["expected"] for x in mc)
    f["mc_total"] = len(mc)
    for k in ("cells_within", "cells_total", "main_cells_within", "main_cells_total"):
        f[k] = f"{f[k]:,}"
    # second run
    f["second_conv_30x5"] = ", ".join(f"{sim['runs']['second']['cells'][f'J30_n5_icc{i}']['converged_pct']:.0f}" for i in ("0.04", "0.17", "0.38"))
    return f


def claim_obs(cl, cid, i):
    v = cl[cid]["fields"][i]["observed"]
    return v / 100 if isinstance(v, float) else v


def fill(obj, facts):
    """Replace {name} for every known fact in every string of obj; fail on an unknown {name}."""
    if isinstance(obj, str):
        def rep(m):
            if m.group(1) not in facts:
                raise KeyError(f"results_notes.json cites an unknown fact {{{m.group(1)}}}")
            return str(facts[m.group(1)])
        return re.sub(r"\{([a-z0-9_.]+)\}", rep, obj)
    if isinstance(obj, list):
        return [fill(x, facts) for x in obj]
    if isinstance(obj, dict):
        return {k: fill(v, facts) for k, v in obj.items()}
    return obj


def arithmetic(claims):
    """text.arithmetic: each claim's statement or number recomputed from the paper's own tables."""
    back, missed = [], []
    for cid, c in claims.items():
        for f in c["fields"]:
            a = f.get("arithmetic")
            if a is None:
                continue
            tol = f.get("arithmetic_tolerance") or (f.get("tolerance") if cid.startswith("_") else {"printed": True})
            g = {"expected": f["expected"], "observed": a, "tolerance": tol}
            (back if matches(g) else missed).append(f"{cid.strip('_')}: {f['name']} ({f['expected']} against {a})")
    detail = (f"{len(back)} of {len(back) + len(missed)} statements and pooled values follow from the paper's own tables. "
              + ("Not: " + "; ".join(missed) + "." if missed else ""))
    return True, detail


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
    notes = {k: (fill(v, facts) if k in ("items", "assumption_sets") else v) for k, v in notes.items()}
    run_block = copy.deepcopy(notes["run"])
    if env:
        run_block["environment"] = env
    res = {"schema": "paper2repro/results/v1", "paper": notes["paper"], "run": run_block,
           "session": notes["session"], "skill": notes["skill"], "items": []}
    stale = []
    for it in notes["items"]:
        it = copy.deepcopy(it)
        sets = it.pop("assumptions_from", [])
        if sets:
            it["assumptions"] = [a for s in sets for a in notes["assumption_sets"][s]] + it.get("assumptions", [])
        expect = it.pop("expect_misses", None)
        src = it.pop("fields_from", None)
        if it.get("label", "").startswith("LABEL:"):
            it["label"] = get(run, f"claims.json:{it['label'][6:]}/label")
        if src:
            got = get(run, src)
            fields = [{k: f[k] for k in f if k in FIELD_KEYS} for f in (got if isinstance(got, list) else got["fields"])]
            it["values"] = {"fields": fields, "tolerance": {"printed": True}}
            if "exceptions" in it:
                it["values"]["exceptions"] = it.pop("exceptions")
            excepted = {e["field"] for e in it["values"].get("exceptions", [])}
            names = {f["name"] for f in fields}
            for e in excepted - names:
                stale.append(f"{it['id']}: exception for a field the run does not have: {e}")
            misses = [f["name"] for f in fields if f["name"] not in excepted and not matches(f, {"printed": True})]
            if expect is not None and expect != "any" and sorted(misses) != sorted(expect):
                stale.append(f"{it['id']}: misses {misses}, notes expect {expect}")
            if misses and "cause" not in it:
                stale.append(f"{it['id']}: {len(misses)} misses and no cause")
        chk = it.pop("check_from", None)
        if chk in ("package.json", "crosscheck.json", "sim_check.json"):
            p = Path(run) / chk
            d = json.load(open(p)) if p.exists() else {"passed": False, "detail": f"{chk} not written"}
            it["check"] = {"passed": bool(d["passed"]), "detail": d.get("detail", "")}
        elif chk == "claims.json":
            passed, detail = arithmetic(json.load(open(Path(run) / chk)))
            it["check"] = {"passed": passed, "detail": detail}
        res["items"].append(it)
    if stale:
        print("Causes in results_notes.json no longer match the run:\n  " + "\n  ".join(stale), file=sys.stderr)
        sys.exit(1)
    with open(out, "w") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
        f.write("\n")
    r = subprocess.run([sys.executable, str(HERE / "check_results.py"), out, "--write"])
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()

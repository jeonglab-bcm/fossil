"""Merge results_notes.json (written by hand: labels, assumptions, causes) with the numbers of a run into
results.json, then let check_results.py compute every verdict and the summary.

Usage: build_results.py RUN_DIR OUT.json [--environment ENV.json]

Notes items take their numbers from the run folder:
  "fields_from": "comparison.json:tables/table1"   values.fields from that file and key path
  "pixels_from": "figure.json:panels/a"            pixels block (scores, threshold, controls)
  "check_from": "package.json" | "crosscheck.json" | "claims.json" | "figure.json"
  "assumptions_from": [...]                        shared assumption sets of the notes
  "expect_misses": [...]                           the fields the item's cause explains; the build fails when the
                                                   run's misses differ, so a stale cause cannot reach the page
Every {name} in the notes' prose is filled from the run (facts_of), so no number in the prose is typed.
The skill block and the session pointer travel with the notes, unchanged.
"""
import copy
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTES = HERE.parent / "results_notes.json"
FIELD_KEYS = ("name", "expected", "observed", "tolerance", "arithmetic", "second_run")
TABLES = ("table1", "table2", "table3", "tableA1", "tableA2", "tableA3")
PIXEL_KEYS = ("tolerance_px", "dpi", "published_near_ours", "ours_near_published", "threshold", "controls")


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


def c(n):
    return f"{n:,}"


def facts_of(run):
    """Numbers the hand-written notes cite, taken from the run so the prose cannot drift from it."""
    run = Path(run)
    cmp_ = json.load(open(run / "comparison.json"))
    sim = json.load(open(run / "simulation.json"))
    cl = json.load(open(run / "claims.json"))
    fig = json.load(open(run / "figure.json"))
    x = json.load(open(run / "crosscheck.json"))
    T, H = cmp_["tables"], cmp_["hypotheses"]
    f = {"cells": c(sum(T[t]["summary"]["fields"] for t in TABLES)),
         "within": c(sum(T[t]["summary"]["within"] for t in TABLES)),
         "second_within": c(sum(cmp_["replicate"][t]["within"] for t in TABLES)),
         "rms_min": f"{min(T[t]['summary']['rms_z'] for t in TABLES):.2f}",
         "rms_max": f"{max(T[t]['summary']['rms_z'] for t in TABLES):.2f}",
         "reps": c(sim["reps"])}
    for t in TABLES:
        s = T[t]["summary"]
        f[f"{t}_within"] = s["within"]
        f[f"{t}_rms"] = f"{s['rms_z']:.2f}"
        f[f"{t}_second"] = cmp_["replicate"][t]["within"]
        ctl = cmp_["controls"][t]
        names = list(ctl)
        f[f"{t}_ctl_n"] = ctl[names[0]]["within"]
        f[f"{t}_ctl_form"] = ctl[names[1]]["within"]
        f[f"{t}_ctl_rr"] = ctl[names[2]]["within"]
    for name, v in H.items():
        for t, s in v.items():
            f[f"h_{name}_{t}"] = s["within"]
            f[f"h_{name}_{t}_of"] = s["fields"]
            f[f"h_{name}_{t}_main"] = s["main_run"]["within"]
            if "sample_run" in s:
                f[f"h_{name}_{t}_sample"] = s["sample_run"]["within"]
    # the misprint in Table 3
    typo = next(fl for fl in T["table3"]["fields"] if fl["name"] == "RR 2.0, 25%, 5%: linear strong, LB")
    rp = next(fl for fl in T["table3"]["fields"] if fl["name"] == "RR 2.0, 25%, 5%: linear strong, RP")
    inc = cmp_["consistency"]["table3"]["inconsistent"]
    imp = next(i for i in inc if i["name"] == typo["name"])
    f.update({"typo_ours": f"{typo['observed']:.4f}", "typo_second": f"{typo['second_run']:.4f}", "typo_implied": f"{imp['implied']:.4f}",
              "typo_rp_ours": f"{rp['observed']:.4f}",
              "cons3": cmp_["consistency"]["table3"]["consistent"], "consA3": cmp_["consistency"]["tableA3"]["consistent"],
              "cons_other3": "; ".join(f"{i['name']} prints {i['printed_mse']} against {i['range'][0]:.4f} to {i['range'][1]:.4f}"
                                       for i in inc if i["name"] != typo["name"]),
              "cons_n_other3": len([i for i in inc if i["name"] != typo["name"]]),
              "cons_otherA3": "; ".join(f"{i['name']} prints {i['printed_mse']} against {i['range'][0]:.4f} to {i['range'][1]:.4f}"
                                        for i in cmp_["consistency"]["tableA3"]["inconsistent"]),
              "cons_n_otherA3": len(cmp_["consistency"]["tableA3"]["inconsistent"])})
    # contamination
    m15 = sim["runs"]["main"]["n1500"]
    fl5 = [v["5%"]["flipped_mean"] for v in m15.values()]
    sd5 = [v["5%"]["flipped_sd"] for v in m15.values()]
    f.update({"flip5_mean": f"{sum(fl5) / len(fl5):.1f}", "flip5_sd": f"{sum(sd5) / len(sd5):.1f}",
              "flip5_sample": sim["flipped_per_tail_sample"]["n1500"]["5%"] * 2})
    se_l = [T["table2"]["fields"][i] for i in range(len(T["table2"]["fields"]))
            if T["table2"]["fields"][i]["name"].startswith(("RR 1.5, 10%, 5%: linear", "RR 2.0, 10%, 5%: linear"))]
    f["se_lin10_ours"] = ", ".join(f"{x_['observed']:.3f}" for x_ in se_l)
    f["se_lin10_paper"] = ", ".join(x_["expected"] for x_ in se_l)
    # figure
    P = fig["panels"]
    for p, v in P.items():
        f[f"fig_{p}"] = f"{min(v['published_near_ours'], v['ours_near_published']):.3f}"
        f[f"fig_{p}_wrong"] = f"{max(x_['score'] for x_ in v['controls'] if x_['kind'] == 'wrong_input'):.3f}"
        f[f"fig_{p}_near"] = f"{max(x_['score'] for x_ in v['controls'] if x_['kind'] == 'near_miss'):.3f}"
        f[f"fig_{p}_thr"] = f"{v['threshold']:.2f}"
        f[f"fig_{p}_paper"] = f"{min(v['paper_table1_drawn'].values()):.3f}"
        f[f"fig_{p}_self"] = f"{v['second_run_vs_ours']:.3f}"
    f["px_per_point"] = f"{abs(sum(v['y_per_point'] for v in fig['calibration'].values()) / len(fig['calibration'])):.2f}"
    mcs = [v[r][m]["relbias_mcse"] for v in m15.values() for r in ("0%", "2%", "5%") for m in ("LB", "RP")]
    f["mc_min"], f["mc_max"] = f"{min(mcs):.1f}", f"{max(mcs):.1f}"
    for p_, key in (("a", "linear|moderate"), ("b", "linear|strong"), ("c", "nonlinear|moderate"), ("d", "nonlinear|strong")):
        z = T["table1"]["summary"]["rms_z_by_panel"][key]
        f[f"fig_{p_}_z"], f[f"fig_{p_}_z2"] = f"{z['ours_vs_paper']:.2f}", f"{z['second_vs_ours']:.2f}"
    f["fig_paper_min"] = f"{min(min(v['paper_table1_drawn'].values()) for v in P.values()):.3f}"
    f["fig_self_min"] = f"{min(v['second_run_vs_ours'] for v in P.values()):.3f}"
    f["fig_self_max"] = f"{max(v['second_run_vs_ours'] for v in P.values()):.3f}"
    co = fig["consistency"]
    f.update({"vert_read": co["read"], "vert_all": co["vertices"], "vert_within": co["within_1_point"],
              "vert_max": f"{co['max_abs_difference']:.2f}", "tick_res": f"{fig['max_tick_residual_px']:.2f}"})
    # claims
    g = cl["text.linear_gap"]["gaps"]
    f["gaps_paper"] = ", ".join(f"{x_['paper']:.1f}" for x_ in g)
    f["gaps_ours"] = ", ".join(f"{x_['ours']:.2f}" for x_ in g)
    f["se0_diff"] = f"{cl['text.se_uncontaminated']['ours_largest_unrounded_difference']:.4f}"
    cv = cl["text.convergence"]["ours"]
    f.update({"copy_lin": cv["linear"]["copy_needed_in_some_fit"], "copy_non": cv["nonlinear"]["copy_needed_in_some_fit"],
              "copy_non_max": cv["nonlinear"]["copy_used_max"], "copy_non_med": f"{cv['nonlinear']['copy_used_median']:.0f}",
              "copy_lin_max": cv["linear"]["copy_used_max"]})
    d = cl["design"]["fields"]
    f["design_x_dev"] = f"{max(abs(x_['observed'] - 50) for x_ in d if 'P(X' in x_['name']):.2f}"
    f["design_y_dev"] = f"{max(abs(x_['observed'] - float(x_['expected'])) for x_ in d if 'P(Y' in x_['name']):.2f}"
    f["design_pmax"] = f"{max(x_.get('largest_p_y', 0) for x_ in d):.3f}"
    f["x_detail"] = x["detail"]
    pub = json.load(open(run / "published_values.json"))
    rest_p, rest_o = [], []
    for row in pub["tables"]["table1"]["rows"]:
        if row["contamination"] == "0%" or (row["py"] == "10%" and row["contamination"] == "5%"):
            continue
        for lev in ("moderate", "strong"):
            lb, rp = float(row["cells"][f"linear|{lev}|LB"]), float(row["cells"][f"linear|{lev}|RP"])
            rest_p.append(abs(abs(lb) - abs(rp)))
            o = m15[f"{row['rr']}|{row['py']}|linear|{lev}"][row["contamination"]]
            rest_o.append(abs(abs(o["LB"]["relbias"]) - abs(o["RP"]["relbias"])))
    f["lin_rest_paper"] = f"{max(rest_p):.1f}"
    f["lin_rest_ours"] = f"{max(rest_o):.1f}"
    return f


def fill(obj, facts):
    """Replace {name} for every known fact in every string of obj; fail on an unknown {name}."""
    if isinstance(obj, str):
        def rep(m):
            if m.group(1) not in facts:
                raise KeyError(f"results_notes.json cites an unknown fact {{{m.group(1)}}}")
            return str(facts[m.group(1)])
        return re.sub(r"\{([A-Za-z0-9_]+)\}", rep, obj)
    if isinstance(obj, list):
        return [fill(x, facts) for x in obj]
    if isinstance(obj, dict):
        return {k: fill(v, facts) for k, v in obj.items()}
    return obj


def arithmetic(claims):
    """text.arithmetic: each claim recomputed from the paper's own tables."""
    back, missed = [], []
    for cid, cl in claims.items():
        if cid.startswith("_"):
            continue
        for fl in cl["fields"]:
            a = fl.get("arithmetic")
            if a is None:
                continue
            g = {"expected": fl["expected"], "observed": a, "tolerance": {"printed": True}}
            (back if matches(g) else missed).append(f"{cid}: {fl['name']} ({fl['expected']} against {a})")
    detail = (f"{len(back)} of {len(back) + len(missed)} statements follow from the paper's own tables."
              + (" Not: " + "; ".join(missed) + "." if missed else ""))
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
        if src:
            fields = [{k: fl[k] for k in fl if k in FIELD_KEYS} for fl in get(run, src)["fields"]]
            it["values"] = {"fields": fields, "tolerance": {"printed": True}}
            if "exceptions" in it:
                it["values"]["exceptions"] = it.pop("exceptions")
            excepted = {e["field"] for e in it["values"].get("exceptions", [])}
            names = {fl["name"] for fl in fields}
            for e in excepted - names:
                stale.append(f"{it['id']}: exception for a field the run does not have: {e}")
            misses = [fl["name"] for fl in fields if fl["name"] not in excepted and not matches(fl, {"printed": True})]
            if sorted(misses) != sorted(expect or []):
                stale.append(f"{it['id']}: misses {misses}, notes expect {expect or []}")
        pix = it.pop("pixels_from", None)
        if pix:
            p = get(run, pix)
            it["pixels"] = {k: p[k] for k in PIXEL_KEYS}
        chk = it.pop("check_from", None)
        if chk in ("package.json", "crosscheck.json"):
            p = Path(run) / chk
            d = json.load(open(p)) if p.exists() else {"passed": False, "detail": f"{chk} not written"}
            it["check"] = {"passed": bool(d["passed"]), "detail": d.get("detail", "")}
        elif chk == "claims.json":
            passed, detail = arithmetic(json.load(open(Path(run) / chk)))
            it["check"] = {"passed": passed, "detail": detail}
        elif chk == "figure.json":
            co = get(run, "figure.json:consistency")
            ok = co["within_1_point"] >= 0.95 * co["read"]
            it["check"] = {"passed": ok, "detail": f"{co['within_1_point']} of the {co['read']} vertices of Fig. 1 that can be read "
                                                   f"(of {co['vertices']}) lie within 1 point of Table 1 as printed; largest difference "
                                                   f"{co['max_abs_difference']:.2f} points"}
        res["items"].append(it)
    if stale:
        print("Causes in results_notes.json no longer match the run:\n  " + "\n  ".join(stale), file=sys.stderr)
        sys.exit(1)
    with open(out, "w") as fh:
        json.dump(res, fh, indent=1)
        fh.write("\n")
    r = subprocess.run([sys.executable, str(HERE / "check_results.py"), out, "--write"])
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()

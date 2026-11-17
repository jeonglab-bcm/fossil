"""Merge results_notes.json (written by hand: labels, assumptions, causes) with the numbers of a run
into results.json, then let check_results.py compute every verdict and the summary.

Usage: build_results.py RUN_DIR OUT.json [--environment ENV.json]

Notes items take their numbers from the run folder:
  "fields_from": "comparison.json:tables/S1"   values.fields from that file and key path
  "pixels_from": "figures/figures.json:figures/fig1"  pixels block (scores and controls), with the item's threshold
  "check_from": "package.json"                 check.passed and detail from check_package.py's report
  "check_from": "claims.json"                  text.arithmetic: the claims recomputed from the paper's tables
  "assumptions_from": [...]                    shared assumption sets of the notes
  "cause_from": "eq10"                         a shared cause of the notes
  "expect_misses": [...]                       the fields the cause explains; the build fails when the run's
                                               misses differ, so a stale cause cannot reach the page
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
FIELD_KEYS = ("name", "expected", "observed", "tolerance")


def get(run, ref):
    f, _, key = ref.partition(":")
    d = json.load(open(Path(run) / f))
    for k in key.split("/") if key else []:
        d = d[k]
    return d


def matches(f):
    sys.path.insert(0, str(HERE))
    from check_results import field_matches
    return field_matches(f, None)


def facts_of(run):
    """Numbers the hand-written notes cite, taken from the run so the prose cannot drift from it."""
    c = json.load(open(Path(run) / "comparison.json"))
    own = c["replicate"]["own_runs_within"]
    hyp = c["hypotheses"]
    nofirst_bars = sum(f["eq10_no_first_term"]["within"] for f in c["figures"].values())
    bars = sum(f["summary"]["fields"] for f in c["figures"].values())
    outside = [1 - v["within"] / c["tables"][t]["summary"]["fields"]
               for t in ("S1", "S3", "S5", "S6", "S7") for v in c["controls"][t].values()]
    return {
        "ctrl_out_min": f"{100 * min(outside):.0f}", "ctrl_out_max": f"{100 * max(outside):.0f}",
        "s6_ctrl_max": max(v["within"] for v in c["controls"]["S6"].values()),
        "own_within": own["within"], "own_cells": own["cells"], "own_miss": own["cells"] - own["within"],
        "own_pct": f"{100 * own['within'] / own['cells']:.1f}", "own_miss_pct": f"{100 * (own['cells'] - own['within']) / own['cells']:.1f}",
        "s6_cells": c["tables"]["S6"]["summary"]["fields"], "s6_within": c["tables"]["S6"]["summary"]["within"],
        "s6_nofirst_within": hyp["eq10_no_first_term"]["S6"]["within"], "s6_nofirst_rms": hyp["eq10_no_first_term"]["S6"]["rms_z"],
        "s6_varnotlog_within": hyp["eq10_var_not_log"]["S6"]["within"], "s6_n2_within": hyp["eq10_n2_for_n1"]["S6"]["within"],
        "s6_p1d_within": hyp["eq10_p1d_for_p1u"]["S6"]["within"], "s6_rms": c["tables"]["S6"]["summary"]["rms_z"],
        "bars": bars, "bars_nofirst_within": nofirst_bars,
        "s1_rms": c["tables"]["S1"]["summary"]["rms_z"], "s2_rms": c["tables"]["S2"]["summary"]["rms_z"],
        "s5_rms": c["tables"]["S5"]["summary"]["rms_z"], "s7_rms": c["tables"]["S7"]["summary"]["rms_z"],
        "s1_label_within": hyp["true_esr_label"]["S1"]["within"], "s2_label_within": hyp["true_esr_label"]["S2"]["within"],
        "s1_label_rms": hyp["true_esr_label"]["S1"]["rms_z"], "s2_label_rms": hyp["true_esr_label"]["S2"]["rms_z"],
        "s1_realized_rms": hyp["true_esr_realized"]["S1"]["rms_z"], "s2_realized_rms": hyp["true_esr_realized"]["S2"]["rms_z"],
        "s5_missing_rms": hyp["zero_missing"]["S5"]["rms_z"], "s5_notcov_within": hyp["zero_not_covered"]["S5"]["within"],
        "s5_notcov_rms": hyp["zero_not_covered"]["S5"]["rms_z"], "s7_half_within": hyp["zero_half"]["S7"]["within"],
        "s7_half_rms": hyp["zero_half"]["S7"]["rms_z"],
        "s6_zero_range": f"{min(hyp[h]['S6']['within'] for h in ('zero_missing', 'zero_not_covered', 'zero_half'))} to "
                         f"{max(hyp[h]['S6']['within'] for h in ('zero_missing', 'zero_not_covered', 'zero_half'))}",
    }


def fill(obj, facts):
    """Replace {name} for every known fact in every string of obj; fail on an unknown {name}."""
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
    """text.arithmetic: each claim's statement or number recomputed from the paper's own tables."""
    back, missed = [], []
    for cid, c in claims.items():
        if cid.startswith("_"):
            continue
        for f in c["fields"]:
            a = f.get("arithmetic")
            if a is None:
                continue
            g = {"expected": f["expected"], "observed": a, "tolerance": {"printed": True}}
            (back if matches(g) else missed).append(f"{cid}: {f['name']} ({f['expected']} against {a})")
    inc = claims.get("_table_inconsistencies", [])
    detail = (f"{len(back)} of {len(back) + len(missed)} statements follow from the paper's own tables and figures. "
              f"Not: " + "; ".join(missed) + ". "
              f"Tables 2-4 restate Tables S1, S2, S5-S7 in every cell but {len(inc)}: "
              + "; ".join(f"{i['table']} {i['cell']} {i['value']} against {i['supplement']} {i['supplement_value']}" for i in inc))
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
    notes = {k: (fill(v, facts) if k in ("items", "causes", "assumption_sets") else v) for k, v in notes.items()}
    comparison = json.load(open(Path(run) / "comparison.json"))
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
        cause = it.pop("cause_from", None)
        expect = it.pop("expect_misses", None)
        src = it.pop("fields_from", None)
        if src:
            fields = [{k: f[k] for k in f if k in FIELD_KEYS or k in ("arithmetic", "second_run", "without_eq10_first_term", "z")}
                      for f in get(run, src)["fields"] if f.get("observed") is not None]
            it["values"] = {"fields": fields}
            if "exceptions" in it:
                it["values"]["exceptions"] = it.pop("exceptions")
            if all("tolerance" in f for f in fields) is False:
                it["values"]["tolerance"] = {"printed": True}
            misses = [f["name"] for f in fields if not matches(dict(f, tolerance=f.get("tolerance", {"printed": True})))]
            if expect == "S6":
                expect = misses if misses and len(misses) > 20 else ["(at least 20 cells)"]
            if expect is not None and sorted(misses) != sorted(expect):
                stale.append(f"{it['id']}: misses {misses}, notes expect {expect}")
            if misses and cause and "cause" not in it:
                it["cause"] = copy.deepcopy(notes["causes"][cause])
            if misses and cause == "chance":
                # The chance cause says our second run puts every missed cell within tolerance: check it.
                key = src.split(":")[1].split("/")[-1]
                rep = comparison["replicate"].get(key)
                if rep is None or rep["within"] != rep["fields"]:
                    stale.append(f"{it['id']}: cause 'chance' needs the second run within everywhere, got {rep}")
        pix = it.pop("pixels_from", None)
        if pix:
            d = get(run, pix)
            tol = json.load(open(Path(run) / pix.split(":")[0]))["tolerance_px"]
            it["pixels"] = {"tolerance_px": tol, "dpi": 599, "published_near_ours": d["published_near_ours"],
                            "ours_near_published": d["ours_near_published"], "threshold": it.pop("threshold"),
                            "controls": d["controls"],
                            "hypotheses": {k: min(v["published_near_ours"], v["ours_near_published"]) for k, v in d["hypotheses"].items()}}
            if cause and "cause" not in it:
                it["cause"] = copy.deepcopy(notes["causes"][cause])
        chk = it.pop("check_from", None)
        if chk == "package.json":
            p = Path(run) / chk
            d = json.load(open(p)) if p.exists() else {"passed": False, "detail": "package check not run"}
            it["check"] = {"passed": bool(d["passed"]), "detail": d.get("detail", "")}
        elif chk == "claims.json":
            passed, detail = arithmetic(json.load(open(Path(run) / chk)))
            it["check"] = {"passed": passed, "detail": detail}
        res["items"].append(it)
    if stale:
        print("Causes in results_notes.json no longer match the run:\n  " + "\n  ".join(stale), file=sys.stderr)
        sys.exit(1)
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
        f.write("\n")
    # Output files are checked against the paper folder by check_reproduction.py; here only the numbers.
    r = subprocess.run([sys.executable, str(HERE / "check_results.py"), out, "--write", "--skip-files"])
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()

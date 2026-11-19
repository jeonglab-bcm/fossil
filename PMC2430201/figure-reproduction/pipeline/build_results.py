"""Merge results_notes.json (written by hand: labels, assumptions, causes) with the numbers of a run into
results.json, then let check_results.py compute every verdict and the summary.

Usage: build_results.py RUN_DIR OUT.json [--environment ENV.json]

Notes items take their numbers from the run folder:
  "fields_from": "comparison.json:tables/3"   values.fields from that file and key path
  "check_from": "package.json" | "crosscheck.json" | "claims.json"   check.passed and detail
  "assumptions_from": [...]                    shared assumption sets of the notes
  "cause_from": "chance"                       a shared cause of the notes, added when the item has misses
  "expect_misses": [...]                       the fields the cause explains; the build fails when the run's
                                               misses differ, so a stale cause cannot reach the page
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
TABLES = ("3", "4", "5", "6", "7", "8")


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


def pct(a, b):
    return f"{100 * a / b:.0f}"


def facts_of(run):
    """Numbers the hand-written notes cite, taken from the run so the prose cannot drift from it."""
    run = Path(run)
    c = json.load(open(run / "comparison.json"))
    sim = json.load(open(run / "simulation.json"))
    cl = json.load(open(run / "claims.json"))
    x = json.load(open(run / "crosscheck.json"))
    T, H = c["tables"], c["hypotheses"]
    f = {"cells": sum(T[t]["summary"]["fields"] for t in TABLES), "within": sum(T[t]["summary"]["within"] for t in TABLES),
         "rounds": sum(T[t]["summary"]["rounds_to_printed"] for t in TABLES),
         "second_within": sum(c["replicate"][t]["within"] for t in TABLES),
         "own_within": c["replicate"]["own_runs_within"]["within"], "own_cells": c["replicate"]["own_runs_within"]["cells"],
         "rms_min": f"{min(T[t]['summary']['rms_z'] for t in TABLES):.2f}", "rms_max": f"{max(T[t]['summary']['rms_z'] for t in TABLES):.2f}"}
    f["rounds_pct"] = pct(f["rounds"], f["cells"])
    for k in ("cells", "within", "rounds", "second_within", "own_within", "own_cells"):
        f[k] = f"{f[k]:,}"
    for t in TABLES:
        f[f"t{t}_within"] = T[t]["summary"]["within"]
        f[f"t{t}_rms"] = f"{T[t]['summary']['rms_z']:.2f}"
        f[f"t{t}_second"] = c["replicate"][t]["within"]
    for h in ("rom_bias_ratio", "rom_bias_ln", "rom_bias_rm1", "i2_from_mean_q", "i2_mean_of_replicates", "i2_median_of_replicates"):
        f[f"{h}_within"] = sum(H[h][t]["within"] for t in TABLES)
        f[f"{h}_cells"] = sum(H[h][t]["fields"] for t in TABLES)
    het = ("3", "4", "5", "7", "8")
    for h in ("het_experimental_only", "het_shared"):
        f[f"{h}_within"] = sum(H[h][t]["within"] for t in het)
        f[f"{h}_cells"] = sum(H[h][t]["fields"] for t in het)
    f["het_independent_within"] = sum(H["het_shared"][t]["main_run"]["within"] for t in het)
    for h, t in (("skew_multiplicative", "6"), ("skew_standardized", "6"), ("draw_values", "3"),
                 ("negative_drop_replicate", "5"), ("sd_pool_literal", "4"), ("no_hedges", "3")):
        f[f"{h}_within"] = H[h][t]["within"]
        f[f"{h}_rms"] = f"{H[h][t]['rms_z']:.2f}"
    rom_wrong = [v["rom_columns"]["within"] for t in TABLES for k, v in c["controls"][t].items() if "right design" not in k]
    rom_right = [v["rom_columns"]["within"] for t in TABLES for k, v in c["controls"][t].items() if "right design" in k]
    all_wrong = [v["within"] for t in TABLES for k, v in c["controls"][t].items() if "right design" not in k]
    f.update({"ctrl_rom_min": min(rom_wrong), "ctrl_rom_max": max(rom_wrong), "right_rom_min": min(rom_right),
              "ctrl_all_min": min(all_wrong), "ctrl_all_max": max(all_wrong),
              "ctrl_rms_min": f"{min(v['rom_columns']['rms_z'] for t in TABLES for k, v in c['controls'][t].items() if 'right design' not in k):.1f}"})
    for t in ("3", "6"):
        for fl in T[t]["fields"]:
            if not matches(fl):
                f[f"t{t}_miss_name"] = fl["name"]
                f[f"t{t}_miss_paper"] = fl["expected"]
                f[f"t{t}_miss_ours"] = f"{fl['observed']:.2f}"
                f[f"t{t}_miss_second"] = f"{fl['second_run']:.2f}"
                f[f"t{t}_miss_tol"] = f"{fl['tolerance']['abs']:.2f}"
    md_i2 = [r["tau0.5"]["MD"]["i2"] for r in sim["runs"]["main"]["6"] if r["n"] == "10/10" and r["k"] == 30]
    md_i2_std = [r["tau0.5"]["MD"]["i2"] for r in sim["variants"]["skew_standardized"]["runs"]["6"] if r["n"] == "10/10" and r["k"] == 30]
    md_i2_2 = [r["tau0.5"]["MD"]["i2"] for r in sim["runs"]["second"]["6"] if r["n"] == "10/10" and r["k"] == 30]
    f.update({"t6_md_i2_k30": ", ".join(f"{v:.2f}" for v in md_i2), "t6_md_i2_k30_std": ", ".join(f"{v:.2f}" for v in md_i2_std),
              "t6_md_i2_k30_second": ", ".join(f"{v:.2f}" for v in md_i2_2)})
    sel = cl["text_biased_rom_coverage"]["selected"]
    f.update({"biased_n_paper": len(sel["paper"]), "biased_n_ours": len(sel["ours"])})
    f.update({"x_fits": x["pooling"]["fits"], "x_diff": f"{x['pooling']['max_relative_difference']:.0e}",
              "x_left_out": x["pooling"]["rom_studies_left_out"],
              "power_close_ours": cl["text_power"]["shown"]["ours"], "power_close_paper": cl["text_power"]["shown"]["paper"]})
    left = sum(r[f"tau{tau}"]["RoM"]["studies_left_out"] for r in sim["runs"]["main"]["5"] for tau in ("0", "0.5"))
    f["t5_left_out"] = left
    f["t5_studies"] = f"{sum(r['k'] * 2 * sim['replicates'] for r in sim['runs']['main']['5']):,}"
    return f


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
    detail = (f"{len(back)} of {len(back) + len(missed)} statements follow from the paper's own tables. "
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
    notes = {k: (fill(v, facts) if k in ("items", "causes", "assumption_sets") else v) for k, v in notes.items()}
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
            fields = [{k: f[k] for k in f if k in FIELD_KEYS} for f in get(run, src)["fields"]]
            it["values"] = {"fields": fields, "tolerance": {"printed": True}}
            if "exceptions" in it:
                it["values"]["exceptions"] = it.pop("exceptions")
            excepted = {e["field"] for e in it["values"].get("exceptions", [])}
            names = {f["name"] for f in fields}
            for e in excepted - names:
                stale.append(f"{it['id']}: exception for a field the run does not have: {e}")
            misses = [f["name"] for f in fields if f["name"] not in excepted and not matches(f, {"printed": True})]
            if expect is not None and sorted(misses) != sorted(expect):
                stale.append(f"{it['id']}: misses {misses}, notes expect {expect}")
            if misses and cause and "cause" not in it:
                it["cause"] = copy.deepcopy(notes["causes"][cause])
            if misses and (it.get("cause") or {}).get("category") == "nondeterminism":
                # A chance miss: our second run, with other seeds, must put every missed cell within tolerance.
                for f in fields:
                    if f["name"] in misses and (f.get("second_run") is None or not matches({**f, "observed": f["second_run"]})):
                        stale.append(f"{it['id']}: a chance cause needs the second run within tolerance for {f['name']}")
        chk = it.pop("check_from", None)
        if chk in ("package.json", "crosscheck.json"):
            p = Path(run) / chk
            d = json.load(open(p)) if p.exists() else {"passed": False, "detail": f"{chk} not written"}
            detail = d.get("detail") or d.get("pooling", {}).get("detail", "")
            it["check"] = {"passed": bool(d["passed"]), "detail": detail}
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
    r = subprocess.run([sys.executable, str(HERE / "check_results.py"), out, "--write"])
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()

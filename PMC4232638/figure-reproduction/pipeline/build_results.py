"""Merge results_notes.json (written by hand: labels, sources, assumptions, causes) with the numbers of a
run into results.json, then let check_results.py compute every verdict and the summary.

Usage: build_results.py RUN_OUTPUT_DIR OUT.json [--environment ENV.json]

A notes item takes its numbers from the run:
  "fields_from": "comparison.json:table3"   values.fields from that file and key
  "fields_from": "claims.json:text.table3"  a claim's fields (expected, observed, arithmetic)
  "check_from": "package.json"              check_package.py's report
  "check_from": "af17"                      the per-combination check of Additional file 17 or 18
  "check_from": "arithmetic"                text.arithmetic: the claims recomputed from the paper's tables
  "assumptions_from": [...]                 shared assumption sets of the notes
  "cause_from": "<name>"                    a shared cause of the notes
  "expect_misses": n                        the number of fields the cause explains; the build fails when
                                            the run's misses differ, so a stale cause cannot reach the page
Every string may cite a number of the run as {name} (see facts_of); an unknown name fails the build.
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
sys.path.insert(0, str(HERE))
from check_results import field_matches  # noqa: E402

FIELD_KEYS = ("name", "expected", "observed", "tolerance", "arithmetic", "arithmetic_tolerance", "repeats")


def get(run, ref):
    f, _, key = ref.partition(":")
    d = json.load(open(Path(run) / f))
    return d[key] if key else d


def misses(fields):
    return [f["name"] for f in fields if not field_matches(f, {"printed": True})]


def facts_of(run):
    """Numbers the hand-written notes cite, taken from the run so the prose cannot drift from it."""
    c = json.load(open(Path(run) / "comparison.json"))
    cl = json.load(open(Path(run) / "claims.json"))
    a = json.load(open(Path(run) / "analysis.json"))
    facts = {}
    for k, v in c.items():
        if isinstance(v, dict) and "summary" in v and "fields" in v["summary"]:
            key = k.replace(".", "_")
            facts[f"{key}_match"] = v["summary"]["match"]
            facts[f"{key}_fields"] = v["summary"]["fields"]
            facts[f"{key}_miss"] = v["summary"]["fields"] - v["summary"]["match"]
    for k in ("af17", "af18"):
        s = c[k]["summary"]
        facts[f"{k}_means_within"] = f"{s['means_within']:,}"
        facts[f"{k}_means"] = f"{s['means']:,}"
        facts[f"{k}_intervals_within"] = f"{s['intervals_within']:,}"
        facts[f"{k}_intervals"] = f"{s['intervals']:,}"
        facts[f"{k}_control"] = f"{c[k]['control_other_set'][0]:,}"
    facts["af19_second_run"] = c["af19"]["second_run"]
    facts["af23_arith_match"] = c["af23_arithmetic"]["match"]
    r1a, r2a = a["combinations"]["all"]["run1"]["counts"], a["combinations"]["all"]["run2"]["counts"]
    pub19 = json.load(open(Path(run) / "published_values.json"))["af19"]
    d12, d1p = [], []
    for grp in ("single", "meta"):
        for k in r1a[grp]:
            for kind in ("mean", "significant"):
                for j in range(3):
                    d12.append(abs(r1a[grp][k][kind][j] - r2a[grp][k][kind][j]))
                    d1p.append(abs(r1a[grp][k][kind][j] - int(pub19[grp][k][kind][j])))
    facts["af19_run_diff_median"] = sorted(d12)[len(d12) // 2]
    facts["af19_paper_diff_median"] = sorted(d1p)[len(d1p) // 2]
    facts["af19_run_diff_max"] = max(d12)
    facts["af19_paper_diff_max"] = max(d1p)
    facts["fig4a_second_run"] = c["fig4a"]["second_run"]
    facts["fig4b_second_run"] = c["fig4b"]["second_run"]
    for k, v in c["controls"].items():
        facts[f"control_{k}"] = v
    for cid, claim in cl.items():
        for j, f in enumerate(claim["fields"]):
            if "repeats" in f:
                facts[f"rep_{cid.replace('.', '_')}_{j}"] = f["repeats"]
    r1, r2 = a["combinations"]["all"]["run1"]["counts"], a["combinations"]["all"]["run2"]["counts"]
    facts["acc_both_run2"] = r2["single"]["accuracy"]["mean"][2]
    facts["acc_sig_run2"] = r2["single"]["accuracy"]["significant"][2]
    facts["comp_both_run2"] = r2["single"]["composite"]["mean"][2]
    facts["comp_sig_run2"] = r2["single"]["composite"]["significant"][2]
    facts["acc_both_run1"] = r1["single"]["accuracy"]["mean"][2]
    facts["comp_both_run1"] = r1["single"]["composite"]["mean"][2]
    return facts


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


def arithmetic(claims, comparison, excepted):
    """The claims recomputed from the paper's own tables. Passes when every statement comes back, apart
    from those the notes list as the paper's own errors."""
    back, missed, bad = [], [], []
    for cid, c in claims.items():
        for f in c["fields"]:
            if f.get("arithmetic") is None:
                continue
            # A count recomputed from rounded printed means may move by a few at a cutoff: arithmetic_tolerance.
            g = {"expected": f["expected"], "observed": f["arithmetic"], "tolerance": f.get("arithmetic_tolerance", f.get("tolerance", {"printed": True}))}
            ok = field_matches(g, {"printed": True})
            (back if ok else missed).append(f"{cid}: {f['name']} (printed {f['expected']}, from the tables {f['arithmetic']})")
            if not ok and (cid, f["name"]) not in excepted:
                bad.append(f["name"])
    f4 = comparison["fig4_arithmetic"]
    detail = (f"{len(back)} of {len(back) + len(missed)} statements recomputed from the paper's own tables come back"
              + (". Not: " + "; ".join(missed) if missed else "")
              + f". Fig. 4 recomputed from the means printed in Additional files 17 and 18: {f4['match']} of {f4['fields']} points.")
    return not bad, detail


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
    comparison = json.load(open(Path(run) / "comparison.json"))
    claims = json.load(open(Path(run) / "claims.json"))
    for it in notes["items"]:
        it = copy.deepcopy(it)
        sets = it.pop("assumptions_from", [])
        if sets:
            it["assumptions"] = [a for s in sets for a in notes["assumption_sets"][s]] + it.get("assumptions", [])
        cause = it.pop("cause_from", None)
        if cause and "cause" not in it:
            it["cause"] = copy.deepcopy(notes["causes"][cause])
        expect = it.pop("expect_misses", None)
        src = it.pop("fields_from", None)
        if src:
            fields = [{k: f[k] for k in FIELD_KEYS if k in f} for f in get(run, src)["fields"]]
            it["values"] = {"fields": fields, "tolerance": {"printed": True}}
            if "exceptions" in it:
                it["values"]["exceptions"] = it.pop("exceptions")
            exc = {e["field"] for e in it["values"].get("exceptions", [])}
            m = [x for x in misses(fields) if x not in exc]
            if expect is not None and len(m) != expect:
                stale.append(f"{it['id']}: {len(m)} fields miss, the notes expect {expect}: {m[:5]}")
            if expect is None and m:
                stale.append(f"{it['id']}: {len(m)} fields miss and the notes give no cause: {m[:5]}")
        chk = it.pop("check_from", None)
        if chk == "package.json":
            p = Path(run) / chk
            d = json.load(open(p)) if p.exists() else {"passed": False, "detail": "package check not run"}
            it["check"] = {"passed": bool(d["passed"]), "detail": d.get("detail", "")}
        elif chk in ("af17", "af18"):
            s = comparison[chk]["summary"]
            ok = s["means_within"] == s["means"]
            it["check"] = {"passed": ok, "detail": (
                f"{s['means_within']:,} of {s['means']:,} means (11,253 combinations x 6 statistics x 2 subsets) within the printed precision "
                f"plus three Monte Carlo standard deviations; {s['intervals_within']:,} of {s['intervals']:,} interval ends within three times "
                f"the run-to-run spread. Control: our run on the other data set puts {comparison[chk]['control_other_set'][0]:,} of {s['means']:,} means within.")}
        elif chk == "arithmetic":
            excepted = {(i["id"], e["field"]) for i in notes["items"] for e in i.get("exceptions", []) if e["category"] == "paper_error"}
            passed, detail = arithmetic(claims, comparison, excepted)
            it["check"] = {"passed": passed, "detail": detail}
        res["items"].append(it)
    if stale:
        print("results_notes.json no longer matches the run:\n  " + "\n  ".join(stale), file=sys.stderr)
        sys.exit(1)
    with open(out, "w") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
        f.write("\n")
    r = subprocess.run([sys.executable, str(HERE / "check_results.py"), out, "--write", "--skip-files"])
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()

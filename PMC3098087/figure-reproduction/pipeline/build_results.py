"""Merge results_notes.json (written by hand: labels, sources, assumptions, causes) with the numbers
of a run into results.json, then let check_results.py compute every verdict and the summary.

Usage: build_results.py RUN_DIR OUT.json [--environment ENV.json]

Each notes item names where its numbers come from:
  "from": "comparison:<key>"   values.fields from output/comparison.json
  "from": "claims:<id>"        values.fields from output/claims.json (with the arithmetic check kept)
  "from": "arithmetic"         the text.arithmetic check: every claim recomputed from the paper's values
  "from": "port"               check from output/port_check.json
  "from": "package"            check from output/package.json
Rules the build applies, so a stale note cannot reach the page:
  - an item with misses and no cause fails the build; a cause given for an item without misses is dropped
    unless the note marks it "always";
  - "exceptions": "af1_plr_columns" lists as paper errors the missed Additional file 1 cells that
    the table prints identically for all nine classifiers (they are PLR's, see the cause);
  - "exceptions": "arithmetic" lists as paper errors the missed claim fields whose statement the
    paper's own figures and tables do not support either (the arithmetic value misses too).
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

KEEP = ("name", "expected", "observed", "tolerance", "z", "arithmetic", "mean_available", "replicates_na")


def matches(f):
    return field_matches(f, {"printed": True} if "tolerance" not in f else None)


def af1_identical(fields):
    """Cells of Additional file 1 whose printed value is the same for all nine classifiers."""
    by = {}
    for f in fields:
        cl, k1, nt, m = f["name"].split(" ")
        by.setdefault((k1, nt, m), set()).add(f["expected"])
    return {key for key, vals in by.items() if len(vals) == 1}


def fields_of(run, src):
    kind, _, key = src.partition(":")
    if kind == "comparison":
        d = json.load(open(Path(run) / "comparison.json"))[key]
        return [{k: f[k] for k in KEEP if k in f} for f in d["fields"]], d
    if kind == "claims":
        d = json.load(open(Path(run) / "claims.json"))[key]
        out = []
        for f in d["fields"]:
            g = {k: f[k] for k in KEEP if k in f}
            if "tolerance" not in g:
                g["tolerance"] = {"printed": True}
            if g.get("observed") is None:
                g["observed"] = "not computed"
            out.append(g)
        return out, d
    raise KeyError(src)


def arithmetic(run):
    claims = json.load(open(Path(run) / "claims.json"))
    back, missed = [], []
    for cid, c in claims.items():
        for f in c["fields"]:
            a = f.get("arithmetic")
            if a is None:
                continue
            g = {"expected": f["expected"], "observed": a, "tolerance": f.get("tolerance", {"printed": True})}
            (back if field_matches(g, None) else missed).append(f"{cid}: {f['name']} (paper says {f['expected']}, its own values give {a})")
    detail = (f"{len(back)} of {len(back) + len(missed)} statements follow from the paper's own figures and tables"
              + (". Not: " + "; ".join(missed) + "." if missed else "."))
    return {"passed": True, "detail": detail, "back": len(back), "checked": len(back) + len(missed), "missed": missed}


def main():
    args = sys.argv[1:]
    env = None
    if "--environment" in args:
        i = args.index("--environment")
        env = json.load(open(args[i + 1]))
        del args[i:i + 2]
    run, out = args
    notes = json.load(open(NOTES))
    res = {"schema": "paper2repro/results/v1", "paper": notes["paper"], "run": copy.deepcopy(notes["run"]),
           "session": notes["session"], "skill": notes["skill"], "items": []}
    if env:
        res["run"]["environment"] = env
    problems = []
    for it in notes["items"]:
        it = copy.deepcopy(it)
        sets = it.pop("assumptions_from", [])
        if sets:
            it["assumptions"] = [a for s in sets for a in notes["assumption_sets"][s]] + it.get("assumptions", [])
        cause_key = it.pop("cause_from", None)
        always = it.pop("cause_always", False)
        rule = it.pop("exceptions_rule", None)
        src = it.pop("from", None)
        if cause_key:
            it["cause"] = copy.deepcopy(notes["causes"][cause_key])
        if src == "arithmetic":
            it["check"] = {k: v for k, v in arithmetic(run).items() if k in ("passed", "detail")}
        elif src == "port":
            d = json.load(open(Path(run) / "port_check.json"))
            it["check"] = {"passed": bool(d["passed"]),
                           "detail": (f"DLDA {d['dlda_agree']} and DQDA {d['dqda_agree']} of {d['test_samples']} test-sample predictions "
                                      f"identical to sma::stat.diag.da (sma {d['sma_version']}) on {d['datasets']} simulated training sets; "
                                      f"AUC equal to Hmisc::somers2 in {d['auc_comparisons']} tries (largest difference {d['auc_max_abs_diff']:.1g}); "
                                      f"t statistics equal to t.test (largest difference {d['t_max_abs_diff']:.1g})")}
        elif src == "package":
            p = Path(run) / "package.json"
            d = json.load(open(p)) if p.exists() else {"passed": False, "detail": "package check not run"}
            it["check"] = {"passed": bool(d["passed"]), "detail": d.get("detail", "")}
        elif src:
            fields, _ = fields_of(run, src)
            it["values"] = {"fields": fields}
            missed = [f for f in fields if not matches(f)]
            exc = []
            if rule == "af1_plr_columns":
                same = af1_identical(fields)
                for f in missed:
                    cl, k1, nt, m = f["name"].split(" ")
                    if cl != "PLR" and m != "AUC" and (k1, nt, m) in same:
                        exc.append({"field": f["name"], "category": "paper_error",
                                    "evidence": "Additional file 1 prints this cell identically for all nine classifiers; the values are PLR's "
                                                "(they match the PLR curve of the paper's own Fig. 1 and Fig. 2), while Figs 1 and 2 show other values for this classifier."})
            elif rule == "arithmetic":
                for f in missed:
                    a = f.get("arithmetic")
                    if a is not None and not field_matches({"expected": f["expected"], "observed": a,
                                                            "tolerance": f.get("tolerance", {"printed": True})}, None):
                        exc.append({"field": f["name"], "category": "paper_error",
                                    "evidence": f"The paper's own figures and tables give {a} here, not {f['expected']} (output/claims.json, 'arithmetic')."})
            if exc:
                it["values"]["exceptions"] = exc
            counted_missed = [f for f in missed if f["name"] not in {e["field"] for e in exc}]
            if counted_missed and "cause" not in it:
                problems.append(f"{it['id']}: {len(counted_missed)} fields miss and the notes give no cause, e.g. {counted_missed[0]['name']}")
            if not counted_missed and not always and "cause" in it:
                del it["cause"]
        res["items"].append(it)
    if problems:
        print("results_notes.json does not explain the run:\n  " + "\n  ".join(problems), file=sys.stderr)
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
        f.write("\n")
    r = subprocess.run([sys.executable, str(HERE / "check_results.py"), out, "--write", "--skip-files"])
    sys.exit(1 if problems else r.returncode)


if __name__ == "__main__":
    main()

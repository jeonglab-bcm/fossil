"""Merge results_notes.json (written by hand: labels, sources, assumptions, causes) with the numbers
of a run into results.json, then let check_results.py compute the verdicts and the summary.

usage: build_results.py RUN_DIR OUT_JSON

Notes items take their numbers from the run folder:
  "fields_from": "comparison.json:fig2.values.epiforest"   values.fields from the comparison
  "pixels_from": "comparison.json:fig2.pixels"             the pixel scores and controls
  "claim_fields": [[name, key(, expected)], ...]           fields from comparison.json's claims:
                                                           expected "yes" (or the printed value),
                                                           observed from our run
  "check_from": "checks/bstat_null.json" | "package.json"   check.passed and a detail line
                "comparison.json:claims.paper"             the claims against the paper's values
Strings "@a+b" in assumptions or cause refer to entries of the notes' "templates". The skill block
and the session pointer travel with the notes (copied unchanged). Causes that depend on the run
are in "causes" of the notes, keyed by item id, with the condition under which they apply.
"""
import copy
import json
import platform
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTES = HERE.parent / "results_notes.json"


def dig(d, path):
    for k in path.split("."):
        d = d[k]
    return d


def from_run(run, ref):
    name, _, path = ref.partition(":")
    d = json.loads((Path(run) / name).read_text())
    return dig(d, path) if path else d


def template(notes, ref):
    out = []
    for name in ref[1:].split("+"):
        t = notes["templates"][name]
        if isinstance(t, list):
            out += copy.deepcopy(t)
        else:
            return copy.deepcopy(t)
    return out


def yn(v):
    return "yes" if v else "no"


def claim_value(v):
    if isinstance(v, bool):
        return yn(v)
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v) if not isinstance(v, (int, float)) else v


def arithmetic(paper):
    """The claims of the text, computed from the paper's own figure values."""
    bools = {k: v for k, v in paper.items() if isinstance(v, bool)}
    held = [k for k, v in bools.items() if v]
    failed = [k for k, v in bools.items() if not v]
    lo, hi = paper["fig3_medians_range"]
    med_ok = 40 <= lo and hi <= 50
    max_ok = paper["fig3_max_below_80_settings"] >= 20
    detail = (f"{len(held)} of {len(bools)} statements about Fig. 2 and the AMD study follow from the paper's own"
              " bars, Table 1 and text"
              + (f" (not: {', '.join(failed)})" if failed else "")
              + f"; Fig. 3's published medians run from {lo:g} to {hi:g} (about 45: {yn(med_ok)})"
              f" and {paper['fig3_max_below_80_settings']} of 24 maxima are below 80"
              f"; epiForest is at or above logistic regression in {paper['epiforest_at_least_lr_settings']} of 24 settings")
    return not failed and med_ok and max_ok, detail


def check(run, ref):
    if ref.startswith("comparison.json:claims.paper"):
        return arithmetic(from_run(run, ref))
    d = from_run(run, ref)
    return bool(d["passed"]), d.get("detail", "")


def r_versions():
    try:
        out = subprocess.run(["Rscript", "-e", "cat(R.version$major, R.version$minor, as.character(packageVersion('randomForest')))"],
                             capture_output=True, text=True, check=True).stdout.split()
        return {"R": f"{out[0]}.{out[1]}", "randomForest": out[2]}
    except Exception:  # noqa: BLE001
        return {}


def main():
    run, out = sys.argv[1:3]
    notes = json.loads(NOTES.read_text())
    res = {"schema": "paper2repro/results/v1"}
    for k in ("paper", "run", "session", "skill"):
        res[k] = copy.deepcopy(notes[k])
    import numpy
    import PIL
    import scipy
    res["run"]["environment"] = {"python": platform.python_version(), "numpy": numpy.__version__,
                                 "scipy": scipy.__version__, "pillow": PIL.__version__, **r_versions()}
    claims = from_run(run, "comparison.json:claims")
    items = []
    for it in notes["items"]:
        it = copy.deepcopy(it)
        if isinstance(it.get("assumptions"), str):
            it["assumptions"] = template(notes, it["assumptions"])
        if isinstance(it.get("cause"), str):
            it["cause"] = template(notes, it["cause"])
        if "fields_from" in it:
            fields = []
            for f in from_run(run, it.pop("fields_from")):
                g = {"name": f["name"], "expected": f["expected"], "observed": f["observed"]}
                if "tolerance" in f:
                    g["tolerance"] = f["tolerance"]
                fields.append(g)
            it["values"] = {"fields": fields, "tolerance": {"abs": 0}}
        if "pixels_from" in it:
            it["pixels"] = from_run(run, it.pop("pixels_from"))
        if "claim_fields" in it:
            ours = claims.get("ours") or {}
            fields = []
            for cf in it.pop("claim_fields"):
                name, key = cf[0], cf[1]
                exp = cf[2] if len(cf) > 2 else "yes"
                fields.append({"name": name, "expected": exp, "observed": claim_value(ours.get(key))})
            it["values"] = {"fields": fields, "tolerance": {"printed": True}}
        if "check_from" in it:
            passed, detail = check(run, it.pop("check_from"))
            it["check"] = {"passed": passed, "detail": detail}
        cause = notes.get("causes", {}).get(it["id"])
        if cause:
            it["cause"] = copy.deepcopy(cause)
        items.append(it)
    res["items"] = items
    Path(out).write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n")
    r = subprocess.run([sys.executable, str(HERE / "check_results.py"), out, "--write", "--skip-files"],
                       capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    sys.stderr.write(r.stderr)
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()

"""Merge results_notes.json (written by hand: labels, sources, assumptions, causes) with the numbers
of a run into results.json, then let check_results.py compute the verdicts and the summary.

  build_results.py RUN_DIR OUT.json

Notes items take their numbers from the run folder:
  "fields_from": "comparison.json:<item>"   values.fields from the comparison (with its controls)
  "check_from": "sim_check.json" | "package.json" | "comparison.json:arithmetic"
The skill block and the session pointer travel with the notes (copied unchanged).
"""

import copy
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTES = HERE.parent / "results_notes.json"


def check_detail(run, src):
    f, _, key = src.partition(":")
    d = json.load(open(Path(run) / f))
    if f == "sim_check.json":
        reps = d["replicates"]
        same = [r for r in reps if not r["differences"]]
        return d["passed"], (f"{len(same)} of {len(reps)} reruns from scratch equal the committed results: "
                             + "; ".join(f"{r['study']} replicate {r['rep']} ({r['rows']} rows)" for r in reps))
    if f == "package.json":
        return d["passed"], d.get("detail", "")
    if key == "arithmetic":
        a = d["arithmetic"]
        detail = (f"{a['back']} of {a['checked']} claim fields come back when computed from the paper's own "
                  f"figure values")
        if a["not_back"]:
            detail += (f"; the {len(a['not_back'])} that do not are where the text contradicts its own figures "
                       "(listed in comparison.json, arithmetic.not_back)")
        return True, detail
    raise KeyError(src)


def main(run, out):
    notes = json.load(open(NOTES))
    comp = json.load(open(Path(run) / "comparison.json"))
    res = {"schema": "paper2repro/results/v1", "paper": notes["paper"], "run": notes["run"],
           "session": notes.get("session", {"ledger": "session/ledger.json"}), "skill": notes["skill"],
           "items": []}
    for it in notes["items"]:
        it = copy.deepcopy(it)
        src = it.pop("fields_from", None)
        if src:
            _, _, key = src.partition(":")
            c = comp["items"][key]
            it.setdefault("values", {})["fields"] = copy.deepcopy(c["fields"])
            if c.get("exceptions"):
                it["values"]["exceptions"] = copy.deepcopy(c["exceptions"])
            extra = {k: c[k] for k in ("controls", "bias_relative_to_own_truth", "anomalies", "unmatched_bars")
                     if k in c}
            if extra:
                it["comparison"] = extra
        chk = it.pop("check_from", None)
        if chk:
            passed, detail = check_detail(run, chk)
            it["check"] = {"passed": bool(passed), "detail": detail}
        res["items"].append(it)
    json.dump(res, open(out, "w"), indent=1)
    r = subprocess.run([sys.executable, str(HERE / "check_results.py"), out, "--write", "--skip-files"])
    sys.exit(r.returncode)


if __name__ == "__main__":
    main(*sys.argv[1:3])

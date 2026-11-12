"""Merge results_notes.json (written by hand: labels, sources, assumptions, causes) with the numbers
of a run into results.json, then let check_results.py compute the verdicts and the summary.

  build_results.py RUN_DIR OUT.json

A notes item with "from": KEY takes its values (or check) from comparison.json[KEY]; "package"
takes its check from package.json. "exceptions" in a notes item go into values.exceptions. The
skill block and the session pointer travel with the notes (copied unchanged).
"""

import copy
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTES = HERE.parent / "results_notes.json"


def main(run, out):
    run = Path(run)
    notes = json.load(open(NOTES))
    comp = json.load(open(run / "comparison.json"))
    res = {"schema": "paper2repro/results/v1", "paper": notes["paper"], "run": notes["run"],
           "session": notes.get("session", {"ledger": "session/ledger.json"}), "skill": notes["skill"], "items": []}
    for it in notes["items"]:
        it = copy.deepcopy(it)
        key = it.pop("from", None)
        exc = it.pop("exceptions", None)
        if key == "package":
            pk = json.load(open(run / "package.json"))
            it["check"] = {"passed": bool(pk.get("passed")), "detail": pk.get("detail", "")}
        elif key:
            c = comp[key]
            if "values" in c:
                it["values"] = copy.deepcopy(c["values"])
                if exc:
                    it["values"]["exceptions"] = exc
                if c.get("extra_points"):
                    it["extra_points"] = c["extra_points"]
            else:
                it["check"] = {"passed": bool(c["check"]["passed"]), "detail": c["check"]["detail"]}
        res["items"].append(it)
    json.dump(res, open(out, "w"), indent=1)
    r = subprocess.run([sys.executable, str(HERE / "check_results.py"), out, "--write", "--skip-files"])
    sys.exit(r.returncode)


if __name__ == "__main__":
    main(*sys.argv[1:3])

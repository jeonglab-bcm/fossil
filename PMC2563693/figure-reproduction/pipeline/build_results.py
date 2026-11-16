"""Merge results_notes.json (written by hand: labels, sources, tolerances, assumptions, causes) with
the numbers of a run into results.json, then let check_results.py compute verdicts and the summary.

  build_results.py RUN_DIR FIGURES_DIR OUT.json

FIGURES_DIR is render.py's output; its outputs.json names each figure item's render and overlay.

A notes item takes its numbers from the run folder:
  "fields_from": "<id>"            values.fields = comparison.json[<id>].fields
  "check_from": "text.arithmetic"  check.passed and a detail line from comparison.json
  "check_from": "cv_check.json"    the repeats rerun from scratch against the committed full run
  "check_from": "package.json"     the package check (check_package.py --json)
The skill block and the session pointer travel with the notes, copied unchanged.
"""

import copy
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTES = HERE.parent / "results_notes.json"


def check_detail(run, name):
    if name == "text.arithmetic":
        a = json.loads((run / "comparison.json").read_text())["text.arithmetic"]
        held = [c for c in a["checks"] if c["holds"]]
        return a["passed"], f"{len(held)} of {len(a['checks'])} checks on the paper's own numbers hold: " + "; ".join(
            c["claim"] for c in a["checks"])
    d = json.loads((run / name).read_text())
    if name == "cv_check.json":
        return d["passed"], (f"{len(d['checked'])} cross-validation repeats rerun from scratch equal the committed "
                             f"full run" if d["passed"] else f"{len(d['differences'])} differences, e.g. {d['differences'][:2]}")
    return d["passed"], d.get("detail", "")


def main(run, figures, out):
    run, figures = Path(run), Path(figures)
    notes = json.loads(NOTES.read_text())
    comp = json.loads((run / "comparison.json").read_text())
    outputs = json.loads((figures / "outputs.json").read_text())
    items = []
    for n in notes["items"]:
        it = copy.deepcopy(n)
        src = it.pop("fields_from", None)
        if src:
            it.setdefault("values", {})["fields"] = comp[src]["fields"]
        chk = it.pop("check_from", None)
        if chk:
            passed, detail = check_detail(run, chk)
            it["check"] = {"passed": bool(passed), "detail": detail}
        if it["id"] in outputs and "outputs" not in it:
            it["outputs"] = outputs[it["id"]]
        if it["kind"] == "figure" and it["method"] != "none" and not it.get("outputs"):
            raise SystemExit(f"{it['id']}: an attempted figure needs its render and overlay (render.py outputs.json)")
        items.append(it)
    doc = {k: notes[k] for k in ("schema", "paper", "run", "session", "skill")}
    doc["items"] = items
    Path(out).write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    subprocess.run([sys.executable, str(HERE / "check_results.py"), out, "--write"], check=False)


if __name__ == "__main__":
    main(*sys.argv[1:4])

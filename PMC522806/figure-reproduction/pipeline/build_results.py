"""Merge results_notes.json (written by hand) with comparison.json (computed) into results.json.

  build_results.py NOTES COMPARISON OUT_JSON [--package PACKAGE_JSON] [--inputs fetch_inputs.sh]
                   [--env ENV_JSON] [--date YYYY-MM-DD]

Each item takes its label, source, assumptions and cause from the notes, and its method, values,
check and outputs from the comparison. The skill and session blocks are copied from the notes
unchanged. check_results.py --write then computes the verdicts and the summary.
"""
import argparse
import json
import re
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("notes")
ap.add_argument("comparison")
ap.add_argument("out")
ap.add_argument("--package")
ap.add_argument("--inputs")
ap.add_argument("--env")
ap.add_argument("--date")
a = ap.parse_args()

notes = json.loads(Path(a.notes).read_text())
comp = json.loads(Path(a.comparison).read_text())["items"]
shared = notes.get("shared_assumptions", {})
items = []
for n in notes["items"]:
    it = {k: n[k] for k in ("id", "label", "kind", "source") if k in n}
    c = comp.get(n["id"], {})
    method = n.get("method") or c.get("method") or "none"
    if n["id"] == "package":
        method = "check"
        if a.package and Path(a.package).exists():
            p = json.loads(Path(a.package).read_text())
            it["check"] = {"passed": bool(p.get("passed")), "detail": p.get("detail", "")}
        else:
            it["check"] = {"passed": False, "detail": "check_package.py report missing"}
    it["method"] = method
    if method != "none":
        for key in ("values", "check"):
            if key in c:
                it[key] = dict(c[key])
    if "exceptions" in n and "values" in it:
        it["values"]["exceptions"] = n["exceptions"]
    assumptions = [shared[r] for r in n.get("assumptions_ref", [])] + n.get("assumptions", [])
    if assumptions:
        it["assumptions"] = assumptions
    for key in ("cause", "note"):
        if key in n:
            it[key] = n[key]
    outs = n.get("outputs") or c.get("outputs")
    if outs:
        it["outputs"] = outs
    items.append(it)

run = dict(notes["run"])
if a.date:
    run["date"] = a.date
if a.inputs:
    sh = Path(a.inputs).read_text()
    base = re.search(r"^u=(\S+)", sh, re.M).group(1)
    run["inputs"] = [{"name": m.group(1), "url": m.group(3).replace("$u", base), "sha256": m.group(2)}
                     for m in re.finditer(r"^fetch (\S+) ([0-9a-f]{64}) (\S+)", sh, re.M)]
if a.env and Path(a.env).exists():
    run["environment"] = json.loads(Path(a.env).read_text())
doc = {"schema": "paper2repro/results/v1", "paper": notes["paper"], "run": run, "session": notes["session"],
       "skill": notes["skill"], "items": items}
Path(a.out).write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
print(f"{len(items)} items")

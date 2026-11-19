#!/usr/bin/env python3
"""Merge results_notes.json (written by hand) with comparison.json (computed) into results.json.

  build_results.py NOTES COMPARISON OUT_JSON [--package PACKAGE_JSON] [--inputs FETCH_SCRIPT]
                   [--env ENV_JSON] [--date YYYY-MM-DD]

Each item takes its label, kind, source, assumptions and cause from the notes, and its method,
values, pixels, check and outputs from the comparison. The skill and session blocks are copied
from the notes unchanged. check_results.py --write then computes the verdicts and the summary.
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

notes = json.load(open(a.notes))
comp = json.load(open(a.comparison))["items"]
shared = notes.get("shared_assumptions", {})
items = []
for n in notes["items"]:
    it = {k: n[k] for k in ("id", "label", "kind", "source") if k in n}
    c = comp.get(n["id"], {})
    method = n.get("method") or c.get("method") or "none"
    if n["id"] == "package":
        method = "check"
        p = json.load(open(a.package)) if a.package and Path(a.package).exists() else {}
        it["check"] = {"passed": bool(p.get("passed")), "detail": p.get("detail", "package check report missing")}
    it["method"] = method
    if method != "none":
        for key in ("values", "check", "pixels"):
            if key in c:
                it[key] = c[key]
    if "exceptions" in n and "values" in it:
        it["values"]["exceptions"] = n["exceptions"]
    assumptions = [shared[r] for r in n.get("assumptions_ref", [])] + n.get("assumptions", [])
    if assumptions:
        it["assumptions"] = assumptions
    for k in ("cause", "note"):
        if k in n:
            it[k] = n[k]
    outs = n.get("outputs") or c.get("outputs")
    if outs:
        it["outputs"] = outs
    items.append(it)
missing = set(comp) - {n["id"] for n in notes["items"]}
if missing:
    raise SystemExit(f"comparison items without notes: {sorted(missing)}")

run = dict(notes["run"])
if a.date:
    run["date"] = a.date
if a.inputs and Path(a.inputs).exists():
    sh = Path(a.inputs).read_text()
    var = dict(re.findall(r"^(\w+)=(https://\S+)$", sh, re.M))
    block = sh.split("<<LIST\n", 1)[1].split("\nLIST", 1)[0]
    inputs = []
    for line in block.splitlines():
        parts = line.split()
        if len(parts) >= 3:
            url = re.sub(r"\$(\w+)", lambda v: var.get(v.group(1), v.group(0)), parts[2])
            inputs.append({"name": parts[0], "url": url, "sha256": parts[1]})
    run["inputs"] = inputs
if a.env and Path(a.env).exists():
    run["environment"] = json.load(open(a.env))
doc = {"schema": "paper2repro/results/v1", "paper": notes["paper"], "run": run, "session": notes["session"],
       "skill": notes["skill"], "items": items}
Path(a.out).write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
print(f"{len(items)} items")

"""Merge results_notes.json (written by hand) with comparison.json (computed) into results.json.

  build_results.py NOTES COMPARISON OUT_JSON [--package PACKAGE_JSON] [--inputs INPUTS_JSON] [--env ENV_JSON]

Each item takes its label, source, assumptions and cause from the notes, and its method, values,
pixels, check and outputs from the comparison. The skill and session blocks are copied from the
notes unchanged. check_results.py --write then computes the verdicts and the summary.
"""
import argparse
import json
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("notes")
ap.add_argument("comparison")
ap.add_argument("out")
ap.add_argument("--package")
ap.add_argument("--inputs", help="fetch_inputs.sh, parsed for names, URLs and SHA-256")
ap.add_argument("--env")
ap.add_argument("--date", default=None)
a = ap.parse_args()

notes = json.load(open(a.notes))
comp = json.load(open(a.comparison))["items"]
shared = notes.get("shared_assumptions", {})
items = []
for n in notes["items"]:
    it = {k: n[k] for k in ("id", "label", "kind", "source") if k in n}
    c = comp.get(n["id"], {})
    method = n.get("method") or c.get("method")
    if n["id"] == "package":
        method = "check"
        if a.package and Path(a.package).exists():
            p = json.load(open(a.package))
            it["check"] = {"passed": bool(p.get("passed")), "detail": p.get("detail", "")}
        else:
            it["check"] = {"passed": False, "detail": "check_package.py report missing"}
    it["method"] = method
    for key in ("values", "pixels", "check"):
        if key in c and method != "none":
            it[key] = {k: v for k, v in c[key].items() if k in ("fields", "tolerance", "exceptions", "passed", "detail",
                                                              "tolerance_px", "dpi", "published_near_ours",
                                                              "ours_near_published", "threshold", "controls")}
    if "exceptions" in n and "values" in it:
        it["values"]["exceptions"] = n["exceptions"]
    assumptions = [shared[r] for r in n.get("assumptions_ref", [])] + n.get("assumptions", [])
    if assumptions:
        it["assumptions"] = assumptions
    if "cause" in n:
        it["cause"] = n["cause"]
    if "note" in n:
        it["note"] = n["note"]
    outs = n.get("outputs") or c.get("outputs")
    if outs:
        it["outputs"] = outs
    items.append(it)

run = dict(notes["run"])
if a.date:
    run["date"] = a.date
if a.inputs and Path(a.inputs).exists():
    import re
    sh = Path(a.inputs).read_text()
    inputs = []
    for m in re.finditer(r"^fetch (\S+) ([0-9a-f]{64}) \\?\n?\s*\"?([^\s\"]+)", sh, re.M):
        inputs.append({"name": m.group(1).strip('"'), "url": m.group(3), "sha256": m.group(2)})
    for m in re.finditer(r"^fetch (\S+) ([0-9a-f]{64}) \\\n\s+(\S+)", sh, re.M):
        pass
    heredoc = re.search(r"<<'EOF'\n(.*?)\nEOF", sh, re.S)
    if heredoc:
        for line in heredoc.group(1).splitlines():
            name, sha = line.split()
            inputs.append({"name": f"{name}.zip", "url": f"https://s3-us-west-2.amazonaws.com/sgd-archive.yeastgenome.org/expression/microarray/{name}/{name}.zip", "sha256": sha})
    sub = {"$sgd": "https://s3-us-west-2.amazonaws.com/sgd-archive.yeastgenome.org", "$go": "https://s3.amazonaws.com/go-data-product-release/2004-03-01", "$g": "S288C_reference_genome_R64-1-1_20110203.tgz"}
    for i in inputs:
        for k, v in sub.items():
            i["url"] = i["url"].replace(k, v)
        i["name"] = i["name"].replace("$g", sub["$g"])
    run["inputs"] = inputs
if a.env and Path(a.env).exists():
    run["environment"] = json.load(open(a.env))
doc = {"schema": "paper2repro/results/v1", "paper": notes["paper"], "run": run, "session": notes["session"],
       "skill": notes["skill"], "items": items}
Path(a.out).write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
print(f"{len(items)} items")

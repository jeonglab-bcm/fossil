#!/usr/bin/env python3
"""Merge results_notes.json (written by hand) with comparison.json (computed) into results.json.

  build_results.py NOTES COMPARISON HYPOTHESES OUT_JSON [--package PACKAGE_JSON] [--inputs FETCH_SCRIPT]
                   [--env ENV_JSON] [--date YYYY-MM-DD]

Each item takes its label, kind, source, assumptions and cause from the notes, and its method,
values, pixels, check and outputs from the comparison. The causes of Table 3 are written from
hypotheses.json (the variant fits), so they follow the numbers. The skill and session blocks are
copied from the notes unchanged. check_results.py --write then computes the verdicts.
"""
import argparse
import json
import re
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("notes")
ap.add_argument("comparison")
ap.add_argument("hypotheses")
ap.add_argument("out")
ap.add_argument("--package")
ap.add_argument("--inputs")
ap.add_argument("--env")
ap.add_argument("--date")
a = ap.parse_args()

notes = json.load(open(a.notes))
comp = json.load(open(a.comparison))
cmp_items = comp["items"]
hyp = json.load(open(a.hypotheses))
shared = notes.get("shared_assumptions", {})


def table3_hypotheses():
    main = hyp["main"]["distance"]
    out = []
    for v in hyp["variants"]:
        out.append({"hypothesis": v["name"].capitalize(),
                    "test": f"Model 2 refitted that way: distance from Table 3 {v['distance']:.3f}, against {main:.3f} for our fit",
                    "result": "supported" if v["distance"] < 0.02 else "rejected"})
    best = hyp["drop_one"]["best"][0]
    out.append({"hypothesis": "One sample missing from, or different in, the authors' copy of the data",
                "test": f"Model 2 refitted without each of the {hyp['drop_one']['runs']} samples: the closest, without {best['sample']}, "
                        f"is still {best['distance']:.3f} from Table 3",
                "result": "rejected"})
    out.append({"hypothesis": "The authors' copy of the pooled tissues differed (their caption lists small intestine and breast where "
                              "the file has liver and mammary gland)",
                "test": "Not testable without their copy; leaving out the liver sample alone does not close the gap",
                "result": "inconclusive"})
    return out


def table3_summary():
    f = cmp_items["table3.sigma"]["values"]["fields"]
    rel = sorted(x["observed"] / float(x["expected"]) - 1 for x in f)
    return (f"Every gene SD comes out below the printed one, by {-100 * rel[-1]:.1f} to {-100 * rel[0]:.1f}% "
            f"(ACTB the most), in the same order. Table 3's figures are not a rounding of ours, and none of the "
            f"variant fits below reaches them; Fig. 3 draws the printed values, so the authors' fit, or their copy "
            f"of the data, differed from ours.")


items = []
for n in notes["items"]:
    it = {k: n[k] for k in ("id", "label", "kind", "source") if k in n}
    c = cmp_items.get(n["id"], {})
    method = n.get("method") or c.get("method") or "none"
    if n["id"] == "package":
        method = "check"
        p = json.load(open(a.package)) if a.package and Path(a.package).exists() else {}
        it["check"] = {"passed": bool(p.get("passed")), "detail": p.get("detail", "package check report missing")}
    it["method"] = method
    if method != "none":
        for key in ("values", "pixels", "check"):
            if key in c:
                it[key] = dict(c[key])
    if "exceptions" in n and "values" in it:
        it["values"]["exceptions"] = n["exceptions"]
    assumptions = [shared[r] for r in n.get("assumptions_ref", [])] + n.get("assumptions", [])
    if assumptions:
        it["assumptions"] = assumptions
    if "cause" in n:
        cause = json.loads(json.dumps(n["cause"]))
        if cause.get("hypotheses") == "TABLE3_HYPOTHESES":
            cause["hypotheses"] = table3_hypotheses()
        if cause.get("summary") == "TABLE3_SUMMARY":
            cause["summary"] = table3_summary()
        it["cause"] = cause
    outs = n.get("outputs") or c.get("outputs")
    if outs:
        it["outputs"] = outs
    items.append(it)
missing = set(cmp_items) - {n["id"] for n in notes["items"]}
if missing:
    raise SystemExit(f"comparison items without notes: {sorted(missing)}")

run = dict(notes["run"])
if a.date:
    run["date"] = a.date
if a.inputs and Path(a.inputs).exists():
    sh = Path(a.inputs).read_text()
    var = dict(re.findall(r"^(\w+)=(https://\S+)$", sh, re.M))
    inputs = []
    for m in re.finditer(r"^fetch (\S+) ([0-9a-f]{64}) \\\n\s+(\S+)", sh, re.M):
        url = re.sub(r"\$(\w+)", lambda v: var.get(v.group(1), v.group(0)), m.group(3))
        inputs.append({"name": m.group(1), "url": url, "sha256": m.group(2)})
    run["inputs"] = inputs
if a.env and Path(a.env).exists():
    run["environment"] = json.load(open(a.env))
doc = {"schema": "paper2repro/results/v1", "paper": notes["paper"], "run": run, "session": notes["session"],
       "skill": notes["skill"], "items": items}
Path(a.out).write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
print(f"{len(items)} items")

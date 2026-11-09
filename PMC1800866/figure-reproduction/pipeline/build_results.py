#!/usr/bin/env python3
"""Merge results_notes.json (written by hand) with the numbers of a run into results.json, then let
check_results.py compute the verdicts and the summary.

In the notes, a value field gives ``"observed_from": "FILE:PATH"`` and a pixel item gives
``"pixels_from": "FILE:PATH"``; FILE is relative to the run folder and PATH is a dotted path into
its JSON (list items by index). ``"observed_map"`` turns an observed number into a string such as
"yes"/"no" by a comparison: {"op": ">", "than_from": "FILE:PATH"} or {"op": ">", "than": 0.5}.
A check item gives ``"check_from"`` for its ``passed`` and ``detail``.

Usage: build_results.py RUN_DIR OUT_JSON
"""
import copy
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTES = HERE.parent / "results_notes.json"


def lookup(run, ref):
    f, _, path = ref.partition(":")
    obj = json.load(open(Path(run) / f))
    parts = path.split(".") if path else []
    i = 0
    while i < len(parts):
        if isinstance(obj, list):
            if "=" in parts[i]:  # key=value picks the list item whose key equals value
                k, v = parts[i].split("=", 1)
                obj = next(x for x in obj if str(x.get(k)) == v)
            else:
                obj = obj[int(parts[i])]
            i += 1
            continue
        # keys may contain dots ("fig3.a", "CHDE Zn3.area"): take the longest key that exists
        for j in range(len(parts), i, -1):
            key = ".".join(parts[i:j])
            if key in obj:
                obj = obj[key]
                i = j
                break
        else:
            raise KeyError(f"{ref}: no key {parts[i]!r}")
    return obj


def compare(a, op, b):
    return {">": a > b, ">=": a >= b, "<": a < b, "==": a == b}[op]


def observed(run, field):
    v = lookup(run, field["observed_from"])
    m = field.get("observed_map")
    if m:
        than = lookup(run, m["than_from"]) if "than_from" in m else m["than"]
        if "plus_from" in m:
            than = than + sum(lookup(run, r) for r in m["plus_from"])
        if "minus_from" in m:
            v = v - lookup(run, m["minus_from"])
        return m.get("true", "yes") if compare(v, m["op"], than) else m.get("false", "no")
    rnd = field.get("round")
    if rnd is not None and isinstance(v, (int, float)):
        v = round(v, rnd)
    return v


def main(run, out):
    notes = json.load(open(NOTES))
    res = {"schema": "paper2repro/results/v1", "paper": notes["paper"], "run": notes["run"],
           "session": {"ledger": "session/ledger.json"}, "items": []}
    for it in notes["items"]:
        it = copy.deepcopy(it)
        if "values" in it:
            for f in it["values"]["fields"]:
                if "observed_from" in f:
                    f["observed"] = observed(run, f)
                    for k in ("observed_from", "observed_map", "round"):
                        f.pop(k, None)
        if "pixels_from" in it:
            p = lookup(run, it.pop("pixels_from"))
            thr = it["pixels"]["threshold"]
            it["pixels"] = {k: p[k] for k in ("tolerance_px", "dpi", "published_near_ours", "ours_near_published", "controls")}
            it["pixels"]["threshold"] = thr
        if "check_from" in it:
            c = lookup(run, it.pop("check_from"))
            it["check"] = {"passed": bool(c["passed"]), "detail": c["detail"]}
        res["items"].append(it)
    Path(out).write_text(json.dumps(res, indent=1) + "\n")
    root = HERE.parent.parent  # the paper folder, for the outputs' paths
    rc = subprocess.run([sys.executable, str(HERE / "check_results.py"), out, "--write", "--root", str(root), "--skip-files"]).returncode
    sys.exit(rc)


if __name__ == "__main__":
    main(*sys.argv[1:3])

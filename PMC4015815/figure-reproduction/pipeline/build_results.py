"""Merge the pipeline's numbers with the hand-written notes into results.json.

usage: build_results.py RUN_DIR NOTES_JSON OUT_JSON

NOTES_JSON (results_notes.json) holds what a person writes: the paper block, inputs, labels,
sources, assumptions, causes, pass marks, and for each measured value where the pipeline writes
it ("from": [file, "dotted.path"]). Every number in results.json comes from RUN_DIR. Verdicts and
the summary are left to check_results.py --write.

Pointers inside a note item:
  "pixels_from": [file, path]   an object with ours {published_near_ours, ours_near_published}
                                 (or a cell share under "cells_within_24") and controls
  fields[i].observed_from       [file, path] for a values field; "{:.3f}"-style "format" optional
  check.passed_from             [file, path, op, value]: passed = (value at path) op value
  detail_template               str.format(**{name: value}) with "detail_from": {name: [file, path]}
"""
import csv
import json
import operator
import os
import sys

OPS = {">=": operator.ge, "<=": operator.le, "==": operator.eq, ">": operator.gt, "<": operator.lt}


def load(run, name):
    p = os.path.join(run, name)
    if name.endswith(".csv"):
        return list(csv.DictReader(open(p)))
    return json.load(open(p))


def get(obj, path):
    for part in path.split(".") if path else []:
        if isinstance(obj, list):
            obj = obj[int(part)]
        else:
            obj = obj[part]
    return obj


def resolve(run, spec, cache):
    f, path = spec[0], spec[1]
    if f not in cache:
        cache[f] = load(run, f)
    return get(cache[f], path)


def build_item(run, note, cache):
    item = {k: v for k, v in note.items() if not k.endswith("_from") and k not in
            ("detail_template",)}
    if "pixels_from" in note:
        src = resolve(run, note["pixels_from"], cache)
        ours = src["ours"]
        if "bar_ends_within_2px" in ours:
            a = b = ours["bar_ends_within_2px"]
            ctrl = [{"name": c["name"], "kind": c["kind"], "score": c["score"]}
                    for c in src["controls"]]
        elif "cells_within_24" in ours:
            a = b = ours["cells_within_24"]
            ctrl = [{"name": c["name"], "kind": c["kind"], "score": c["cells_within_24"]}
                    for c in src["controls"]]
        else:
            a, b = ours["published_near_ours"], ours["ours_near_published"]
            ctrl = [{"name": c["name"], "kind": c["kind"], "score": c["score"]}
                    for c in src["controls"]]
        item["pixels"] = {**note.get("pixels", {}), "published_near_ours": a,
                          "ours_near_published": b, "controls": ctrl}
    if "values" in note:
        fields = []
        for f in note["values"]["fields"]:
            f = dict(f)
            if "observed_from" in f:
                v = resolve(run, f.pop("observed_from"), cache)
                fmt = f.pop("format", None)
                f["observed"] = fmt.format(v) if fmt else v
            fields.append(f)
        item["values"] = {**note["values"], "fields": fields}
    if "check" in note:
        c = dict(note["check"])
        if "passed_from" in c:
            spec = c.pop("passed_from")
            c["passed"] = bool(OPS[spec[2]](resolve(run, spec[:2], cache), spec[3]))
        if "detail_template" in note:
            vals = {k: resolve(run, s, cache) for k, s in note.get("detail_from", {}).items()}
            c["detail"] = note["detail_template"].format(**vals)
        item["check"] = c
    item.pop("detail_from", None)
    return item


def main(run, notes_path, out):
    notes = json.load(open(notes_path))
    cache = {}
    res = {k: v for k, v in notes.items() if k != "items"}
    res["items"] = [build_item(run, n, cache) for n in notes["items"]]
    json.dump(res, open(out, "w"), indent=2, ensure_ascii=False)
    print(f"{len(res['items'])} items written to {out}")


if __name__ == "__main__":
    main(*sys.argv[1:4])

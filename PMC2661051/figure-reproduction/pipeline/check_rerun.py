#!/usr/bin/env python3
"""Check that rerun replicates and gene sets equal the committed ones.

  check_rerun.py FRESH_SIM_DIR COMMITTED_SIM_DIR FRESH_REAL_DIR COMMITTED_REAL_DIR OUT_JSON

Every rep_*.csv in the fresh simulation folder must equal the committed file of the same name, and
every row of the fresh p53.csv and hedenfalk.csv (a subset of the sets, by index) must equal the
committed row: p-values within 1e-9 (they are counts out of 1000, or parametric p-values).
"""
import csv
import json
import sys
from pathlib import Path

fs, cs, fr, cr, out = map(Path, sys.argv[1:6])
problems, checked = [], {"replicates": 0, "sets": 0}


def same(a, b):
    try:
        return abs(float(a) - float(b)) <= 1e-9
    except ValueError:
        return a == b


for f in sorted(fs.glob("rep_*.csv")):
    new = list(csv.DictReader(open(f)))
    old = list(csv.DictReader(open(cs / f.name)))
    checked["replicates"] += 1
    for a, b in zip(new, old):
        for k in a:
            if not same(a[k], b.get(k)):
                problems.append(f"{f.name} {a['set']} {k}: fresh {a[k]} committed {b.get(k)}")
    if len(new) != len(old):
        problems.append(f"{f.name}: {len(new)} rows against {len(old)}")
for name in ("p53.csv", "hedenfalk.csv"):
    if not (fr / name).exists():
        continue
    old = {r["index"]: r for r in csv.DictReader(open(cr / name))}
    for a in csv.DictReader(open(fr / name)):
        b = old.get(a["index"])
        checked["sets"] += 1
        if b is None:
            problems.append(f"{name}: set {a['index']} not committed")
            continue
        for k in a:
            if not same(a[k], b.get(k)):
                problems.append(f"{name} {a['set']} {k}: fresh {a[k]} committed {b.get(k)}")
res = {"passed": not problems, "checked": checked, "problems": problems[:50]}
Path(out).write_text(json.dumps(res, indent=1) + "\n")
print(f"rerun check: {checked['replicates']} replicates, {checked['sets']} gene sets; "
      + ("all equal" if not problems else f"{len(problems)} differences"))
for p in problems[:20]:
    print("  " + p)
sys.exit(0 if not problems else 1)

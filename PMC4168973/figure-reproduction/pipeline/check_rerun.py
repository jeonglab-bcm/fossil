"""Check the default (CI) run's reruns against the committed outputs.

  check_rerun.py PDS_RERUN_DIR COMMITTED_OUTPUT_DIR LAMBDA_CHECK_JSON OUT_JSON

The pathway scores rerun for a few pathways of each data set must equal the committed scores
(within 1e-8), and the recomputed cross-validation runs of each model must equal the committed
penalties (models.R checks them and writes lambda_check.json).
"""
import csv
import json
import sys
from pathlib import Path

rerun, committed, lam, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
problems, checked = [], {"pathway_scores": 0, "cv_models": 0}
for f in sorted(rerun.glob("*.csv")):
    old = {r["pathway"]: r for r in csv.DictReader(open(committed / "pds" / f.name))}
    for r in csv.DictReader(open(f)):
        o = old.get(r["pathway"])
        if o is None:
            problems.append(f"{f.name}: {r['pathway']} not in the committed scores")
            continue
        bad = [k for k in r if k not in ("pathway", "flipped") and abs(float(r[k]) - float(o[k])) > 1e-8]
        if bad or r["flipped"] != o["flipped"]:
            problems.append(f"{f.name}: {r['pathway']} differs in {len(bad)} samples")
        checked["pathway_scores"] += 1
lc = json.load(open(lam))
for k, v in lc.items():
    checked["cv_models"] += 1
    if not v.get("equal"):
        problems.append(f"cross-validation runs of {k} differ from the committed penalties")
res = {"passed": not problems and all(checked.values()), "checked": checked, "problems": problems}
out.write_text(json.dumps(res, indent=1) + "\n")
print(json.dumps(res))

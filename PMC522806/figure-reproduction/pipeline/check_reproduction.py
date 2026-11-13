"""Check a fresh run against the committed reproduction.

  check_reproduction.py FRESH_DIR COMMITTED_OUTPUT_DIR PAPER_DIR OUT_JSON

1. check_results.py on the fresh results.json: rules hold and verdicts are current.
2. Pass marks: every item's verdict and measure in the fresh results.json equal the committed
   PAPER_DIR/results.json (a score that crosses a pass mark or a control changes the verdict).
3. compare_runs.py: every committed output file equals the fresh one (numbers within 1e-9, images
   by decoded pixels, confidences within 2e-6); package.json (timings) and README.md are left out.
Exits 1 if any check fails.
"""
import json
import subprocess
import sys
from pathlib import Path

fresh, committed, paper, out = map(Path, sys.argv[1:5])
here = Path(__file__).resolve().parent
report = {}

r = subprocess.run([sys.executable, here / "check_results.py", fresh / "results.json", "--root", paper],
                   capture_output=True, text=True)
report["check_results"] = {"passed": r.returncode == 0, "output": (r.stdout + r.stderr).strip().splitlines()[-30:]}

new = json.load(open(fresh / "results.json"))
old = json.load(open(paper / "results.json"))
changed = []
oi = {i["id"]: i for i in old["items"]}
for it in new["items"]:
    o = oi.get(it["id"])
    if o is None or o.get("verdict") != it.get("verdict"):
        changed.append({"id": it["id"], "committed": o and o.get("verdict"), "fresh": it.get("verdict")})
for k in set(oi) - {i["id"] for i in new["items"]}:
    changed.append({"id": k, "committed": oi[k].get("verdict"), "fresh": None})
same_items = json.dumps([{k: v for k, v in i.items()} for i in new["items"]], sort_keys=True) == \
    json.dumps([{k: v for k, v in i.items()} for i in old["items"]], sort_keys=True)
report["pass_marks"] = {"passed": not changed and new.get("summary") == old.get("summary"), "changed": changed,
                        "items_identical": same_items}

# Confidences are stored to 6 decimals; a last-digit rounding flip between machines is allowed
# (--atol 2e-6). Predicted classes and correct counts are integers and must be equal.
r = subprocess.run([sys.executable, here / "compare_runs.py", fresh, committed, "--atol", "2e-6", "--ignore", "package.json",
                    "README.md"],
                   capture_output=True, text=True)
report["compare_runs"] = {"passed": r.returncode == 0, "output": r.stdout.strip().splitlines()[-40:]}

ok = all(v["passed"] for v in report.values())
report["passed"] = ok
Path(out).write_text(json.dumps(report, indent=1) + "\n")
for k, v in report.items():
    if isinstance(v, dict):
        print(f"{'ok  ' if v['passed'] else 'FAIL'} {k}")
        if not v["passed"]:
            print("\n".join(v.get("output", [])[-20:]) if "output" in v else json.dumps(v, indent=1))
sys.exit(0 if ok else 1)

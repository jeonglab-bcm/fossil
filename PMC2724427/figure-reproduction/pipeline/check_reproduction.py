"""Check a fresh run against the committed reproduction.

  check_reproduction.py FRESH_DIR COMMITTED_OUTPUT_DIR PAPER_DIR OUT_JSON

1. check_results.py on the fresh results.json: rules hold and verdicts are current.
2. Pass marks: every item's verdict and measure in the fresh results.json equal the committed
   PAPER_DIR/results.json (a score that crosses a pass mark or a control changes the verdict).
3. compare_runs.py: every committed output file equals the fresh one (numbers within 1e-9, images
   by decoded pixels); package.json, results.json and README.md are left out.
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

# Numbers within rtol 1e-9 (the CSVs hold 15 significant digits); images by decoded pixels.
# package.json is left out (its detail line is checked through results.json) and so is
# results.json (its run date changes; its items are compared above).
r = subprocess.run([sys.executable, here / "compare_runs.py", fresh, committed, "--ignore", "package.json",
                    "results.json", "README.md", "*/fig*_ours.png", "*/fig*_overlay.png"],
                   capture_output=True, text=True)
report["compare_runs"] = {"passed": r.returncode == 0, "output": r.stdout.strip().splitlines()[-40:]}

# The renders: titles and axis text are drawn with the machine's fonts, whose antialiasing differs
# between machines with the same R and fonts package. The scored part of each render is the inside
# of the published panel boxes (compare.py); there every pixel must be equal.
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

axes = json.load(open(here.parent / "published" / "axes.json"))
diffs = []
for fig in ("1", "2", "3"):
    boxes = [p["box"] for p in axes[f"figure-{fig}"]["panels"]]
    for sub, name in (("figs", f"fig{fig}_ours.png"), ("cmp", f"fig{fig}_overlay.png")):
        a = np.asarray(Image.open(fresh / sub / name).convert("RGB")).astype(int)
        b = np.asarray(Image.open(committed / sub / name).convert("RGB")).astype(int)
        n = sum(int((np.abs(a[y0 + 1:y1, x0 + 1:x1] - b[y0 + 1:y1, x0 + 1:x1]).max(axis=2) > 0).sum())
                for x0, x1, y0, y1 in boxes) if a.shape == b.shape else -1
        diffs.append(f"{sub}/{name}: {'same inside the panel boxes' if n == 0 else f'{n} pixels differ inside the panel boxes' if n > 0 else 'size differs'}")
report["renders"] = {"passed": all("same" in d for d in diffs), "output": diffs}

ok = all(v["passed"] for v in report.values())
report["passed"] = ok
Path(out).write_text(json.dumps(report, indent=1) + "\n")
for k, v in report.items():
    if isinstance(v, dict):
        print(f"{'ok  ' if v['passed'] else 'FAIL'} {k}")
        if not v["passed"]:
            print("\n".join(v.get("output", [])[-20:]) if "output" in v else json.dumps(v, indent=1))
sys.exit(0 if ok else 1)

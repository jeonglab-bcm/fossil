"""Check a fresh run against the committed reproduction, and write report.md.

Usage: check_reproduction.py RUN_DIR PAPER_DIR OUT_JSON REPORT_MD

1. check_results.py on the fresh results.json: rules hold and verdicts are current.
2. The fresh results.json has the same items, verdicts and summary as the committed PAPER_DIR/results.json
   (a score that crosses a pass mark or a control changes a verdict and fails here).
3. compare_runs.py: every committed file under figure-reproduction/output equals the fresh one (numbers
   within 1e-9, images by decoded pixels); package.json (timings) is left out.
4. The fresh results page equals the committed site/PMC3392844/index.html (text, and embedded images as pixels).
Exits 1 if any check fails.
"""
import json
import subprocess
import sys
from pathlib import Path

run, paper, out, report_md = map(Path, sys.argv[1:5])
paper = paper.resolve()  # main.nf passes figure-reproduction/..; its name must be the paper ID
here = Path(__file__).resolve().parent
site = paper.parent / "site" / paper.name
report = {}

r = subprocess.run([sys.executable, here / "check_results.py", run / "results.json", "--root", paper, "--markdown"],
                   capture_output=True, text=True)
report["check_results"] = {"passed": r.returncode == 0, "output": (r.stdout + r.stderr).strip().splitlines()}

new = json.load(open(run / "results.json"))
old = json.load(open(paper / "results.json"))
oi = {i["id"]: i for i in old["items"]}
changed = [{"id": i["id"], "committed": (oi.get(i["id"]) or {}).get("verdict"), "fresh": i.get("verdict")}
           for i in new["items"] if (oi.get(i["id"]) or {}).get("verdict") != i.get("verdict")]
changed += [{"id": k, "committed": v.get("verdict"), "fresh": None} for k, v in oi.items() if k not in {i["id"] for i in new["items"]}]
report["verdicts"] = {"passed": not changed and new.get("summary") == old.get("summary"), "changed": changed}

r = subprocess.run([sys.executable, here / "compare_runs.py", run / "output", paper / "figure-reproduction" / "output",
                    "--ignore", "package.json"], capture_output=True, text=True)
report["compare_runs"] = {"passed": r.returncode == 0, "output": r.stdout.strip().splitlines()}

r = subprocess.run([sys.executable, here / "compare_runs.py", run / "site", site], capture_output=True, text=True)
report["page"] = {"passed": r.returncode == 0 and (site / "index.html").exists(), "output": r.stdout.strip().splitlines()}

# The repository's results-check file (figure-reproduction/results.json) is what the run writes.
committed_rc = json.load(open(paper / "figure-reproduction" / "results.json"))
fresh_rc = json.load(open(run / "results_check.json"))
report["results_check"] = {"passed": committed_rc == fresh_rc,
                           "output": [f"figure-reproduction/results.json: {len(committed_rc['results'])} entries, "
                                      f"{'the same as' if committed_rc == fresh_rc else 'DIFFERENT from'} the run's"]}

ok = all(v["passed"] for v in report.values())
report["passed"] = ok
Path(out).write_text(json.dumps(report, indent=1) + "\n")
md = ["# PMC3392844 reproduction check", "", f"**{'Passed' if ok else 'FAILED'}.**", "",
      "## Results (check_results.py)", ""] + report["check_results"]["output"] + [
      "", "## Verdicts against the committed results.json", "",
      "Same items, verdicts and summary." if report["verdicts"]["passed"] else "```\n" + json.dumps(report["verdicts"]["changed"], indent=1) + "\n```",
      "", "## Fresh run against the committed outputs (compare_runs.py)", ""] + report["compare_runs"]["output"] + [
      "", "## Results page", ""] + report["page"]["output"] + [
      "", "## Results check file", ""] + report["results_check"]["output"]
Path(report_md).write_text("\n".join(md) + "\n")
for k, v in report.items():
    if isinstance(v, dict):
        print(f"{'ok  ' if v['passed'] else 'FAIL'} {k}")
        if not v["passed"]:
            print("\n".join(v.get("output", [])[-25:]) if "output" in v else json.dumps(v, indent=1))
sys.exit(0 if ok else 1)

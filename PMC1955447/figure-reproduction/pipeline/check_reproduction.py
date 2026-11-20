"""Check a fresh run against the committed reproduction, and write report.md.

Usage: check_reproduction.py RUN_DIR PAPER_DIR OUT_JSON REPORT_MD [--full]

1. check_results.py on the fresh results.json: rules hold and verdicts are current.
2. The fresh results.json has the same items, verdicts and summary as the committed PAPER_DIR/results.json.
3. compare_runs.py: every committed file under figure-reproduction/output equals the fresh one (numbers within
   1e-9). Left out: package.json (timings), crosscheck.json and sim_check.json (their differences of nearly equal
   log-likelihoods move in the last digits between processors; each has its own pass mark, which results.json
   carries). With --full the per-replicate records are fresh too; they are compared through the summaries.
4. The default run's sim_check.json passed: the first replicates of every cell, rerun from scratch, equal the
   committed records.
5. The fresh results page equals the committed site/PMC1955447/index.html.
6. The repository's results-check file (figure-reproduction/results.json) is what the run writes.
Exits 1 if any check fails.
"""
import json
import subprocess
import sys
from pathlib import Path

args = [a for a in sys.argv[1:] if a != "--full"]
full = "--full" in sys.argv
run, paper, out, report_md = map(Path, args[:4])
paper = paper.resolve()
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

ignore = ["package.json", "crosscheck.json", "sim_check.json"] + (["records/*.csv.gz"] if full else [])
r = subprocess.run([sys.executable, here / "compare_runs.py", run / "output", paper / "figure-reproduction" / "output",
                    "--ignore", *ignore], capture_output=True, text=True)
report["compare_runs"] = {"passed": r.returncode == 0, "output": r.stdout.strip().splitlines()}

sc = run / "output" / "sim_check.json"
if full:
    report["sim_check"] = {"passed": True, "output": ["--full: every replicate was rerun; the check of the first ones is not needed"]}
else:
    d = json.load(open(sc)) if sc.exists() else {"passed": False, "detail": "sim_check.json not written"}
    report["sim_check"] = {"passed": bool(d["passed"]), "output": [d["detail"]]}

r = subprocess.run([sys.executable, here / "compare_runs.py", run / "site", site], capture_output=True, text=True)
report["page"] = {"passed": r.returncode == 0 and (site / "index.html").exists(), "output": r.stdout.strip().splitlines()}

committed_rc = json.load(open(paper / "figure-reproduction" / "results.json"))
fresh_rc = json.load(open(run / "results_check.json"))
report["results_check"] = {"passed": committed_rc == fresh_rc,
                           "output": [f"figure-reproduction/results.json: {len(committed_rc['results'])} entries, "
                                      f"{'the same as' if committed_rc == fresh_rc else 'DIFFERENT from'} the run's"]}

ok = all(v["passed"] for v in report.values())
report["passed"] = ok
Path(out).write_text(json.dumps(report, indent=1) + "\n")
md = ["# PMC1955447 reproduction check", "", f"**{'Passed' if ok else 'FAILED'}.**", "",
      "## Results (check_results.py)", ""] + report["check_results"]["output"] + [
      "", "## Verdicts against the committed results.json", "",
      "Same items, verdicts and summary." if report["verdicts"]["passed"] else "```\n" + json.dumps(report["verdicts"]["changed"], indent=1) + "\n```",
      "", "## Replicates rerun from scratch (sim_check.py)", ""] + report["sim_check"]["output"] + [
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

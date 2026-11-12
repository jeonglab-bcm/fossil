"""The pipeline's check step.

usage: check_reproduction.py RESULTS_JSON RUN_OUTPUT COMMITTED_OUTPUT REPORT_MD

Fails (exit 1) when
* check_results.py finds a broken rule or a stale verdict in results.json;
* an expected output is missing;
* the cross-validation repeats rerun from scratch (cv_check.json) differ from the committed full run;
* the package check failed;
* the fresh run differs from the committed outputs (compare_runs.py: numbers to 1e-9 relative,
  images by decoded pixels).
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPECTED = ["comparison.json", "cv_summary.json", "fig2.json", "robustness.json", "hypotheses.json", "digitized.json",
            "published_vector.json", "datasets.json", "figure4.json", "cv_check.json", "package.json"] + [
            f"figures/{f}_{k}.png" for f in ("fig2", "fig3", "fig4", "figS1", "figS2", "figS3", "figS5", "fig_s4")
            for k in ("ours", "overlay")]
# package.json holds timings and temporary paths (its pass/fail is in results.json, which is compared);
# cv_check.json is this run's own record; cv/ holds the committed full run, an input of this one.
IGNORE = ["package.json", "cv_check.json", "report.md", "cv/*", "cv/*/*"]


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def main():
    results, rundir, committed, report = sys.argv[1:5]
    rundir = Path(rundir)
    lines = ["# PMC2563693 reproduction check", ""]
    ok = True
    rc, out = run([sys.executable, str(HERE / "check_results.py"), results, "--markdown", "--skip-files"])
    lines += ["## results.json", "", out.strip(), ""]
    ok &= rc == 0
    missing = [e for e in EXPECTED if not (rundir / e).exists()]
    if missing:
        ok = False
        lines += ["## Missing outputs", ""] + [f"- {m}" for m in missing] + [""]
    cv = json.loads((rundir / "cv_check.json").read_text()) if (rundir / "cv_check.json").exists() else {"passed": False}
    lines += ["## Cross-validation repeats rerun from scratch", "",
              f"{len(cv.get('checked', []))} repeats rerun; {len(cv.get('differences', []))} differences from the committed full run.", ""]
    ok &= bool(cv["passed"])
    pk = json.loads((rundir / "package.json").read_text()) if (rundir / "package.json").exists() else {"passed": False}
    lines += ["## Package", "", pk.get("detail", "no report"), ""]
    ok &= bool(pk.get("passed"))
    rc, out = run([sys.executable, str(HERE / "compare_runs.py"), str(rundir), committed, "--ignore", *IGNORE])
    lines += ["## Fresh run against the committed outputs", "", out.strip(), ""]
    ok &= rc == 0
    lines.append("**PASS**" if ok else "**FAIL**")
    Path(report).write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

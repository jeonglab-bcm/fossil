"""The pipeline's check step.

usage: check_reproduction.py RESULTS_JSON RUN_DIR COMMITTED_OUTPUT REPORT_MD PAPER_DIR

Fails (exit 1) when
* check_results.py finds a broken rule or a stale verdict in results.json;
* the fresh run differs from the committed outputs (compare_runs.py: numbers to a relative 1e-6,
  images by decoded pixels);
* an expected output is missing;
* the package check failed.
Writes REPORT_MD with both tables.
"""

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPECTED = [
    "results.json", "analysis.json", "published_values.json", "comparison.json", "package.json",
    "figures/fig2a_ours.png", "figures/fig2a_overlay.png",
    "figures/fig2b_ours.png", "figures/fig2b_overlay.png",
    "figures/fig3_ours.png", "figures/fig3_overlay.png",
    "figures/fig4_ours.png", "figures/fig4_overlay.png",
]
# package.json holds timings and temporary paths; its pass or fail travels in results.json, which
# is compared. studies.json only runs with --studies.
IGNORE = ["package.json", "report.md", "studies.json", "site/*", "alignments/*"]


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def main() -> int:
    results, rundir, committed, report, paper = sys.argv[1:6]
    rundir, committed = Path(rundir), Path(committed)
    failures, parts = [], []

    missing = [name for name in EXPECTED if not (rundir / name).exists()]
    if missing:
        failures.append(f"missing outputs: {', '.join(missing)}")

    code, out = run([sys.executable, str(HERE / "check_results.py"), results, "--markdown",
                     "--root", str(Path(paper).resolve())])
    parts.append("## What came back\n\n" + out)
    if code:
        failures.append("check_results.py failed")

    pkg = rundir / "package.json"
    if pkg.exists():
        report_json = json.loads(pkg.read_text())
        if not report_json.get("passed"):
            failures.append("the package check failed: " + str(report_json.get("detail", "")))

    if committed.exists():
        cmd = [sys.executable, str(HERE / "compare_runs.py"), str(rundir), str(committed),
               "--ignore", *IGNORE]
        code, out = run(cmd)
        parts.append("## This run against the committed outputs\n\n" + out)
        if code:
            failures.append("the fresh run differs from the committed outputs")
    else:
        parts.append(f"## This run against the committed outputs\n\nNo committed outputs at {committed}.")

    text = "# PMC2813257\n\n" + "\n\n".join(parts)
    if failures:
        text += "\n\n## Failures\n\n" + "\n".join(f"* {f}" for f in failures) + "\n"
    Path(report).write_text(text)
    print(text)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

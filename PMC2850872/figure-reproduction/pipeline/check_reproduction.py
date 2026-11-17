"""The check step: results.json valid and current, the fresh run equal to the committed outputs.

Usage: check_reproduction.py RUNDIR COMMITTED_OUTPUT RESULTS_JSON REPORT.md

Fails (exit 1) when check_results.py finds a broken rule or a stale verdict, when the fresh run
differs from the committed outputs, or when the package check failed.
"""

import json
import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[3] / "tools" / "paper2repro"


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def main(rundir, committed, results, report):
    rundir = Path(rundir)
    lines = ["# PMC2850872 reproduction check", ""]
    ok = True
    code, out = run([sys.executable, str(TOOLS / "check_results.py"), results, "--root",
                     str(Path(results).parent), "--markdown"])
    lines += ["## results.json", "", out.strip(), ""]
    ok &= code == 0
    # package.json holds timings and temporary paths; it is checked by its own `passed` flag.
    code, out = run([sys.executable, str(TOOLS / "compare_runs.py"), str(rundir), committed,
                     "--atol", "2e-6", "--ignore", "package.json", "results.json", "hypotheses.json", "report.md", "site/*"])
    lines += ["## Fresh run against the committed outputs", "", out.strip(), ""]
    ok &= code == 0
    fresh = json.loads((rundir / "results.json").read_text())
    same = fresh == json.loads(Path(results).read_text())
    lines += ["## results.json of this run against the committed one", "",
              "identical" if same else "**differs**: rerun with the new outputs and commit results.json", ""]
    ok &= same
    pkg = json.loads((rundir / "package.json").read_text())
    lines += ["## Package", "", ("passed: " if pkg.get("passed") else "FAILED: ") + pkg.get("detail", ""), ""]
    ok &= bool(pkg.get("passed"))
    lines.append("All checks passed." if ok else "**Some checks failed.**")
    Path(report).write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main(*sys.argv[1:5])

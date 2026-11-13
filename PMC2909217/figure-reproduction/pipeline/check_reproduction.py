"""The pipeline's check step.

usage: check_reproduction.py RESULTS_JSON RUN_DIR COMMITTED_OUTPUT COMMITTED_RESULTS REPORT_MD

Fails (exit 1) when
* check_results.py finds a broken rule or a stale verdict in the fresh results.json;
* an expected output is missing;
* the package check failed;
* the fresh run differs from the committed outputs (compare_runs.py: numbers to 1e-6 relative,
  images by decoded pixels), or the fresh results.json from the committed one.
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPECTED = ["counts.json", "network.json", "roc.json", "table1.json", "densities.json", "hypotheses.json",
            "comparison.json", "claims.json", "page.json", "package.json",
            *[f"figures/fig{n}_{k}.png" for n in (2, 3, 4, 5, 6) for k in ("ours", "overlay")]]
# package.json holds timings and temporary paths (its pass/fail is in results.json, which is compared).
IGNORE = ["package.json", "report.md"]


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def main():
    results, rundir, committed, committed_results, report = sys.argv[1:6]
    rundir = Path(rundir)
    lines = ["# PMC2909217 reproduction check", ""]
    ok = True

    rc, out = run([sys.executable, str(HERE / "check_results.py"), results, "--markdown", "--skip-files"])
    lines += ["## results.json", "", out.strip(), ""]
    ok &= rc == 0

    missing = [e for e in EXPECTED if not (rundir / e).exists()]
    if missing:
        ok = False
        lines += ["## Missing outputs", ""] + [f"- {m}" for m in missing] + [""]

    pk = json.loads((rundir / "package.json").read_text()) if (rundir / "package.json").exists() else {"passed": False}
    lines += ["## Package", "", pk.get("detail", "no report"), ""]
    ok &= bool(pk.get("passed"))

    rc, out = run([sys.executable, str(HERE / "compare_runs.py"), str(rundir), committed,
                   "--rtol", "1e-6", "--atol", "1e-9", "--ignore", *IGNORE])
    lines += ["## Fresh run against the committed outputs", "", out.strip(), ""]
    ok &= rc == 0

    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
        shutil.copy(results, Path(a) / "results.json")
        if Path(committed_results).exists():
            shutil.copy(committed_results, Path(b) / "results.json")
        rc, out = run([sys.executable, str(HERE / "compare_runs.py"), a, b, "--rtol", "1e-6", "--atol", "1e-9"])
        if not Path(committed_results).exists():
            rc, out = 1, "no committed results.json"
    lines += ["## Fresh results.json against the committed one", "", out.strip(), ""]
    ok &= rc == 0

    lines.append("**PASS**" if ok else "**FAIL**")
    Path(report).write_text("\n".join(lines) + "\n")
    print("\n".join(lines[-3:]))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

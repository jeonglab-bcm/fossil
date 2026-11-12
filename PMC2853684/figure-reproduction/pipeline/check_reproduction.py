"""The pipeline's check step.

usage: check_reproduction.py RESULTS_JSON RUN_DIR COMMITTED_OUTPUT REPORT_MD

Fails (exit 1) when check_results.py finds a broken rule or a stale verdict in results.json, when
an expected output is missing, when the package check failed, or when the fresh run differs from
the committed outputs (compare_runs.py: numbers to 1e-6 relative, images by decoded pixels).
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIGS = ["fig2a", "fig2b", "fig3", "fig4a", "fig4b", "figS1", "figS2"]
EXPECTED = ["published_values.json", "analysis.json", "consensus.json", "comparison.json", "package.json",
            "mcl/mcl_HPRD_I2.0.txt", "mcl/mcl_OPHID_I2.0.txt"] + \
           [f"figures/{f}_{k}.png" for f in FIGS for k in ("ours", "overlay")]
# package.json holds timings and temporary paths (its result is in results.json, which is compared);
# the MCL logs hold timings; mcl_version.txt is the version banner, which Ubuntu's build of MCL
# 14-137 prints differently from bioconda's (the clusters are identical).
IGNORE = ["package.json", "report.md", "mcl/*.log", "mcl/mcl_version.txt", "site/*"]


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def main():
    results, rundir, committed, report = sys.argv[1:5]
    rundir = Path(rundir)
    lines = ["# PMC2853684 reproduction check", ""]
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
    rc, out = run([sys.executable, str(HERE / "compare_runs.py"), str(rundir), committed, "--ignore", *IGNORE])
    lines += ["## Fresh run against the committed outputs", "", out.strip(), ""]
    ok &= rc == 0
    lines.append("**PASS**" if ok else "**FAIL**")
    Path(report).write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

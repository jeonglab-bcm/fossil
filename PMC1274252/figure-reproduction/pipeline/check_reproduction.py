"""The pipeline's check step.

usage: check_reproduction.py RESULTS_JSON RUN_DIR COMMITTED_OUTPUT REPORT_MD [--quick]

Fails (exit 1) when
* check_results.py finds a broken rule or a stale verdict in results.json;
* the port does not reproduce Weka 3.4.3 (the port item in results.json);
* the fresh run differs from the committed outputs (compare_runs.py: numbers to 1e-6 relative,
  images by decoded pixels);
* the package check failed or an expected output is missing.
With --quick the 10- and 20-rule cross-validations were skipped, so analysis.json and results.json
lack those numbers; the comparison is then reported, not enforced.
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIGS = [f"figures/fig1{p}_{k}.png" for p in "abcdef" for k in ("ours", "overlay")] + \
       [f"figures/fig3{p}_{k}.png" for p in "abc" for k in ("ours", "overlay")] + \
       ["figures/fig1_ours.png", "figures/fig2_ours.png", "figures/fig2_overlay.png", "figures/fig3_ours.png"]
EXPECTED = ["analysis.json", "figures.json", "package.json", "checks/weka_versions.json"] + FIGS
# package.json holds timings and temporary paths (its pass/fail is in results.json, which is compared)
IGNORE = ["package.json", "report.md"]


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def main():
    results, rundir, committed, report = sys.argv[1:5]
    quick = "--quick" in sys.argv
    rundir = Path(rundir)
    lines = ["# PMC1274252 reproduction check", ""]
    ok = True

    rc, out = run([sys.executable, str(HERE / "check_results.py"), results, "--markdown", "--skip-files"])
    lines += ["## results.json", "", out.strip(), ""]
    ok &= rc == 0

    missing = [e for e in EXPECTED if not (rundir / e).exists()]
    if missing:
        ok = False
        lines += ["## Missing outputs", ""] + [f"- {m}" for m in missing] + [""]

    R = json.loads(Path(results).read_text())
    port = next(i for i in R["items"] if i["id"] == "port")
    lines += ["## Port against Weka 3.4.3", "", port["check"]["detail"], ""]
    ok &= bool(port["check"]["passed"])

    pk = json.loads((rundir / "package.json").read_text()) if (rundir / "package.json").exists() else {"passed": False}
    lines += ["## Package", "", pk.get("detail", "no report"), ""]
    ok &= bool(pk.get("passed"))

    fresh = rundir.parent / "fresh"
    fresh.mkdir(exist_ok=True)
    for p in rundir.rglob("*"):
        if p.is_file():
            dst = fresh / p.relative_to(rundir)
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(p.read_bytes())
    (fresh / "results.json").write_bytes(Path(results).read_bytes())
    cmd = [sys.executable, str(HERE / "compare_runs.py"), str(fresh), committed, "--ignore", *IGNORE]
    rc, out = run(cmd)
    lines += ["## Fresh run against the committed outputs", "", out.strip(), ""]
    if not quick:
        ok &= rc == 0

    lines.append("**PASS**" if ok else "**FAIL**")
    Path(report).write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

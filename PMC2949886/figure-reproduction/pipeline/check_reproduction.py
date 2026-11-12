"""The pipeline's check step.

usage: check_reproduction.py RESULTS_JSON RUN_DIR COMMITTED_OUTPUT REPORT_MD [--full]

Fails (exit 1) when
* check_results.py finds a broken rule or a stale verdict in results.json;
* the data sets rerun from scratch (sim_check.json) differ from the committed chunk;
* the fresh run differs from the committed outputs (compare_runs.py: numbers to 1e-6 relative,
  images by decoded pixels);
* the package check failed or an expected output is missing.
With --full every data set was simulated again and there is no sim_check.json; the comparison with
the committed outputs is then enforced as well (same code and seeds).
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIGS = ["fig1", "fig2", "fig3", "fig4", "fig5", "fig6", "fig7", "figS2", "figS3", "figS4", "figS5", "figS6",
        "figS8", "figS9"]
EXPECTED = (["published_values.json", "comparison.json", "package.json", "fig1.json", "leukemia.json",
             "one_sd0.1.json", "one_sd0.01.json", "one_sd0.json", "sim_sd0.1.json", "sim_sd0.01.json",
             "sim_pi0.7.json"]
            + [f"figures/{f}_{k}.png" for f in FIGS for k in ("ours", "overlay")])
# package.json holds the R version line (its pass/fail is in results.json, which is compared);
# sim_check.json is this run's own record.
IGNORE = ["package.json", "sim_check.json", "report.md"]


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def main():
    results, rundir, committed, report = sys.argv[1:5]
    full = "--full" in sys.argv
    rundir = Path(rundir)
    lines = ["# PMC2949886 reproduction check", ""]
    ok = True

    rc, out = run([sys.executable, str(HERE / "check_results.py"), results, "--markdown", "--skip-files"])
    lines += ["## results.json", "", out.strip(), ""]
    ok &= rc == 0

    missing = [e for e in EXPECTED if not (rundir / e).exists()]
    if missing:
        ok = False
        lines += ["## Missing outputs", ""] + [f"- {m}" for m in missing] + [""]

    if not full:
        sc = json.loads((rundir / "sim_check.json").read_text()) if (rundir / "sim_check.json").exists() \
            else {"passed": False, "files": []}
        lines += ["## Simulated data sets 1-50 rerun from scratch", "", "| File | Rows | Same as committed |",
                  "| --- | --- | --- |"]
        for f in sc["files"]:
            lines.append(f"| {f['file']} | {f['rows']} | {'yes' if not f['n_differences'] else 'no: ' + '; '.join(f['differences'][:3])} |")
        lines.append("")
        ok &= bool(sc["passed"])

    pk = json.loads((rundir / "package.json").read_text()) if (rundir / "package.json").exists() else {"passed": False}
    lines += ["## Package", "", pk.get("detail", "no report"), ""]
    ok &= bool(pk.get("passed"))

    rc, out = run([sys.executable, str(HERE / "compare_runs.py"), str(rundir), committed, "--rtol", "1e-6",
                   "--atol", "1e-9", "--ignore", *IGNORE])
    lines += ["## Fresh run against the committed outputs", "", out.strip(), ""]
    ok &= rc == 0

    lines.append("**PASS**" if ok else "**FAIL**")
    Path(report).write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

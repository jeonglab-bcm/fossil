"""The pipeline's check step.

usage: check_reproduction.py RESULTS_JSON RUN_DIR COMMITTED_OUTPUT REPORT_MD [--full]

Fails (exit 1) when
* check_results.py finds a broken rule or a stale verdict in results.json;
* the replicates rerun from scratch (sim_check.json) differ from the committed per-replicate results;
* the fresh run differs from the committed outputs (compare_runs.py: numbers to 1e-6 relative,
  images by decoded pixels);
* the package check failed or an expected output is missing.
With --full every replicate was simulated again; the comparison with the committed outputs is then
reported, not enforced.
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPECTED = ["published_values.json", "targets.json", "summary.json", "comparison.json", "sim_check.json",
            "truth_variants.json", "hypotheses.json", "package.json"] + [
    f"figures/fig{n}_{k}.png" for n in range(1, 9) for k in ("ours", "overlay", "published")]
# package.json and sim_check.json are this run's own records (their pass/fail is in results.json,
# which is compared); report.md and results.json are compared through check_results.py.
# pooling_check.csv comes from pipeline/pooling_check.R, run by hand (about 2.5 CPU hours), not from main.nf
IGNORE = ["package.json", "sim_check.json", "report.md", "results.json", "sim/*", "sim/*/*", "site/*",
          "pooling_check.csv"]


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def main():
    results, rundir, committed, report = sys.argv[1:5]
    full = "--full" in sys.argv
    rundir = Path(rundir)
    lines = ["# PMC2824146 reproduction check", ""]
    ok = True

    rc, out = run([sys.executable, str(HERE / "check_results.py"), results, "--markdown", "--skip-files"])
    lines += ["## results.json", "", out.strip(), ""]
    ok &= rc == 0

    missing = [e for e in EXPECTED if not (rundir / e).exists()]
    if missing:
        ok = False
        lines += ["## Missing outputs", ""] + [f"- {m}" for m in missing] + [""]

    sc = json.loads((rundir / "sim_check.json").read_text()) if (rundir / "sim_check.json").exists() \
        else {"passed": False, "replicates": []}
    lines += ["## Replicates rerun from scratch", "", "| Study | Replicate | Rows | Same as committed |",
              "| --- | --- | --- | --- |"]
    for r in sc["replicates"]:
        same = "yes" if not r["differences"] else "no: " + "; ".join(r["differences"][:3])
        lines.append(f"| {r['study']} | {r['rep']} | {r['rows']} | {same} |")
    lines.append("")
    ok &= bool(sc["passed"])

    pk = json.loads((rundir / "package.json").read_text()) if (rundir / "package.json").exists() else {"passed": False}
    lines += ["## Package", "", pk.get("detail", "no report"), ""]
    ok &= bool(pk.get("passed"))

    rc, out = run([sys.executable, str(HERE / "compare_runs.py"), str(rundir), committed, "--ignore", *IGNORE])
    lines += ["## Fresh run against the committed outputs", "", out.strip(), ""]
    if not full:
        ok &= rc == 0

    lines.append("**PASS**" if ok else "**FAIL**")
    Path(report).write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

"""The pipeline's check step.

usage: check_reproduction.py RESULTS_JSON RUN_DIR COMMITTED_OUTPUT REPORT_MD [--full]

Fails (exit 1) when
* check_results.py finds a broken rule or a stale verdict in results.json;
* the replicates rerun from scratch (sim_check.json) differ from the committed per-replicate
  statistics;
* the fresh run differs from the committed outputs (compare_runs.py: numbers to 1e-6 relative,
  images by decoded pixels);
* the package check failed or an expected output is missing.
With --full every replicate was simulated again; the comparison with the committed outputs is then
reported, not enforced (the full run is the same code, so it should still match).
"""
import subprocess
import sys
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
EXPECTED = ["published_values.json", "table1.json", "summary.json", "comparison.json", "sim_check.json",
            "figures/fig1_ours.png", "figures/fig1_overlay.png", "figures/fig2_ours.png", "figures/fig2_overlay.png",
            "figures/fig3_ours.png", "figures/fig3_overlay.png", "figures/fig4_ours.png", "figures/fig4_overlay.png",
            "figures/fig5_ours.png", "figures/fig5_overlay.png", "figures/fig6_ours.png", "figures/fig6_overlay.png",
            "checks/port_check.json", "checks/haplo_check.json", "package.json"]
# package.json holds timings and temporary paths (its pass/fail is in results.json, which is compared);
# sim_check.json is this run's own record. The committed checks/ are copied in unless --port_check.
IGNORE = ["package.json", "sim_check.json", "checks/*"]


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def main():
    results, rundir, committed, report = sys.argv[1:5]
    full = "--full" in sys.argv
    rundir = Path(rundir)
    lines = ["# PMC2666661 reproduction check", ""]
    ok = True

    rc, out = run([sys.executable, str(HERE / "check_results.py"), results, "--markdown", "--skip-files"])
    lines += ["## results.json", "", out.strip(), ""]
    ok &= rc == 0

    missing = [e for e in EXPECTED if not (rundir / e).exists()]
    if missing:
        ok = False
        lines += ["## Missing outputs", ""] + [f"- {m}" for m in missing] + [""]

    sc = json.loads((rundir / "sim_check.json").read_text()) if (rundir / "sim_check.json").exists() else {"passed": False, "replicates": []}
    lines += ["## Replicates rerun from scratch", "", "| Study | Replicate | Same as committed |", "| --- | --- | --- |"]
    for r in sc["replicates"]:
        where = r.get("ld_model") or f"r2 = {r.get('r2')}"
        lines.append(f"| {r['study']} | {where}, #{r['rep']} | {'yes' if not r['differences'] else 'no: ' + '; '.join(r['differences'][:3])} |")
    lines.append("")
    ok &= bool(sc["passed"])

    pk = json.loads((rundir / "package.json").read_text()) if (rundir / "package.json").exists() else {"passed": False}
    lines += ["## Package", "", pk.get("detail", "no report"), ""]
    ok &= bool(pk.get("passed"))

    cmd = [sys.executable, str(HERE / "compare_runs.py"), str(rundir), committed, "--ignore", *IGNORE]
    rc, out = run(cmd)
    lines += ["## Fresh run against the committed outputs", "", out.strip(), ""]
    if not full:
        ok &= rc == 0

    lines.append("**PASS**" if ok else "**FAIL**")
    Path(report).write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

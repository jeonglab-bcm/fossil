"""The check step: results.json must pass, and the fresh run must equal the committed outputs.

usage: check_reproduction.py RUN_DIR COMMITTED_OUTPUT_DIR REPORT_MD

Fails (exit 1) when check_results.py finds a broken rule or a stale verdict, when an expected
output is missing, or when compare_runs.py finds a difference between this run and the
committed output/ (numbers within tolerance, images by decoded pixels).
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXPECTED = ["results.json", "tables.json", "sweep_dr.csv", "sweep_dt.csv", "port_check.json",
            "figures_check.json", "fig3_ours.png", "fig3_overlay.png", "fig3_scores.json",
            "fig4_ours.png", "fig4_overlay.png", "fig4_scores.json", "fig5_ours.png",
            "fig5_overlay.png", "fig5_scores.json", "weights_dr_2.5.1.3.json",
            "weights_dt_2.5.1.3.json"]


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def main(run_dir, committed, report):
    lines, ok = ["# PMC4015815 reproduction check", ""], True
    missing = [f for f in EXPECTED if not os.path.exists(os.path.join(run_dir, f))]
    if missing:
        ok = False
        lines += [f"Missing outputs: {', '.join(missing)}", ""]
    rc, out = run([sys.executable, os.path.join(HERE, "check_results.py"),
                   os.path.join(run_dir, "results.json"), "--markdown", "--skip-files"])
    ok &= rc == 0
    lines += ["## results.json", "", out.strip(), ""]
    rc, out = run([sys.executable, os.path.join(HERE, "compare_runs.py"), run_dir, committed, "--pixel-tol", "1",
                   "--ignore", "site/*", "report.md", "compare/*", "causes/*", "top1_stats.json",
                   "top1_nrdb90_i3.fasta.gz"])
    ok &= rc == 0
    lines += ["## This run against the committed output/", "", out.strip(), ""]
    lines.append("Check passed." if ok else "Check FAILED.")
    open(report, "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main(*sys.argv[1:4])

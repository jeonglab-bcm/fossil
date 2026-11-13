"""The pipeline's check step.

usage: check_reproduction.py RESULTS_JSON RUN_DIR COMMITTED_OUTPUT REPORT_MD [--timing]

Fails (exit 1) when
* check_results.py finds a broken rule or a stale verdict in results.json;
* the fresh run differs from the committed outputs (compare_runs.py: numbers to 1e-6 relative, images
  by decoded pixels); with --timing the re-measured run times (timing.json, fig5.json and the Fig. 5
  renders) are reported, not enforced, because they depend on the machine;
* the package check failed or an expected output is missing.
"""
import json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPECTED = ["dream.json", "datasets.json", "profiles.json", "fig4.json", "fig5.json", "enrich.json", "claims.json",
            "table3.json", "normalisation.json", "port_check.json", "timing.json", "package.json", "results.json"] + \
           [f"figures/fig{n}_{k}.png" for n in (2, 3, 4, 5, 7) for k in ("ours", "overlay")] + ["figures/fig4_run.png"] + \
           [f"dream/D{i}.tsv" for i in range(1, 14)]
IGNORE = ["package.json", "report.md", "site/*", "results.json"]
TIMING = ["timing.json", "fig5.json", "figures/fig5_ours.png", "figures/fig5_overlay.png", "claims.json"]


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def main():
    results, rundir, committed, report = sys.argv[1:5]
    timing = "--timing" in sys.argv
    rundir = Path(rundir)
    lines, ok = ["# PMC4110735 reproduction check", ""], True
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
    ign = IGNORE + (TIMING if timing else [])
    rc, out = run([sys.executable, str(HERE / "compare_runs.py"), str(rundir), committed, "--ignore", *ign])
    lines += ["## Fresh run against the committed outputs", "", out.strip(), ""]
    ok &= rc == 0
    if timing:
        lines += ["Run times were measured again (--timing); they are not compared with the committed ones.", ""]
    lines.append("**PASS**" if ok else "**FAIL**")
    Path(report).write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

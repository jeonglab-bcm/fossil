"""The pipeline's check step.

usage: check_reproduction.py RESULTS_JSON RUN_DIR FIGURES_DIR SENSITIVITY_JSON REMOVED_TSV COMMITTED_OUTPUT REPORT_MD

Fails (exit 1) when
* check_results.py finds a broken rule or a stale verdict in results.json;
* the fresh run differs from the committed outputs (compare_runs.py: numbers to 1e-6 relative or
  2e-6 absolute, images to 2 grey levels). Decision values are written rounded to 6 decimals; on
  GitHub's runners a few AvePscore-20 values land one unit of that rounding away from the
  cluster's (CPU last bits), so the absolute tolerance is two units of the written precision: output/run (every analysis JSON), output/figures (renders, overlays,
  scores), output/sensitivity.json, output/homology_removed.tsv, and results.json against the
  committed one;
* an expected output is missing.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def main():
    results, rundir, figs, sens, removed, committed, report = sys.argv[1:8]
    committed = Path(committed)
    lines = ["# PMC4331676 reproduction check", ""]
    ok = True

    rc, out = run([sys.executable, str(HERE / "check_results.py"), results, "--markdown", "--skip-files"])
    lines += ["## results.json", "", out.strip(), ""]
    ok &= rc == 0

    with tempfile.TemporaryDirectory() as tmp:
        fresh, comm = Path(tmp) / "fresh", Path(tmp) / "committed"
        for d in (fresh, comm):
            d.mkdir()
        shutil.copytree(rundir, fresh / "run")
        shutil.copytree(figs, fresh / "figures")
        for f in (results, sens, removed):
            shutil.copy(f, fresh / Path(f).name)
        shutil.copytree(committed / "run", comm / "run")
        shutil.copytree(committed / "figures", comm / "figures")
        shutil.copy(committed / "sensitivity.json", comm / "sensitivity.json")
        shutil.copy(committed / "homology_removed.tsv", comm / "homology_removed.tsv")
        shutil.copy(committed.parent.parent / "results.json", comm / "results.json")
        rc, out = run([sys.executable, str(HERE / "compare_runs.py"), str(fresh), str(comm),
                       "--rtol", "1e-6", "--atol", "2e-6", "--pixel-tol", "2"])
        lines += ["## Fresh run against the committed outputs", "", out.strip(), ""]
        ok &= rc == 0

    lines.append("PASS" if ok else "FAIL")
    Path(report).write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

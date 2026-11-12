"""The pipeline's check step.

usage: check_reproduction.py RESULTS_JSON RUN_DIR FIGURES_DIR PUBLISHED_DATA COMMITTED_OUTPUT REPORT_MD [--full]

Fails (exit 1) when
* check_results.py finds a broken rule or a stale verdict in results.json;
* the fresh run differs from the committed outputs (compare_runs.py, numbers to 1e-6 relative,
  images to 2 grey levels): output/run (the analysis JSON) and output/figures (renders, overlays,
  scores), and results.json against the committed one;
* an expected output is missing.
With --full the samplers were rerun; their outputs (the *_fits.json and every number derived from
them) then depend on the CPU, so only results.json's rules are enforced and the comparison with the
committed outputs is reported, not enforced.
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
    results, rundir, figs, published_data, committed, report = sys.argv[1:7]
    full = "--full" in sys.argv
    committed = Path(committed)
    lines = ["# PMC4765871 reproduction check", ""]
    ok = True

    rc, out = run([sys.executable, str(HERE / "check_results.py"), results, "--markdown", "--skip-files"])
    lines += ["## results.json", "", out.strip(), ""]
    ok &= rc == 0

    with tempfile.TemporaryDirectory() as tmp:
        fresh = Path(tmp) / "fresh"
        shutil.copytree(rundir, fresh / "run")
        shutil.copytree(figs, fresh / "figures")
        shutil.copy(results, fresh / "results.json")
        comm = Path(tmp) / "committed"
        comm.mkdir()
        shutil.copytree(committed / "run", comm / "run")
        (comm / "figures").mkdir()
        for f in list(committed.glob("fig*_ours.png")) + list(committed.glob("fig*_overlay.png")) + [committed / "scores.json"]:
            shutil.copy(f, comm / "figures" / f.name)
        shutil.copy(committed / "published_data.json", comm / "published_data.json")
        shutil.copy(published_data, fresh / "published_data.json")
        shutil.copy(committed.parent.parent / "results.json", comm / "results.json")
        rc, out = run([sys.executable, str(HERE / "compare_runs.py"), str(fresh), str(comm),
                       "--rtol", "1e-6", "--atol", "1e-9", "--pixel-tol", "2"])
        lines += ["## Fresh run against the committed outputs" + (" (reported only: --full)" if full else ""), "",
                  out.strip(), ""]
        if not full:
            ok &= rc == 0

    lines.append("PASS" if ok else "FAIL")
    Path(report).write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

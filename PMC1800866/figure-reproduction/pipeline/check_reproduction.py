"""The pipeline's check step.

usage: check_reproduction.py RESULTS_JSON RUN_DIR COMMITTED_OUTPUT REPORT_MD [--full]

Fails (exit 1) when
* check_results.py finds a broken rule or a stale verdict in results.json;
* the fresh run differs from the committed outputs (compare_runs.py: numbers to 1e-6 relative,
  images to 2 grey levels), and results.json from the committed one;
* an expected output is missing.
With --full the LOO was refitted and the structures parsed again; the comparison with the committed
outputs is then reported, not enforced.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARTS = ["struct", "sites", "figures12", "evaluation", "predictions", "proteome", "published_curves.json"]
# package.json holds timings and temporary paths; its pass/fail is in results.json, which is compared.
# proteome_sample.* are committed inputs of the run (the sample is drawn by sample_proteome.py from the
# full proteome, which --full fetches), not outputs.
IGNORE = ["package.json", "proteome/proteome_sample.fa", "proteome/proteome_sample.tsv"]


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def main():
    results, rundir, committed, report = sys.argv[1:5]
    full = "--full" in sys.argv
    committed = Path(committed)
    lines = ["# PMC1800866 reproduction check", ""]
    ok = True

    rc, out = run([sys.executable, str(HERE / "check_results.py"), results, "--markdown", "--skip-files"])
    lines += ["## results.json", "", out.strip(), ""]
    ok &= rc == 0

    missing = [p for p in PARTS if not (Path(rundir) / p).exists()]
    if missing:
        lines += [f"Missing outputs: {', '.join(missing)}", ""]
        ok = False

    with tempfile.TemporaryDirectory() as tmp:
        fresh, comm = Path(tmp) / "fresh", Path(tmp) / "committed"
        fresh.mkdir()
        comm.mkdir()
        for p in PARTS:
            for src, dst in ((Path(rundir) / p, fresh / p), (committed / p, comm / p)):
                if src.is_dir():
                    shutil.copytree(src, dst)
                elif src.exists():
                    shutil.copy(src, dst)
        shutil.copy(results, fresh / "results.json")
        shutil.copy(committed.parent.parent / "results.json", comm / "results.json")
        rc, out = run([sys.executable, str(HERE / "compare_runs.py"), str(fresh), str(comm),
                       "--rtol", "1e-6", "--atol", "1e-9", "--pixel-tol", "2", "--ignore", *IGNORE])
        lines += ["## Fresh run against the committed outputs" + (" (reported only: --full)" if full else ""), "", out.strip(), ""]
        if not full:
            ok &= rc == 0

    lines.append("PASS" if ok else "FAIL")
    Path(report).write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

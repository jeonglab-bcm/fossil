"""The pipeline's check step.

usage: check_reproduction.py RESULTS_JSON RUN_DIR FIGURES_DIR COMMITTED_OUTPUT REPORT_MD [--full]

Fails (exit 1) when
* check_results.py finds a broken rule or a stale verdict in results.json;
* the fresh run differs from the committed outputs (compare_runs.py: numbers to 1e-6 relative,
  images to 2 grey levels): output/run, output/figures.json and the renders and overlays, and
  results.json against the committed one (the run date and the package report, which records the
  machine's Python and paths, are left out);
* an expected output is missing.
With --full the Collins scores, GO, HPRD and KEGG were downloaded again; KEGG changes with every
release, so the comparison with the committed outputs is reported, not enforced.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def strip(results_json, dest):
    r = json.loads(Path(results_json).read_text())
    r["run"].pop("date", None)
    for it in r["items"]:
        if it["id"] == "package":
            it["check"]["detail"] = it["check"]["detail"].split(";")[0]
    Path(dest).write_text(json.dumps(r, indent=1, ensure_ascii=False))


def main():
    results, rundir, figs, committed, report = sys.argv[1:6]
    full = "--full" in sys.argv
    committed = Path(committed)
    lines = ["# PMC2711306 reproduction check", ""]
    ok = True

    rc, out = run([sys.executable, str(HERE / "check_results.py"), results, "--markdown", "--skip-files"])
    lines += ["## results.json", "", out.strip(), ""]
    ok &= rc == 0

    with tempfile.TemporaryDirectory() as tmp:
        fresh, comm = Path(tmp) / "fresh", Path(tmp) / "committed"
        for base, src_run, src_figs, res in ((fresh, Path(rundir), Path(figs), Path(results)),
                                            (comm, committed / "run", committed, committed.parent.parent / "results.json")):
            (base / "run").mkdir(parents=True)
            for f in src_run.iterdir():
                if f.name != "package.json":
                    shutil.copy(f, base / "run" / f.name)
            (base / "figures").mkdir()
            for f in list(src_figs.glob("fig*_ours.png")) + list(src_figs.glob("fig*_overlay.png")) + [src_figs / "figures.json"]:
                if f.exists():
                    shutil.copy(f, base / "figures" / f.name)
            if res.exists():
                strip(res, base / "results.json")
        missing = [p.name for p in (comm / "run").iterdir() if not (fresh / "run" / p.name).exists()]
        if missing:
            lines += [f"Missing from the fresh run: {', '.join(missing)}", ""]
            ok = False
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

"""Check step: verdicts are consistent, and the fresh run matches the committed
outputs. Writes report.md for the job summary.

    check_reproduction.py RESULTS_JSON RUNDIR COMMITTED REPORT [--full]
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("rundir")
    ap.add_argument("committed")
    ap.add_argument("report")
    ap.add_argument("--full", action="store_true")
    args = ap.parse_args()

    lines = ["# PMC3499255 reproduction report", ""]
    failed = False

    # 1. verdicts
    cr = run([sys.executable, os.path.join(HERE, "check_results.py"), args.results,
              "--markdown", "--skip-files"])
    lines += ["## Results", "", cr.stdout, ""]
    if cr.returncode != 0:
        failed = True
        lines += ["**check_results failed:**", "```", cr.stderr, "```", ""]

    # 2. fresh vs committed (ignore matplotlib PNGs: pixel-identical rendering is
    # not guaranteed across environments; the numbers behind them are checked).
    # medians.json is a committed input for the --full series, not a pipeline output;
    # package.json carries the environment's Python version and venv paths.
    ignore = ["*.png", "*.log", "report.md", "medians.json", "package.json"]
    if not args.full:
        # test.json / series.json are copied from committed when not --full, so they
        # match trivially; still compared.
        pass
    comp = run([sys.executable, os.path.join(HERE, "compare_runs.py"),
                args.rundir, args.committed, "--ignore", *ignore])
    lines += ["## Fresh run against committed outputs", "", comp.stdout, ""]
    if comp.returncode != 0:
        failed = True
        lines += ["**compare_runs found differences.**", "```", comp.stderr, "```", ""]

    with open(args.report, "w") as fh:
        fh.write("\n".join(lines))
    print("\n".join(lines))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

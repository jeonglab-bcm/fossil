#!/usr/bin/env python3
"""The pipeline's check step.

usage: check_reproduction.py RESULTS_JSON RUN_OUTPUT COMMITTED_OUTPUT REPORT_MD [--full]

Fails (exit 1) when

* check_results.py finds a broken rule, a stale verdict or a missing cause in results.json;
* the fresh run differs from the committed outputs (compare_runs.py: numbers at 1e-6 relative,
  images by decoded pixels);
* an expected output is missing.

With --full every score matrix was recomputed from the benchmark data rather than read from the
committed ones. The scores are deterministic, so the comparison is still enforced; only the score
files themselves, which the default run does not rewrite, are left out of it.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPECTED = [
    "tables.json",
    "figure1_comparison.json",
    "figure1_published.json",
    "predictions.json",
    "claims.json",
    "fig1_ours.png",
    "fig2_ours.png",
    *[f"fig1{label}_{kind}.png" for label in "abcd" for kind in ("ours", "published", "overlay", "diff")],
]


def run(command: list[str]) -> tuple[int, str]:
    finished = subprocess.run(command, capture_output=True, text=True)
    return finished.returncode, finished.stdout + finished.stderr


def main() -> int:
    results, run_output, committed, report = sys.argv[1:5]
    full = "--full" in sys.argv
    run_output, committed = Path(run_output), Path(committed)
    lines = ["# PMC2735674 reproduction check", ""]
    ok = True

    code, out = run([sys.executable, str(HERE / "check_results.py"), results, "--markdown", "--skip-files"])
    lines += ["## results.json", "", out.strip(), ""]
    ok &= code == 0

    missing = [name for name in EXPECTED if not (run_output / name).is_file()]
    if missing:
        lines += ["## Missing outputs", "", *[f"- {name}" for name in missing], ""]
        ok = False

    with tempfile.TemporaryDirectory() as tmp:
        fresh, old = Path(tmp) / "fresh", Path(tmp) / "committed"
        fresh.mkdir()
        old.mkdir()
        for name in EXPECTED:
            if (run_output / name).is_file():
                shutil.copy(run_output / name, fresh / name)
            if (committed / name).is_file():
                shutil.copy(committed / name, old / name)
        # results.json records the versions of the runtime and the libraries. Those are facts
        # about the machine, not results, and a runner's patch version differs from ours, so they
        # are reported below and left out of the comparison.
        environments = {}
        committed_results = committed.parent.parent / "results.json"
        for label, source, folder in (
            ("fresh", Path(results), fresh),
            ("committed", committed_results, old),
        ):
            if not source.is_file():
                continue
            payload = json.loads(source.read_text())
            environments[label] = payload.get("run", {}).pop("environment", {})
            (folder / "results.json").write_text(json.dumps(payload, indent=1) + "\n")
        code, out = run(
            [
                sys.executable,
                str(HERE / "compare_runs.py"),
                str(fresh),
                str(old),
                "--rtol",
                "1e-6",
                "--atol",
                "1e-9",
                "--pixel-tol",
                "2",
            ]
        )
        lines += ["## Fresh run against the committed outputs", "", out.strip(), ""]
        ok &= code == 0

    if environments:
        names = sorted({k for e in environments.values() for k in e})
        lines += [
            "## Environment",
            "",
            "Recorded in results.json and left out of the comparison above.",
            "",
            "| Package | Fresh run | Committed |",
            "| --- | --- | --- |",
            *[
                f"| {name} | {environments.get('fresh', {}).get(name, '-')} |"
                f" {environments.get('committed', {}).get(name, '-')} |"
                for name in names
            ],
            "",
        ]
    lines += [
        "## Run",
        "",
        f"- score matrices: {'recomputed from the benchmark data (--full)' if full else 'read from the committed outputs, nuclear receptor recomputed'}",
        "",
    ]
    Path(report).write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Fill the README placeholders from results.json, so no verdict is typed by hand.

    update_readmes.py --results PMC2735674/results.json

`<!--__RESULTS_TABLE__-->` becomes the `check_results.py --markdown` table and
`<!--__CLAIMS_LINE__-->` becomes the one line about the main claim from results_notes.json. Both
placeholders are kept, so the command can be run again after a rerun.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLACEHOLDERS = {
    "RESULTS_TABLE": None,  # filled from check_results.py --markdown
    "CLAIMS_LINE": None,  # filled from results_notes.json
}


def fill(path: Path, name: str, body: str) -> bool:
    text = path.read_text()
    marker = f"<!--__{name}__-->"
    if marker not in text:
        return False
    pattern = re.compile(
        re.escape(marker) + r"(.*?)" + re.escape(f"<!--__{name}_END__-->"), re.S
    )
    block = f"{marker}\n\n{body.strip()}\n\n<!--__{name}_END__-->"
    text = pattern.sub(block, text) if pattern.search(text) else text.replace(marker, block)
    path.write_text(text)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results", type=Path, required=True)
    ap.add_argument("--readmes", type=Path, nargs="*", help="files to fill (default: both READMEs)")
    args = ap.parse_args()

    paper = args.results.parent
    readmes = args.readmes or [paper / "README.md", paper / "figure-reproduction" / "README.md"]
    finished = subprocess.run(
        [sys.executable, str(HERE / "check_results.py"), str(args.results), "--markdown", "--skip-files"],
        capture_output=True,
        text=True,
    )
    if finished.returncode != 0:
        print(finished.stdout + finished.stderr, file=sys.stderr)
        return 1
    table = finished.stdout.strip()
    notes = json.loads((paper / "figure-reproduction" / "results_notes.json").read_text())
    claims_line = notes["page"]["claims_line"]

    for readme in readmes:
        changed = fill(readme, "RESULTS_TABLE", table)
        changed |= fill(readme, "CLAIMS_LINE", claims_line)
        print(f"{readme}: {'filled' if changed else 'no placeholder found'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

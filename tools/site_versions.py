#!/usr/bin/env python3
"""The Paper2Repro column of the front page, from each paper's "skill" block.

Usage:
  site_versions.py           check that every paper's skill block gives a Paper2Repro cell

tools/build_index.py writes the column when it builds the front page; cell() below is what it writes,
so the column is generated, never typed:

  a version            v0.4.0, linked to its release; "worked out from the session" when inferred
  source "unknown"     Not recorded
  source "none"        Before Paper2Repro

An optional "site_note" in the skill block adds a short line under it. The skill block is read as
tools/check_skill.py reads it.
"""
import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_skill import ROOT, skill_block  # noqa: E402

RELEASE = "https://github.com/jeonglab-bcm/Paper2Repro/releases/tag/paper2repro-v"


def cell(paper):
    where, s = skill_block(paper)
    if not isinstance(s, dict):
        raise SystemExit(f"{paper}: no skill block in {where or 'any results.json'}; see tools/check_skill.py")
    note = s.get("site_note")
    if s.get("version"):
        v = html.escape(s["version"])
        out = f'<a class="ver" href="{RELEASE}{v}">v{v}</a>'
        if s.get("source") == "inferred":
            note = note or "worked out from the session"
    elif s.get("source") == "none":
        out = '<span class="ver-none">Before Paper2Repro</span>'
    else:
        out = '<span class="ver-none">Not recorded</span>'
    if note:
        out += f'<span class="ver-note">{html.escape(note)}</span>'
    return out


def main():
    if sys.argv[1:] == ["--write"]:
        sys.exit("site_versions.py --write is gone: tools/build_index.py writes the column when it builds the page")
    if sys.argv[1:]:
        sys.exit(__doc__)
    from build_index import papers  # noqa: E402
    errors = []
    for paper in papers():
        try:
            cell(paper)
        except SystemExit as e:
            errors.append(str(e))
    for e in errors:
        print(f"ERROR {e}", file=sys.stderr)
    if errors:
        return 1
    print("every paper's skill block gives its Paper2Repro cell on the front page")
    return 0


if __name__ == "__main__":
    sys.exit(main())

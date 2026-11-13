#!/usr/bin/env python3
"""Fill the Paper2Repro column of the front page from each paper's "skill" block.

Usage:
  site_versions.py           check that site/index.html shows what the skill blocks say
  site_versions.py --write   rewrite the Paper2Repro cells

Each row of the front-page index names its paper in <span class="pmc">PMC…</span> and ends with
<td data-label="Paper2Repro">…</td>. The cell is generated, never typed:

  a version            v0.4.0, linked to its release; "worked out from the session" when inferred
  source "unknown"     Not recorded
  source "none"        Before Paper2Repro

An optional "site_note" in the skill block adds a short line under it. The skill block is read as
tools/check_skill.py reads it.
"""
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_skill import ROOT, skill_block  # noqa: E402

PAGE = Path(ROOT) / "site" / "index.html"
RELEASE = "https://github.com/jeonglab-bcm/Paper2Repro/releases/tag/paper2repro-v"
ROW = re.compile(r"<tr>.*?</tr>", re.S)
CELL = re.compile(r'(<td data-label="Paper2Repro">)(.*?)(</td>)', re.S)


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
    write = sys.argv[1:] == ["--write"]
    if sys.argv[1:] not in ([], ["--write"]):
        sys.exit(__doc__)
    page = PAGE.read_text(encoding="utf-8")
    errors = []

    def fix(row):
        r = row.group(0)
        m = re.search(r'<span class="pmc">(PMC\d+)</span>', r)
        if not m:
            return r
        paper = m.group(1)
        c = CELL.search(r)
        if not c:
            errors.append(f'{paper}: its row has no <td data-label="Paper2Repro"> cell')
            return r
        want = cell(paper)
        if c.group(2) != want:
            errors.append(f"{paper}: the page shows {c.group(2)!r}, the skill block says {want!r}")
        return r[:c.start(2)] + want + r[c.end(2):]

    new = ROW.sub(fix, page)
    if write:
        PAGE.write_text(new, encoding="utf-8")
        print(f"wrote {len(errors)} cell(s)" if errors else "nothing to change")
        return 0
    for e in errors:
        print(f"ERROR {e}", file=sys.stderr)
    if errors:
        print("run python3 tools/site_versions.py --write", file=sys.stderr)
        return 1
    print("site/index.html: every Paper2Repro cell matches its skill block")
    return 0


if __name__ == "__main__":
    sys.exit(main())

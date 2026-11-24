#!/usr/bin/env python3
"""Move front-page rows into PMC…/index.json.

Usage:
  index_row_to_json.py [--ref REF] [--force] [PMC… ...]

Reads site/index.html as it stands in REF (a branch, tag or commit; the working tree when left out),
finds the row of each paper named (every row when none is named) and writes PMC…/index.json, which
tools/build_index.py turns back into the row. The paper's footer link, when the page has one, goes
along. An existing index.json is kept unless --force.

For a reproduction pull request opened before the front page was generated (issue #129): merge main
into its branch, keep main's site/index.html and README.md, and run

  python3 tools/index_row_to_json.py --ref origin/<the PR's branch> PMC…

so the row it wrote by hand becomes its own PMC…/index.json.

Each index.json written is built back into a row and compared with the row it came from; a difference
is reported (the Paper2Repro cell is left out of the comparison, since it comes from the skill block).
"""
import html
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_index import GITHUB, ROOT, VERDICTS, row, write  # noqa: E402

ROW = re.compile(r"[ \t]*<tr>\s*<td class=\"date\".*?</tr>\n?", re.S)


def page_at(ref):
    if ref is None:
        return (ROOT / "site" / "index.html").read_text(encoding="utf-8")
    return subprocess.run(["git", "-C", str(ROOT), "show", f"{ref}:site/index.html"],
                          capture_output=True, text=True, check=True).stdout


def one(pattern, text, what):
    m = re.search(pattern, text, re.S)
    if not m:
        raise ValueError(f"no {what}")
    return m.group(1)


def parse(tr, footer):
    """index.json of one hand-written row."""
    tr = re.sub(r"<!--/?PMC\d+-\w+-->", "", tr)  # the markers pipelines wrote between
    p = one(r'<span class="pmc">(PMC\d+)</span>', tr, "PMC id")
    d = {"pmcid": p,
         "published": one(r'data-label="Published"><time datetime="([^"]+)"', tr, "published date"),
         "analyzed": one(r'data-label="Analyzed"><time datetime="([^"]+)"', tr, "analyzed date"),
         "title": html.unescape(one(r'<a class="title" href="[^"]*">(.*?)</a>', tr, "title")),
         "journal": html.unescape(one(r'<span class="journal">(.*?)</span>', tr, "journal"))}
    go = re.findall(r'<a href="([^"]*)">(.*?)</a>', one(r'<span class="go">(.*?)</span>', tr, "links"))
    links = []
    for href, text in go:
        href, text = html.unescape(href), html.unescape(text)
        if text == "Article" and href.startswith("https://doi.org/"):
            d["doi"] = href.removeprefix("https://doi.org/")
        elif text == "GitHub" and href == GITHUB + p:
            pass
        else:
            links.append({"text": text, "href": href})
    if "doi" not in d:
        raise ValueError("no Article link to https://doi.org/")
    if links:
        d["links"] = links

    def items(label):
        ul = one(rf'data-label="{label}"><ul>(.*?)</ul>', tr, label)
        return [x.strip() for x in re.findall(r"<li>(.*?)</li>", ul, re.S)]

    d["lost"], d["recovered"] = items("What we lost"), items("What we recovered")
    cellv = one(r'data-label="Verdict">(.*?)</td>', tr, "verdict")
    v = one(r'<span class="verdict" data-v="(\w+)">', cellv, "verdict")
    if v not in VERDICTS:
        raise ValueError(f"verdict {v!r} is not one of {', '.join(VERDICTS)}")
    d["verdict"] = {"v": v}
    note = re.search(r'<span class="verdict-note">(.*?)</span>', cellv, re.S)
    if note:
        d["verdict"]["note"] = html.unescape(note.group(1))
    if p in footer:
        d["footer"] = footer[p]
    return d


def normal(tr):
    tr = re.sub(r"<!--/?PMC\d+-\w+-->", "", tr)
    tr = re.sub(r'<td data-label="Paper2Repro">.*?</td>', "", tr, flags=re.S)
    return re.sub(r"\s+", " ", tr).strip()


def main():
    args, ref, force = sys.argv[1:], None, False
    if "--force" in args:
        args.remove("--force")
        force = True
    if "--ref" in args:
        i = args.index("--ref")
        if i + 1 >= len(args):
            sys.exit(__doc__)
        ref = args[i + 1]
        del args[i:i + 2]
    if any(not re.fullmatch(r"PMC\d+", a) for a in args):
        sys.exit(__doc__)
    page = page_at(ref)
    foot = page.split('<footer class="foot">', 1)[-1]
    footer = {p: html.unescape(t) for p, t in re.findall(r'<a href="(PMC\d+)/">(.*?)</a>', foot)}
    rows = {}
    for tr in ROW.findall(page.split('<footer class="foot">', 1)[0]):
        m = re.search(r'<span class="pmc">(PMC\d+)</span>', tr)
        if m:
            rows[m.group(1)] = tr
    wanted = args or sorted(rows)
    failed = False
    for p in wanted:
        if p not in rows:
            print(f"ERROR {p}: no row in site/index.html{' at ' + ref if ref else ''}", file=sys.stderr)
            failed = True
            continue
        out = ROOT / p / "index.json"
        if out.exists() and not force:
            print(f"{p}: {p}/index.json exists, kept (--force to rewrite)")
            continue
        if not out.parent.is_dir():
            print(f"ERROR {p}: no folder {p}/ here; check out the branch that adds it", file=sys.stderr)
            failed = True
            continue
        try:
            d = parse(rows[p], footer)
        except ValueError as e:
            print(f"ERROR {p}: {e}", file=sys.stderr)
            failed = True
            continue
        write(out, d)
        if normal(row(d)) != normal(rows[p]):
            print(f"WARNING {p}: the row built from {p}/index.json differs from the page's row; compare them",
                  file=sys.stderr)
            failed = True
        else:
            print(f"{p}: wrote {p}/index.json")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

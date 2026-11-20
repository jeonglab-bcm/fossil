#!/usr/bin/env python3
"""Check the links of every row in the front-page paper index (site/index.html).

Usage:
  check_index_links.py

design.md: "In the paper index, each title links to the paper's results page; Article (the DOI),
Code analysis and GitHub sit under it." For each row that names its paper in
<span class="pmc">PMC…</span> this checks that:

  - the title (<a class="title">) links to the results page, "PMC…/"
  - the first link under it (<span class="go">) is "Article" and goes to https://doi.org/…
  - no link under it is called "Results" (the layout before the front-page redesign)
  - the results page site/PMC…/index.html exists

A row written by a paper's own pipeline from a template made before the redesign fails here.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "site" / "index.html"
ROW = re.compile(r"<tr>.*?</tr>", re.S)


def check(row):
    m = re.search(r'<span class="pmc">(PMC\d+)</span>', row)
    if not m:
        return None, []
    paper, errors = m.group(1), []
    title = re.search(r'<a class="title" href="([^"]*)"', row)
    if not title:
        errors.append("no <a class=\"title\"> link")
    elif title.group(1) != f"{paper}/":
        errors.append(f"the title links to {title.group(1)!r}, not to its results page {paper + '/'!r}")
    go = re.search(r'<span class="go">(.*?)</span>', row, re.S)
    links = re.findall(r'<a href="([^"]*)">([^<]*)</a>', go.group(1)) if go else []
    if not links:
        errors.append('no links under the title (<span class="go">)')
    else:
        href, text = links[0]
        if text != "Article" or not href.startswith("https://doi.org/"):
            errors.append(f"the first link under the title is {text!r} to {href!r}, not Article to https://doi.org/…")
        for href, text in links:
            if text == "Results":
                errors.append(f"a Results link ({href!r}) sits under the title; the title is the way to the results")
    if not (ROOT / "site" / paper / "index.html").is_file():
        errors.append(f"site/{paper}/index.html does not exist")
    return paper, errors


def main():
    if sys.argv[1:]:
        sys.exit(__doc__)
    page = PAGE.read_text(encoding="utf-8")
    papers, failed = [], False
    for row in ROW.findall(page):
        paper, errors = check(row)
        if paper is None:
            continue
        papers.append(paper)
        for e in errors:
            failed = True
            print(f"ERROR {paper}: {e}", file=sys.stderr)
    if not papers:
        print("ERROR no paper rows found in site/index.html", file=sys.stderr)
        return 1
    if failed:
        print("each title links to PMC…/; Article (the DOI), Code analysis and GitHub sit under it (design.md)",
              file=sys.stderr)
        return 1
    print(f"site/index.html: all {len(papers)} titles link to their results pages, Article to the DOI")
    return 0


if __name__ == "__main__":
    sys.exit(main())

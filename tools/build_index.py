#!/usr/bin/env python3
"""Build the front page's paper index from each paper's PMC…/index.json.

Usage:
  build_index.py                  check every PMC…/index.json and that the page builds
  build_index.py --out FILE       write the built front page to FILE (the deploy writes _site/index.html)

site/index.html is the template. Its <tbody> holds <!--PAPER-ROWS--> and its footer links hold
<!--PAPER-LINKS-->; this fills both, and the data-count numbers, from the papers. No pull request edits
the rows by hand, so two paper pull requests never touch the same file (issue #129).

PMC…/index.json, one per paper:

  pmcid         "PMC3196500", the folder's name
  published     the paper's date: "2011-10-18", or "2012-06" when only the month is printed
  analyzed      the day we finished it: "2026-11-19"; rows go newest first by this date
  title         the paper's title, plain text
  journal       "Thorlund et al., PLoS ONE", plain text
  doi           "10.1371/journal.pone.0025491", without https://doi.org/
  links         optional, links between Article and GitHub: [{"text": "Code analysis", "href": "PMC…/implementation.html"}]
  lost          what was lost, one HTML fragment per item
  recovered     what we recovered, one HTML fragment per item
  verdict       {"v": "agrees" | "partly" | "differs" | "running", "note": optional plain-text line}
  footer        optional plain text for the paper's link in the footer ("Ratio of means tables")

The Article and GitHub links come from doi and pmcid, and the title always links to PMC…/, so a row
keeps the layout of design.md and tools/check_index_links.py. The Paper2Repro column comes from the
paper's skill block (tools/site_versions.py), never from index.json.

Pipelines change their own index.json with set_fields() (for instance the verdict after a rerun).
"""
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_versions import cell  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "site" / "index.html"
GITHUB = "https://github.com/jeonglab-bcm/fossil/tree/main/"
ROWS_MARK = "<!--PAPER-ROWS-->"
LINKS_MARK = "<!--PAPER-LINKS-->"

_C = '<circle cx="10" cy="10" r="8.6" fill="none" stroke="currentColor" stroke-width="1.6"/>'
VERDICTS = {  # design.md: a word with its icon to the right; never red or amber
    "agrees": ("Agrees", '<svg viewBox="0 0 20 20" aria-hidden="true">' + _C +
               '<path d="M6 10.4l2.7 2.7L14.2 7.4" fill="none" stroke="currentColor" stroke-width="1.9" '
               'stroke-linecap="round" stroke-linejoin="round"/></svg>'),
    "partly": ("Partly agrees", '<svg viewBox="0 0 20 20" aria-hidden="true">' + _C +
               '<path d="M10 1.4A8.6 8.6 0 0 0 10 18.6Z" fill="currentColor"/></svg>'),
    "differs": ("Differs", '<svg viewBox="0 0 20 20" aria-hidden="true">' + _C + '</svg>'),
    "running": ("Running", '<svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="8.6" fill="none" '
                'stroke="currentColor" stroke-width="1.6" stroke-dasharray="1.6 2.4"/></svg>'),
}
FIELDS = {"pmcid", "published", "analyzed", "title", "journal", "doi", "links", "lost", "recovered", "verdict", "footer"}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
         "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]


def papers():
    """The folders that are papers: PMC… at the top with a results page under site/."""
    return sorted(p.name for p in ROOT.glob("PMC*") if p.is_dir())


def load(paper):
    """index.json of one paper, and a list of what is wrong with it."""
    path = ROOT / paper / "index.json"
    if not path.is_file():
        return None, [f"{paper}/index.json does not exist (tools/index_row_to_json.py writes it from a row)"]
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return None, [f"{paper}/index.json: {e}"]
    errors = []
    for k in sorted(set(d) - FIELDS):
        errors.append(f"unknown field {k!r}")
    if d.get("pmcid") != paper:
        errors.append(f"pmcid is {d.get('pmcid')!r}, not the folder's name {paper!r}")
    if not re.fullmatch(r"\d{4}(-\d{2}(-\d{2})?)?", str(d.get("published", ""))):
        errors.append("published is not YYYY, YYYY-MM or YYYY-MM-DD")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(d.get("analyzed", ""))):
        errors.append("analyzed is not YYYY-MM-DD")
    for k in ("title", "journal", "doi"):
        if not isinstance(d.get(k), str) or not d[k].strip():
            errors.append(f"{k} is missing")
    if str(d.get("doi", "")).startswith("http"):
        errors.append("doi is a URL; give it without https://doi.org/")
    for k in ("lost", "recovered"):
        if not isinstance(d.get(k), list) or not d[k] or not all(isinstance(x, str) and x for x in d[k]):
            errors.append(f"{k} is not a list of one or more items")
    links = d.get("links", [])
    if not isinstance(links, list) or not all(isinstance(x, dict) and set(x) == {"text", "href"} for x in links):
        errors.append('links is not a list of {"text", "href"}')
    elif any(x["text"] in ("Article", "GitHub", "Results") for x in links):
        errors.append("links repeats Article or GitHub, or adds Results; those come from doi and pmcid")
    v = d.get("verdict")
    if not isinstance(v, dict) or v.get("v") not in VERDICTS or set(v) - {"v", "note"}:
        errors.append(f'verdict is not {{"v": one of {", ".join(VERDICTS)}, "note": optional}}')
    if not (ROOT / "site" / paper / "index.html").is_file():
        errors.append(f"site/{paper}/index.html does not exist; the title links to it")
    return d, [f"{paper}/index.json: {e}" for e in errors]


def shown(day):
    """'2011-10-18' -> '18 Oct 2011', '2012-06' -> 'Jun 2012'."""
    parts = [int(x) for x in day.split("-")]
    if len(parts) == 1:
        return str(parts[0])
    if len(parts) == 2:
        return f"{MONTHS[parts[1] - 1]} {parts[0]}"
    return f"{parts[2]} {MONTHS[parts[1] - 1]} {parts[0]}"


def row(d):
    """The <tr> of one paper, as the front page has always written it."""
    e = html.escape
    p = d["pmcid"]
    go = [f'<a href="https://doi.org/{e(d["doi"])}">Article</a>']
    go += [f'<a href="{e(x["href"])}">{e(x["text"])}</a>' for x in d.get("links", [])]
    go.append(f'<a href="{GITHUB}{p}">GitHub</a>')
    word, icon = VERDICTS[d["verdict"]["v"]]
    note = d["verdict"].get("note")
    verdict = f'<span class="verdict" data-v="{d["verdict"]["v"]}">{word}{icon}</span>'
    if note:
        verdict += f'<span class="verdict-note">{e(note)}</span>'

    def items(xs):
        return "".join(f"\n                  <li>{x}</li>" for x in xs)

    return f"""              <tr>
                <td class="date" data-label="Published"><time datetime="{d['published']}">{shown(d['published'])}</time></td>
                <td class="date" data-label="Analyzed"><time datetime="{d['analyzed']}">{shown(d['analyzed'])}</time></td>
                <td data-label="Paper">
                  <span class="pmc">{p}</span>
                  <a class="title" href="{p}/">{e(d['title'])}</a>
                  <span class="journal">{e(d['journal'])}</span>
                  <span class="go">{''.join(go)}</span>
                </td>
                <td data-label="What we lost"><ul>{items(d['lost'])}
                </ul></td>
                <td data-label="What we recovered"><ul>{items(d['recovered'])}
                </ul></td>
                <td data-label="Verdict">{verdict}</td>
                <td data-label="Paper2Repro">{cell(p)}</td>
              </tr>
"""


def count_text(key, n, cap):
    t = str(n) if "year" in key or n > 20 else WORDS[n]
    return t[:1].upper() + t[1:] if cap else t


def build():
    """The built front page, and a list of errors (the page is None when there are any)."""
    entries, errors = [], []
    for p in papers():
        d, errs = load(p)
        errors += errs
        if d and not errs:
            entries.append(d)
    page = TEMPLATE.read_text(encoding="utf-8")
    for mark in (ROWS_MARK, LINKS_MARK):
        if page.count(mark) != 1:
            errors.append(f"site/index.html: {mark} should appear once, not {page.count(mark)} times")
    if errors:
        return None, errors
    newest = sorted(entries, key=lambda d: (d["analyzed"], d["pmcid"]), reverse=True)
    oldest = sorted(entries, key=lambda d: (d["analyzed"], d["pmcid"]))
    rows = "".join(row(d) for d in newest)
    links = "".join(f'      <a href="{d["pmcid"]}/">{html.escape(d["footer"])}</a>\n' for d in oldest if d.get("footer"))
    page = re.sub(r"[ \t]*" + re.escape(ROWS_MARK) + r"\n?", lambda m: rows, page)
    page = re.sub(r"[ \t]*" + re.escape(LINKS_MARK) + r"\n?", lambda m: links, page)
    # The numbers the page's script also counts, so the page is right without the script.
    years = [int(d["published"][:4]) for d in entries]
    values = {"papers": len(entries), "first-year": min(years), "last-year": max(years)}
    for v in VERDICTS:
        values[v] = sum(d["verdict"]["v"] == v for d in entries)

    def fill(m):
        key = m.group(2)
        if key not in values:
            return m.group(0)
        return f"{m.group(1)}{count_text(key, values[key], 'data-cap' in m.group(1))}</span>"

    page = re.sub(r'(<span data-count="([\w-]+)"[^>]*>)[^<]*</span>', fill, page)
    return page, []


def set_fields(paper, **fields):
    """Change fields of PMC…/index.json, for a paper's own pipeline (e.g. verdict={"v": …, "note": …})."""
    path = ROOT / paper / "index.json"
    d = json.loads(path.read_text(encoding="utf-8"))
    d.update(fields)
    write(path, d)


def write(path, d):
    order = ["pmcid", "published", "analyzed", "title", "journal", "doi", "links", "lost", "recovered", "verdict", "footer"]
    d = {k: d[k] for k in order if k in d} | {k: v for k, v in d.items() if k not in order}
    path.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    args = sys.argv[1:]
    if args not in ([], ) and not (len(args) == 2 and args[0] == "--out"):
        sys.exit(__doc__)
    page, errors = build()
    for e in errors:
        print(f"ERROR {e}", file=sys.stderr)
    if errors:
        return 1
    n = page.count('<span class="pmc">')
    if args:
        out = Path(args[1])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page, encoding="utf-8")
        print(f"wrote {out}: {n} papers")
    else:
        print(f"every PMC…/index.json is good; the front page builds with {n} papers")
    return 0


if __name__ == "__main__":
    sys.exit(main())

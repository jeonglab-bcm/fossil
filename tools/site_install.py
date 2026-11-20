#!/usr/bin/env python3
"""Put an "Install" block at the top of each results page whose paper has a recovered package.

Usage:
  site_install.py           check that every site/PMC…/index.html shows what its package README says
  site_install.py --write   rewrite the blocks

A paper has a package when PMC…/package/README.md exists. The block is generated, never typed:

  name        "name" in package/pyproject.toml (Python) or "Package:" in package/DESCRIPTION (R)
  command     the first fenced code block under "## Install" in package/README.md
  needs       the first paragraph after that code block ("Python 3.10 or later, with NumPy …")
  links       the package's README and, when it exists, package/tutorial/TUTORIAL.md, on GitHub

It sits between <!-- install:begin --> and <!-- install:end -->, inside <div class="container bench">
and before the first figure. A paper's own build_page.py rewrites its whole page, so run
`python3 tools/site_install.py --write` after rebuilding one; CI (results-check.yml) runs the check.
"""
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
TREE = "https://github.com/jeonglab-bcm/fossil/blob/main"
BEGIN, END = "<!-- install:begin -->", "<!-- install:end -->"
ANCHOR = '<div class="container bench">\n'
BLOCK = re.compile(r"[ \t]*" + re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n?", re.S)


def package(paper):
    """(name, language, command, needs, links) for a paper's package, or None when it has none."""
    pkg = ROOT / paper / "package"
    readme = pkg / "README.md"
    if not readme.is_file():
        return None
    text = readme.read_text(encoding="utf-8")
    m = re.search(r"^## Install\s*\n+```(\w*)\n(.*?)\n```\n+(.*?)(?:\n\n|\Z)", text, re.S | re.M)
    if not m:
        raise SystemExit(f"{paper}: package/README.md has no fenced code block under '## Install'")
    fence, command, needs = m.group(1), m.group(2).strip(), " ".join(m.group(3).split())
    if needs.startswith(("#", "```")):
        needs = ""
    if (pkg / "pyproject.toml").is_file():
        name = re.search(r'^name\s*=\s*"([^"]+)"', (pkg / "pyproject.toml").read_text(encoding="utf-8"), re.M)
        lang = "Python"
    elif (pkg / "DESCRIPTION").is_file():
        name = re.search(r"^Package:\s*(\S+)", (pkg / "DESCRIPTION").read_text(encoding="utf-8"), re.M)
        lang = "R"
    else:
        raise SystemExit(f"{paper}: package/ has neither pyproject.toml nor DESCRIPTION")
    if not name:
        raise SystemExit(f"{paper}: no package name in package/{'pyproject.toml' if lang == 'Python' else 'DESCRIPTION'}")
    links = [("README", f"{TREE}/{paper}/package/README.md")]
    if (pkg / "tutorial" / "TUTORIAL.md").is_file():
        links.append(("Tutorial", f"{TREE}/{paper}/package/tutorial/TUTORIAL.md"))
    return name.group(1), lang, fence or ("r" if lang == "R" else "bash"), command, needs, links


def inline(md):
    """The little Markdown a requirements line uses: `code` and [text](url)."""
    out = html.escape(md, quote=False)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', out)


def block(paper):
    p = package(paper)
    if p is None:
        return None
    name, lang, fence, command, needs, links = p
    a = " ".join(f'<a href="{html.escape(u)}">{t}</a>' for t, u in links)
    needs_html = f'<p class="install-needs">{inline(needs)}</p>' if needs else ""
    return (f'{BEGIN}\n'
            f'    <section class="install surface" aria-labelledby="install-head">\n'
            f'      <div class="install-head"><h2 id="install-head">Install {html.escape(name)}</h2>'
            f'<span class="install-lang">{lang} package</span></div>\n'
            f'      <pre class="install-code" data-lang="{html.escape(fence)}"><code>{html.escape(command)}</code></pre>\n'
            f'      <div class="install-foot">{needs_html}<span class="install-links">{a}</span></div>\n'
            f'    </section>\n'
            f'    {END}\n')


def main():
    write = sys.argv[1:] == ["--write"]
    if sys.argv[1:] not in ([], ["--write"]):
        sys.exit(__doc__)
    errors, changed = [], 0
    for page in sorted(SITE.glob("PMC*/index.html")):
        paper = page.parent.name
        s = page.read_text(encoding="utf-8")
        want = block(paper)
        have = BLOCK.search(s)
        new = BLOCK.sub("", s)
        if want:
            if ANCHOR not in new:
                errors.append(f'{paper}: no <div class="container bench"> to put the install block in')
                continue
            new = new.replace(ANCHOR, ANCHOR + "    " + want, 1)
        if new != s:
            changed += 1
            what = "has no install block" if want and not have else (
                "has an install block but no package/README.md" if not want else "install block differs from package/README.md")
            errors.append(f"{paper}: site/{paper}/index.html {what}")
            if write:
                page.write_text(new, encoding="utf-8")
    if write:
        print(f"rewrote {changed} page(s)" if changed else "nothing to change")
        return 0
    for e in errors:
        print(f"ERROR {e}", file=sys.stderr)
    if errors:
        print("run python3 tools/site_install.py --write", file=sys.stderr)
        return 1
    print("site/PMC*/index.html: every install block matches its package README")
    return 0


if __name__ == "__main__":
    sys.exit(main())

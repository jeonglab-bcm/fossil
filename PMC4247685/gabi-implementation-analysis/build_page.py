# /// script
# requires-python = ">=3.10"
# dependencies = ["markdown==3.10"]
# ///
"""Build site/PMC4247685/implementation.html from this folder's README.md.

Usage, from anywhere:
    uv run PMC4247685/gabi-implementation-analysis/build_page.py [README.md] [out.html]

The README's sections, tables, code blocks and links are rendered as they stand. The page adds a short
hero of its own (a head, a lede and the paper's label), the site's top bar and footer, and links
../analysis.css. Relative links in the README become links into the repository on GitHub. Straight quotes
in prose are set curly. En and em dashes in prose (never in code) become "to" between two numbers and a
comma elsewhere; every line changed that way is printed.
"""
import html
import posixpath
import re
import sys
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REPO_DIR = HERE.relative_to(ROOT).as_posix()  # PMC4247685/gabi-implementation-analysis
GITHUB = "https://github.com/jeonglab-bcm/fossil/tree/main/"

src_path = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "README.md"
out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "site" / "PMC4247685" / "implementation.html"
src = src_path.read_text(encoding="utf-8")

title, body = src.split("\n", 1)
assert title.startswith("# "), "the README must open with its # title"
# The label and the footer state these facts; stop if the README no longer does.
for fact in ("Curry 2014", "BMC Bioinformatics 15:355"):
    assert fact in title, f"README title no longer names {fact!r}"
for fact in ("TOTAL: 77 pass", "about 75 s"):
    assert fact in body, f"README no longer says {fact!r}"


# Dashes: the site sets no en or em dash in prose. Code fences and code spans are left alone.
def undash(text):
    text = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", text)
    text = re.sub(r"\s*[–—]\s*", ", ", text)
    return re.sub(r"(\w)\s--\s(\w)", r"\1, \2", text)


changed, lines, fenced = [], body.split("\n"), False
for i, line in enumerate(lines):
    if line.lstrip().startswith("```"):
        fenced = not fenced
        continue
    if fenced:
        continue
    parts = re.split(r"(`[^`]*`)", line)
    new = "".join(p if p.startswith("`") else undash(p) for p in parts)
    if new != line:
        changed.append((i + 2, line, new))  # +2: the title line and 1-based numbering
        lines[i] = new
body = "\n".join(lines)

md = markdown.Markdown(
    extensions=["tables", "fenced_code", "toc", "smarty"],
    extension_configs={"smarty": {"smart_dashes": False, "smart_ellipses": False, "smart_angled_quotes": False}},
)
content = md.convert(body)


# Relative links point into the repository: send them to GitHub.
def to_github(m):
    href = m.group(1)
    if re.match(r"^(?:[a-z][a-z0-9+.-]*:|#|/)", href, re.I):
        return m.group(0)
    return f'href="{GITHUB}{posixpath.normpath(posixpath.join(REPO_DIR, href))}"'


content = re.sub(r'href="([^"]+)"', to_github, content)


# Tables go on a lifted white sheet that scrolls on its own; the recovered algorithm goes on a plastic band,
# every other code block in a tray. The nearest heading names each table's scroll region.
def heading_text(fragment):
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


out, pos, section = [], 0, ""
for m in re.finditer(r"<h([23])[^>]*>(.*?)</h\1>|<table>(.*?)</table>|<pre><code>", content, re.S):
    out.append(content[pos:m.start()])
    if m.group(1):
        section = heading_text(m.group(2))
        out.append(m.group(0))
    elif m.group(0).startswith("<table>"):
        inner = m.group(3).replace("<th>", '<th scope="col">')
        head_row = re.search(r"<tr>(.*?)</tr>", inner, re.S).group(1)
        cols = head_row.count("<th")
        sheet = "surface sheet" + (" sheet--measure" if cols <= 3 else "")
        label = html.escape(f"{section}, table", quote=True)
        out.append(f'<div class="{sheet}" role="region" aria-label="{label}" tabindex="0">\n'
                   f'<table class="record" data-cols="{cols}">{inner}</table>\n</div>')
    else:
        cls = "plastic band" if section.lower().startswith("recovered algorithm") else "tray"
        out.append(f'<pre class="{cls}" tabindex="0"><code>')
    pos = m.end()
out.append(content[pos:])
content = "".join(out)

# A last look: no dash may reach the page outside code.
prose = re.sub(r"<(pre|code)\b.*?</\1>", "", content, flags=re.S)
assert not re.search(r"[–—]", prose), "a dash survived in the README's prose"

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>GABi code analysis</title>
<meta name="description" content="What the GABi 0.1 code and Additional file 1 behind Curry (2014) compute, and where they differ from the paper. Built from the analysis README.">
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Schibsted+Grotesk:wght@700&family=Instrument+Sans:wght@400;500&family=DM+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="../analysis.css">
</head>
<body>
<header class="topbar">
  <div class="container">
    <a class="wordmark" href="../" aria-label="fossil, home">fossil</a>
    <nav aria-label="Site"><a href="../#papers">The papers</a><a href="./">Results</a></nav>
  </div>
</header>

<main>
  <section class="hero" aria-labelledby="hero-head">
    <div class="window" aria-hidden="true"><span></span><span></span><span></span><span></span></div>
    <div class="container hero-grid">
      <div class="hero-text">
        <h1 id="hero-head">We dug up and reran GABi’s code.</h1>
        <p class="lead">What it really computes, and where it parts from the paper.</p>
      </div>
      <figure class="rx" aria-label="The paper and its code">
        <figcaption class="label">
          <span class="label-head"><span>Curry 2014</span><span>GABi 0.1</span></span>
          <span class="label-title">GABi 0.1 and the S1 bicluster models</span>
          <span>BMC Bioinformatics 15:355</span>
          <span class="stamp" data-v="differs">Parts from the paper<small>each difference checked</small></span>
          <span class="label-stub">From CRAN and Additional file 1</span>
        </figcaption>
      </figure>
    </div>
  </section>

  <div class="container note">
    <article class="prose">
{content}
<p class="colophon">Built from <a href="{GITHUB}{REPO_DIR}">{REPO_DIR}/README.md</a> by <code>build_page.py</code>. GABi is GPL (≥ 2); Additional file 1 is CC BY 4.0. Neither is redistributed here.</p>
    </article>
  </div>
</main>

<footer class="foot">
  <div class="container">
    <p class="statement">All 77 checks rerun in about 75 seconds.</p>
    <nav class="links" aria-label="Footer">
      <a href="{GITHUB}{REPO_DIR}">The code on GitHub</a>
      <a href="./">GABi figures</a>
      <a href="../PMC4081639/implementation.html">lldmn code analysis</a>
    </nav>
  </div>
</footer>
</body>
</html>
"""

out_path.write_text(page, encoding="utf-8")
print(f"wrote {out_path} ({len(page)} bytes)")
print(f"{len(changed)} README line(s) changed for dashes" + (":" if changed else ""))
for n, before, after in changed:
    print(f"  README.md:{n}\n    - {before}\n    + {after}")

#!/usr/bin/env python3
"""The session on the site: a summary block on each results page and the full log as session.html.

usage: session_page.py [PMC... ]      (no argument: every paper with a results page)

Each paper's session/ folder (written by the paper2repro skill's session ledger) holds ledger.json and
conversation.md. For a paper with one, this adds a "The session" block to site/PMC…/index.html with
four numbers from ledger.json and a link to site/PMC…/session.html, which it renders from
conversation.md (each turn's tool calls folded). A paper without one gets the block saying
"Session not recorded".

The paper pipelines call with_session() from build_page.py, so a rebuilt page keeps the block; run
this script to refresh the published pages without rerunning a pipeline. Both ways give the same
output, and running it twice changes nothing.
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = "https://github.com/jeonglab-bcm/fossil"
START, END = "<!-- session:start -->", "<!-- session:end -->"
esc = html.escape


def load_ledger(paper_dir):
    f = Path(paper_dir) / "session" / "ledger.json"
    return json.loads(f.read_text()) if f.is_file() else None


def has_log(paper_dir):
    return (Path(paper_dir) / "session" / "conversation.md").is_file()


# ---------- numbers ----------

def fmt_minutes(m):
    if m < 120:
        return f"{m:.0f} min"
    if m < 48 * 60:
        return f"{m / 60:.1f} h"
    return f"{m / 1440:.1f} days"


def fmt_tokens(n):
    if n >= 1e6:
        return f"{n / 1e6:.1f} M"
    if n >= 1e3:
        return f"{n / 1e3:.0f} k"
    return str(n)


def stats(led):
    sub = led.get("subagents") or {}
    tools, sub_tools = led.get("tool_calls", 0), sub.get("tool_calls", 0)
    total = (led.get("tokens_all") or {}).get("total") or led["tokens"]["total"]
    return [
        ("Wall clock", fmt_minutes(led["wall_clock_minutes"]), "first message to last, waits included"),
        ("Human prompts", f"{led['human_prompts']:,}", "messages typed by a person"),
        ("Tool calls", f"{tools + sub_tools:,}", f"{sub_tools:,} of them in subagents" if sub_tools else "none in subagents"),
        ("Tokens", fmt_tokens(total), "every request, subagents included"),
    ]


def stats_dl(led):
    rows = "".join(f'<div><dt>{esc(k)}</dt><dd class="num">{esc(v)}</dd><dd class="note">{esc(n)}</dd></div>'
                   for k, v, n in stats(led))
    return f'<dl class="session-stats">{rows}</dl>'


# ---------- the block on the results page ----------

def block(paper_dir):
    paper = Path(paper_dir).name
    led = load_ledger(paper_dir)
    if led and has_log(paper_dir):
        body = (f'<p>The reproduction was done by an AI agent, Claude Code, in one session. '
                f'Every prompt, reply and tool call of it is published.</p>{stats_dl(led)}'
                f'<p class="session-go"><a class="btn btn--primary" href="session.html">Read the session</a> '
                f'<a href="{REPO}/tree/main/{paper}/session">The raw files</a></p>')
    else:
        body = '<p class="session-none">Session not recorded: no log of the agent session was kept for this reproduction.</p>'
    return (f'{START}<section class="session-sum" aria-labelledby="session-head"><div class="container">'
            f'<div class="session-card surface"><h2 id="session-head">The session</h2>{body}</div></div></section>{END}')


def inject(page, paper_dir):
    """Put the block at the end of <main>, replacing one already there."""
    page = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\n?", "", page, flags=re.S)
    i = page.rfind("</main>")
    if i < 0:
        raise ValueError("no </main> in the page")
    return page[:i] + block(paper_dir) + "\n" + page[i:]


# ---------- Markdown, the subset conversation.md uses ----------

def inline(s):
    """Code spans become placeholders first, so bold and links can wrap them."""
    codes = []

    def keep(m):
        codes.append(f"<code>{esc(m.group(1))}</code>")
        return f"\x00{len(codes) - 1}\x00"

    s = inline_text(re.sub(r"`([^`]+)`", keep, s))
    return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], s)


def inline_text(s):
    s = esc(s, quote=False)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', s)
    s = re.sub(r'(?<!["=>])(https?://(?:(?!&lt;|&gt;)[^\s<"\x00])+?)(?=[.,;:)]?(?:\s|$|&lt;|&gt;|<|"|\x00))', r'<a href="\1">\1</a>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
    return s


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def markdown(lines):
    """Blocks: fenced code, tables, bullet and numbered lists, headings, paragraphs."""
    out, i, n = [], 0, len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
        elif line.startswith("```"):
            j = i + 1
            while j < n and not lines[j].startswith("```"):
                j += 1
            out.append(f"<pre><code>{esc(chr(10).join(lines[i + 1:j]))}</code></pre>")
            i = j + 1
        elif line.lstrip().startswith("|") and i + 1 < n and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            head = "".join(f"<th>{inline(c)}</th>" for c in cells(line))
            j, rows = i + 2, []
            while j < n and lines[j].lstrip().startswith("|"):
                rows.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells(lines[j])) + "</tr>")
                j += 1
            out.append(f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')
            i = j
        elif re.match(r"^#{1,6} ", line):
            level = min(len(line) - len(line.lstrip("#")) + 2, 6)
            out.append(f"<h{level}>{inline(line.lstrip('#').strip())}</h{level}>")
            i += 1
        elif re.match(r"^\s*([-*]|\d+\.) ", line):
            ordered = bool(re.match(r"^\s*\d+\. ", line))
            items, j = [], i
            while j < n and lines[j].strip():
                if re.match(r"^\s*([-*]|\d+\.) ", lines[j]):
                    items.append(re.sub(r"^\s*([-*]|\d+\.) ", "", lines[j]))
                else:
                    items[-1] += " " + lines[j].strip()
                j += 1
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{inline(t)}</li>" for t in items) + f"</{tag}>")
            i = j
        else:
            j = i
            while j < n and lines[j].strip() and not lines[j].startswith("```") and not re.match(r"^(#{1,6} |\s*([-*]|\d+\.) |\s*\|)", lines[j]):
                j += 1
            j = max(j, i + 1)
            out.append("<p>" + "<br>".join(inline(l) for l in lines[i:j]) + "</p>")
            i = j
    return "".join(out)


# ---------- the session page ----------

TURN = re.compile(r"^### (User \(sent mid-turn\)|User|Claude|System notification) · (.+)$")
ROLE = {"User": ("user", "User"), "User (sent mid-turn)": ("user", "User, sent mid-turn"),
        "Claude": ("claude", "Claude"), "System notification": ("system", "System notification")}


def turn_html(role, when, lines, tool_names):
    """A turn's text as Markdown; each run of tool-call lines folded into one <details>."""
    tool = re.compile(r"^- `(" + "|".join(re.escape(t) for t in sorted(tool_names, key=len, reverse=True)) + r")` ?(.*)$") if tool_names else None
    parts, text, calls = [], [], []

    def flush_text():
        if any(l.strip() for l in text):
            parts.append(markdown(text))
        text.clear()

    def flush_calls():
        if calls:
            items = "".join(f'<li><span class="tool-name">{esc(t)}</span> <code>{esc(a)}</code></li>' if a
                            else f'<li><span class="tool-name">{esc(t)}</span></li>' for t, a in calls)
            label = f"{len(calls)} tool call" + ("s" if len(calls) > 1 else "")
            parts.append(f'<details class="tools"><summary>{label}</summary><ul>{items}</ul></details>')
        calls.clear()

    for line in lines:
        m = tool.match(line) if tool else None
        if m:
            flush_text()
            calls.append((m.group(1), m.group(2).strip()))
        elif not line.strip() and calls:
            continue
        else:
            flush_calls()
            text.append(line)
    flush_text()
    flush_calls()
    cls, label = ROLE[role]
    return (f'<article class="turn turn--{cls}"><header><span class="who">{esc(label)}</span> '
            f'<time class="mono">{esc(when)} UTC</time></header>{"".join(parts)}</article>')


def conversation_html(md, tool_names):
    lines = md.splitlines()
    try:
        start = next(i for i, l in enumerate(lines) if l.startswith("### ") or l.startswith("## "))
    except StopIteration:
        return ""
    out, role, when, buf = [], None, None, []

    def flush():
        if role:
            out.append(turn_html(role, when, buf, tool_names))

    for line in lines[start:]:
        m = TURN.match(line)
        if m:
            flush()
            role, when, buf = m.group(1), m.group(2).strip(), []
        elif line.startswith("## ") and not line.startswith("### "):
            flush()
            role, buf = None, []
            title = line[3:].strip()
            if title != "Conversation":
                out.append(f'<h2 class="part">{inline(title)}</h2>')
        elif role:
            buf.append(line)
    flush()
    return "".join(out)


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>The Session · {paper}</title>
<meta name="description" content="The full log of the Claude Code session that reproduced {paper}: every prompt, reply and tool call.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Schibsted+Grotesk:wght@700&family=Instrument+Sans:wght@400;500&family=DM+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="../results.css">
</head>
<body>
<header class="topbar">
  <div class="container">
    <a class="wordmark" href="../" aria-label="fossil, home">fossil</a>
    <nav aria-label="Site"><a href="./">The results</a><a href="../#papers">The papers</a><a href="{repo}/tree/main/{paper}">The code</a></nav>
  </div>
</header>

<main class="session-page">
  <section class="session-hero" aria-labelledby="hero-head"><div class="container">
    <p class="eyebrow mono">{paper} · session {sid}</p>
    <h1 id="hero-head">The session</h1>
    <p class="lead">The Claude Code session that reproduced {paper}, from its first prompt to its last. Each turn's tool calls are folded; open one to see the commands, shortened as the ledger keeps them.</p>
    {stats}
    <p class="session-go"><a href="{repo}/blob/main/{paper}/session/conversation.md">conversation.md</a> <a href="{repo}/blob/main/{paper}/session/ledger.json">ledger.json</a></p>
  </div></section>
  <section class="container session-log" aria-label="Conversation">
    {log}
  </section>
</main>

<footer class="foot">
  <div class="container">
    <p class="statement">One session, every turn of it.</p>
    <nav class="links" aria-label="Footer">
      <a href="./">The results</a>
      <a href="{repo}/tree/main/{paper}/session">The raw files</a>
      <a href="../">All papers</a>
    </nav>
  </div>
</footer>
</body>
</html>
"""


def session_page(paper_dir):
    paper_dir = Path(paper_dir)
    led = load_ledger(paper_dir)
    md = (paper_dir / "session" / "conversation.md").read_text()
    log = conversation_html(md, set(led.get("tool_calls_by_name", {})))
    return PAGE.format(paper=esc(paper_dir.name), sid=esc(led.get("session_id", "")), repo=REPO,
                       stats=stats_dl(led), log=log)


def with_session(page, paper_dir, out_file):
    """For build_page.py: add the block to the page and write session.html next to out_file."""
    paper_dir = Path(paper_dir)
    if load_ledger(paper_dir) and has_log(paper_dir):
        (Path(out_file).parent / "session.html").write_text(session_page(paper_dir))
    return inject(page, paper_dir)


def main(papers):
    if not papers:
        papers = sorted(p.parent.name for p in (ROOT / "site").glob("PMC*/index.html"))
    for paper in papers:
        index = ROOT / "site" / paper / "index.html"
        index.write_text(with_session(index.read_text(), ROOT / paper, index))
        print(paper, "session" if has_log(ROOT / paper) else "not recorded")


if __name__ == "__main__":
    main(sys.argv[1:])

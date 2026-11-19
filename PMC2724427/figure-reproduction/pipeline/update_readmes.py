"""Write the results table (check_results.py --markdown on ../results.json) into the READMEs.

  update_readmes.py PAPER_DIR

PAPER_DIR/README.md gets the summary line and a short table (item, verdict, measure) between
<!--RESULTS-SUMMARY--> markers; figure-reproduction/README.md gets the full table (with the causes)
between <!--RESULTS-TABLE--> markers. Run it after results.json changes; never edit those parts by hand.
"""
import re
import subprocess
import sys
from pathlib import Path

paper = Path(sys.argv[1])
# The words after the counts in the top-level README's status cell (plain facts from results.json).
STATUS_NOTE = (Path(__file__).resolve().parent.parent / "status_note.txt").read_text().strip() \
    if (Path(__file__).resolve().parent.parent / "status_note.txt").exists() else "the simulation rebuilt as `logitbias`"
here = Path(__file__).resolve().parent
r = subprocess.run([sys.executable, here / "check_results.py", paper / "results.json", "--markdown", "--root", paper],
                   capture_output=True, text=True, check=True)
lines = [l for l in r.stdout.splitlines() if l.startswith("|")]
summary = [l for l in r.stdout.splitlines() if l and not l.startswith("|") and not l.startswith("OK ")][-1]
short = []
for l in lines:
    cells = [c.strip() for c in l.strip("|").split("|")]
    short.append("| " + " | ".join(cells[:3]) + " |")


def put(path, tag, body):
    s = path.read_text()
    new = re.sub(rf"<!--{tag}-->.*?<!--/{tag}-->", f"<!--{tag}-->\n{body}\n<!--/{tag}-->", s, flags=re.S)
    path.write_text(new)


put(paper / "README.md", "RESULTS-SUMMARY", summary + "\n\n" + "\n".join(short))
put(paper / "figure-reproduction" / "README.md", "RESULTS-TABLE", summary + "\n\n" + "\n".join(lines))
print("READMEs updated:", summary)

# Status cell of the paper's row in the repository README, from the same summary
top = paper.parent / "README.md"
if top.exists():
    s = top.read_text()
    status = summary.rstrip(".") + " (`results.json`): " + STATUS_NOTE
    tag = f"{paper.name}-STATUS"
    top.write_text(re.sub(rf"<!--{tag}-->.*?<!--/{tag}-->", f"<!--{tag}-->{status}<!--/{tag}-->", s, flags=re.S))

# The one-line verdict on the claims, from results_notes.json, under the results of both READMEs
import json  # noqa: E402

line = json.loads((paper / "figure-reproduction" / "results_notes.json").read_text())["page"]["claims_line"]
for path in (paper / "README.md", paper / "figure-reproduction" / "README.md"):
    s = path.read_text()
    block = "<!--CLAIMS-LINE-->\n" + line + "\n<!--/CLAIMS-LINE-->"
    if "<!--/CLAIMS-LINE-->" in s:
        s = re.sub(r"<!--CLAIMS-LINE-->.*?<!--/CLAIMS-LINE-->", lambda m: block, s, count=1, flags=re.S)
    else:
        s = s.replace("<!--CLAIMS-LINE-->", block, 1)
    path.write_text(s)

# The front page's verdict cell for this paper, from results.json: the paper's core results are
# Table 1, Fig. 1 and the claim that the bias points away from zero. All of them agreeing gives
# "agrees", none of them "differs", anything else "partly". Written between the markers of the
# paper's row in site/index.html.
R = json.loads((paper / "results.json").read_text())
CORE = ["table1.continuous", "table1.discrete", "fig1.continuous", "fig1.discrete", "text.away_from_null"]
vs = [i["verdict"] for i in R["items"] if i["id"] in CORE]
ok = [v in ("exact", "agrees") for v in vs]
v = "agrees" if all(ok) else ("differs" if all(x == "differs" for x in vs) else "partly")
WORD = {"agrees": "Agrees", "partly": "Partly agrees", "differs": "Differs"}
ICON = {"agrees": '<svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="8.6" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M6 10.4l2.7 2.7L14.2 7.4" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/></svg>',
        "partly": '<svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="8.6" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M10 1.4A8.6 8.6 0 0 0 10 18.6Z" fill="currentColor"/></svg>',
        "differs": '<svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="8.6" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>'}
note = json.loads((paper / "figure-reproduction" / "results_notes.json").read_text())["page"].get("front_note", "")
site = paper.parent / "site" / "index.html"
if site.exists():
    s = site.read_text()
    tag = f"{paper.name}-VERDICT"
    cell = (f'<span class="verdict" data-v="{v}">{WORD[v]}{ICON[v]}</span>'
            + (f'<span class="verdict-note">{note}</span>' if note else ""))
    site.write_text(re.sub(rf"<!--{tag}-->.*?<!--/{tag}-->", f"<!--{tag}-->{cell}<!--/{tag}-->", s, flags=re.S))
    print("front page verdict:", v)

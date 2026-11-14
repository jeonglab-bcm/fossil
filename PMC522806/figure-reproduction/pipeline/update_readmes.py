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
    if (Path(__file__).resolve().parent.parent / "status_note.txt").exists() else "the method rebuilt as `cfsenn`"
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
    s = re.sub(r"<!--CLAIMS-LINE-->.*?(<!--/CLAIMS-LINE-->|$)", "<!--CLAIMS-LINE-->\n" + line + "\n<!--/CLAIMS-LINE-->", s, count=1, flags=re.S | re.M)
    path.write_text(s)

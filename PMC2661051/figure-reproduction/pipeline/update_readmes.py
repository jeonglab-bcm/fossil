#!/usr/bin/env python3
"""Write the results table (check_results.py --markdown on ../results.json) into the READMEs, and
the paper's status into the repository README and the front page.

  update_readmes.py PAPER_DIR

PAPER_DIR/README.md gets the summary line and a short table (item, verdict, measure) between
<!--RESULTS-SUMMARY--> markers; figure-reproduction/README.md gets the full table (with the causes)
between <!--RESULTS-TABLE--> markers; the repository README's row gets the summary and
results_notes.json's "status_note" between <!--PMC…-STATUS--> markers; site/index.html's row gets
the verdict stamp (agrees when every attempted item is exact or agrees, partly otherwise) between
<!--PMC…-VERDICT--> markers. Run it after results.json changes; never edit those parts by hand.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

paper = Path(sys.argv[1]).resolve()
here = Path(__file__).resolve().parent
r = subprocess.run([sys.executable, here / "check_results.py", paper / "results.json", "--markdown", "--root", paper],
                   capture_output=True, text=True, check=True)
lines = [l for l in r.stdout.splitlines() if l.startswith("|")]
summary = [l for l in r.stdout.splitlines() if l and not l.startswith("|") and not l.startswith("OK ")][-1]
short = ["| " + " | ".join([c.strip() for c in l.strip("|").split("|")][:3]) + " |" for l in lines]


def put(path, tag, body, sep="\n"):
    s = path.read_text()
    new, n = re.subn(rf"<!--{tag}-->.*?<!--/{tag}-->", f"<!--{tag}-->{sep}{body}{sep}<!--/{tag}-->", s, flags=re.S)
    if n != 1:
        raise SystemExit(f"{path}: marker {tag} found {n} times")
    path.write_text(new)


put(paper / "README.md", "RESULTS-SUMMARY", summary + "\n\n" + "\n".join(short))
put(paper / "figure-reproduction" / "README.md", "RESULTS-TABLE", summary + "\n\n" + "\n".join(lines))
notes = json.load(open(paper / "figure-reproduction" / "results_notes.json"))
res = json.load(open(paper / "results.json"))
sm = res["summary"]
status = (f"{sm['exact']} exact, {sm['agrees']} agree, {sm['partly']} partly, {sm['inconclusive']} inconclusive, "
          f"{sm['differs']} differ, {sm['not_attempted']} not attempted (`results.json`): {notes['status_note']}")
put(paper.parent / "README.md", f"{paper.name}-STATUS", status, sep="")
attempted = [i["verdict"] for i in res["items"] if i["verdict"] != "not_attempted"]
v = "agrees" if all(x in ("exact", "agrees") for x in attempted) else "partly"
icon = {"agrees": '<svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="8.6" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M6 10.4l2.7 2.7L14.2 7.4" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/></svg>',
        "partly": '<svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="8.6" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M10 1.4A8.6 8.6 0 0 0 10 18.6Z" fill="currentColor"/></svg>'}[v]
word = {"agrees": "Agrees", "partly": "Partly agrees"}[v]
put(paper.parent / "site" / "index.html", f"{paper.name}-VERDICT",
    f'<span class="verdict" data-v="{v}">{word}{icon}</span><span class="verdict-note">{notes["site_note"]}</span>', sep="")
print("READMEs and front page updated:", summary)

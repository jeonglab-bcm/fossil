"""Write the results tables (check_results.py --markdown on ../results.json) into the READMEs.

Usage: update_readmes.py PAPER_DIR

PAPER_DIR/README.md gets the summary line and a short table (item, verdict, measure) between
<!--RESULTS-SUMMARY--> markers; figure-reproduction/README.md gets the full table (with the causes)
between <!--RESULTS-TABLE--> markers; package/README.md gets the checks between <!--CHECKS--> markers; the
repository README gets the paper's status between <!--PMC1955447-STATUS--> markers. Every number comes from
results.json or the committed outputs. Run it after results.json changes; never edit those parts by hand.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

paper = Path(sys.argv[1]).resolve()
here = Path(__file__).resolve().parent
sys.path.insert(0, str(here))
from build_results import facts_of  # noqa: E402
from build_page import main_verdict  # noqa: E402

r = subprocess.run([sys.executable, here / "check_results.py", paper / "results.json", "--markdown", "--root", paper],
                   capture_output=True, text=True, check=True)
lines = [l for l in r.stdout.splitlines() if l.startswith("|")]
summary = [l for l in r.stdout.splitlines() if l and not l.startswith("|") and not l.startswith("OK ")][-1]
short = ["| " + " | ".join([c.strip() for c in l.strip("|").split("|")][:3]) + " |" for l in lines]


def put(path, tag, body, inline=False):
    s = path.read_text()
    sep = "" if inline else "\n"
    new, n = re.subn(rf"<!--{tag}-->.*?<!--/{tag}-->", lambda m: f"<!--{tag}-->{sep}{body}{sep}<!--/{tag}-->", s, flags=re.S)
    if n != 1:
        raise SystemExit(f"{path}: no <!--{tag}--> markers")
    path.write_text(new)


R = json.load(open(paper / "results.json"))
F = facts_of(paper / "figure-reproduction" / "output")
sm = R["summary"]
mv = main_verdict(R)
N = json.load(open(paper / "figure-reproduction" / "results_notes.json"))
from build_results import fill  # noqa: E402
facts = {**F, **sm, "main_verdict": mv}
claim_line = fill(N["page"]["claims_line"], facts)
put(paper / "README.md", "RESULTS-SUMMARY", summary + "\n\n" + "\n".join(short))
put(paper / "figure-reproduction" / "README.md", "RESULTS-TABLE", summary + "\n\n" + "\n".join(lines))
put(paper / "figure-reproduction" / "README.md", "CLAIMS-LINE", claim_line)
put(paper / "README.md", "CLAIMS-LINE", claim_line)
put(paper / "figure-reproduction" / "README.md", "DETAILS", fill(N["readme"]["details"], facts).strip())
put(paper / "README.md", "SUMMARY-PROSE", fill(N["readme"]["summary_prose"], facts).strip())
put(paper / "package" / "README.md", "CHECKS", fill(N["readme"]["package_checks"], facts), inline=True)
status = (f"{sm['exact']} exact, {sm['agrees']} agree, {sm['partly']} partly, {sm['differs']} differ, {sm['not_attempted']} not attempted "
          f"(`results.json`): " + fill(N["readme"]["status"], facts) + f"; main claim {mv}")
put(paper.parent / "README.md", f"{paper.name}-STATUS", status, inline=True)

# The front page's stamp: agrees when every attempted item is exact or agrees, partly otherwise.
att = [i["verdict"] for i in R["items"] if i["verdict"] != "not_attempted"]
v = "agrees" if all(x in ("exact", "agrees") for x in att) else "partly"
icon = {"agrees": '<svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="8.6" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M6 10.4l2.7 2.7L14.2 7.4" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/></svg>',
        "partly": '<svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="8.6" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M10 1.4A8.6 8.6 0 0 0 10 18.6Z" fill="currentColor"/></svg>'}[v]
word = {"agrees": "Agrees", "partly": "Partly agrees"}[v]
note = fill(N["readme"]["front_note"], facts)
put(paper.parent / "site" / "index.html", f"{paper.name}-VERDICT",
    f'<span class="verdict" data-v="{v}">{word}{icon}</span><span class="verdict-note">{note}</span>', inline=True)
print("READMEs updated:", summary)

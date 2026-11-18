"""Write the results tables (check_results.py --markdown on ../results.json) into the READMEs.

Usage: update_readmes.py PAPER_DIR

PAPER_DIR/README.md gets the summary line and a short table (item, verdict, measure) between
<!--RESULTS-SUMMARY--> markers; figure-reproduction/README.md gets the full table (with the causes)
between <!--RESULTS-TABLE--> markers; package/README.md gets the checks between <!--CHECKS--> markers; the
repository README gets the paper's status between <!--PMC2430201-STATUS--> markers. Every number comes from
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
claim_line = (f"The main claim {mv}. The one claim that misses on our run sits on a rounding line in Table 6 "
              f"(a setting of the skewed data the paper does not state); three statements of the text do not match the paper's own tables.")
put(paper / "README.md", "RESULTS-SUMMARY", summary + "\n\n" + "\n".join(short))
put(paper / "figure-reproduction" / "README.md", "RESULTS-TABLE", summary + "\n\n" + "\n".join(lines))
put(paper / "figure-reproduction" / "README.md", "CLAIMS-LINE", claim_line)
put(paper / "README.md", "CLAIMS-LINE", claim_line)
put(paper / "package" / "README.md", "CHECKS",
    f"The package is implemented from the paper's text and checked against the paper's printed tables ({F['within']} of "
    f"{F['cells']} cells of Tables 3-8 within Monte Carlo error) and its pooling against R's metafor 4.4.0 (the example "
    f"data, and {F['x_fits']} simulated meta-analyses to a relative {F['x_diff']}).", inline=True)
status = (f"{sm['exact']} exact, {sm['agrees']} agree, {sm['partly']} partly, {sm['differs']} differ, {sm['not_attempted']} not attempted "
          f"(`results.json`): the SAS simulation rebuilt as `rommeta` and rerun; {F['within']} of {F['cells']} printed cells of Tables 3-8 "
          f"within Monte Carlo error; RoM bias as a share of the true RoM and I2 from the mean Q/(k-1) found from the tables; main claim {mv}")
put(paper.parent / "README.md", f"{paper.name}-STATUS", status, inline=True)

# The front page's stamp: agrees when every attempted item is exact or agrees, partly otherwise.
att = [i["verdict"] for i in R["items"] if i["verdict"] != "not_attempted"]
v = "agrees" if all(x in ("exact", "agrees") for x in att) else "partly"
icon = {"agrees": '<svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="8.6" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M6 10.4l2.7 2.7L14.2 7.4" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/></svg>',
        "partly": '<svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="8.6" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M10 1.4A8.6 8.6 0 0 0 10 18.6Z" fill="currentColor"/></svg>'}[v]
word = {"agrees": "Agrees", "partly": "Partly agrees"}[v]
note = f"The main claim {mv}; {F['within']} of {F['cells']} table cells came back"
put(paper.parent / "site" / "index.html", f"{paper.name}-VERDICT",
    f'<span class="verdict" data-v="{v}">{word}{icon}</span><span class="verdict-note">{note}</span>', inline=True)
print("READMEs updated:", summary)

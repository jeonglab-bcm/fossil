#!/usr/bin/env python3
"""Write the results table (check_results.py --markdown on ../results.json) into the READMEs, and
the paper's verdict into the front page.

  update_readmes.py PAPER_DIR

PAPER_DIR/README.md gets the summary line and a short table (item, verdict, measure) between
<!--RESULTS-SUMMARY--> markers; figure-reproduction/README.md gets the full table (with the causes)
between <!--RESULTS-TABLE--> markers; PMC…/index.json gets the front page's verdict (agrees when every
attempted item is exact or agrees, partly otherwise). Run it after results.json changes; never edit those parts by hand.
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
attempted = [i["verdict"] for i in res["items"] if i["verdict"] != "not_attempted"]
v = "agrees" if all(x in ("exact", "agrees") for x in attempted) else "partly"
sys.path.insert(0, str(paper.parent / "tools"))
from build_index import set_fields  # noqa: E402

set_fields(paper.name, verdict={"v": v, "note": notes["site_note"]})  # the front page is built from it
print("READMEs and front page updated:", summary)

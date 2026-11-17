"""Write the results tables (check_results.py --markdown on ../results.json) into the READMEs.

Usage: update_readmes.py PAPER_DIR

PAPER_DIR/README.md gets the summary line and a short table (item, verdict, measure) between
<!--RESULTS-SUMMARY--> markers; figure-reproduction/README.md gets the full table (with the causes)
between <!--RESULTS-TABLE--> markers; the repository README gets the paper's status between
<!--PMC3098087-STATUS--> markers. Every number comes from results.json. Run it after results.json
changes; never edit those parts by hand.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

paper = Path(sys.argv[1]).resolve()
here = Path(__file__).resolve().parent
sys.path.insert(0, str(here))
from check_results import field_matches  # noqa: E402

r = subprocess.run([sys.executable, here / "check_results.py", paper / "results.json", "--markdown", "--root", paper],
                   capture_output=True, text=True, check=True)
lines = [ln for ln in r.stdout.splitlines() if ln.startswith("|")]
summary = [ln for ln in r.stdout.splitlines() if ln and not ln.startswith("|") and not ln.startswith("OK ")][-1]
short = ["| " + " | ".join([c.strip() for c in ln.strip("|").split("|")][:3]) + " |" for ln in lines]


def put(path, tag, body, inline=False):
    s = path.read_text()
    sep = "" if inline else "\n"
    new, n = re.subn(rf"<!--{tag}-->.*?<!--/{tag}-->", lambda m: f"<!--{tag}-->{sep}{body}{sep}<!--/{tag}-->", s, flags=re.S)
    if n != 1:
        raise SystemExit(f"{path}: no <!--{tag}--> markers")
    path.write_text(new)


put(paper / "README.md", "RESULTS-SUMMARY", summary + "\n\n" + "\n".join(short))
put(paper / "figure-reproduction" / "README.md", "RESULTS-TABLE", summary + "\n\n" + "\n".join(lines))

R = json.load(open(paper / "results.json"))
by = {i["id"]: i for i in R["items"]}


def hits(i):
    v = by[i]["values"]
    exc = {e["field"] for e in v.get("exceptions", [])}
    f = [x for x in v["fields"] if x["name"] not in exc]
    return sum(field_matches(x, v.get("tolerance")) for x in f), len(f)


sm = R["summary"]
parts = [f"{sm[k]} {k.replace('_', ' ')}" for k in ("exact", "agrees", "partly", "inconclusive", "differs", "not_attempted") if sm.get(k)]
figs = [hits(i) for i in ("fig1", "fig2", "fig3", "fig4", "fig5", "fig6")]
tabs = {t: hits(t) for t in ("af1", "af3", "af13", "af14")}
status = (", ".join(parts) + " (`results.json`): the lost R simulation and breast cancer analysis rebuilt as `multds` and rerun; "
          f"{sum(h for h, _ in figs)} of {sum(n for _, n in figs)} plotted points of Figs 1-6 and "
          f"{sum(h for h, _ in tabs.values())} of {sum(n for _, n in tabs.values())} cells of Additional files 1, 3, 13 and 14 within Monte Carlo error; "
          "Additional file 1 prints PLR's accuracies for every classifier")
put(paper.parent / "README.md", f"{paper.name}-STATUS", status, inline=True)
print("READMEs updated:", summary)

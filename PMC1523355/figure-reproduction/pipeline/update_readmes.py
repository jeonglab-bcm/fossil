"""Write the results tables (check_results.py --markdown on ../results.json) into the READMEs.

Usage: update_readmes.py PAPER_DIR

PAPER_DIR/README.md gets the summary line and a short table (item, verdict, measure) between
<!--RESULTS-SUMMARY--> markers; figure-reproduction/README.md gets the full table (with the causes)
between <!--RESULTS-TABLE--> markers; the repository README gets the paper's status between
<!--PMC1523355-STATUS--> markers. Every number comes from results.json. Run it after results.json
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


put(paper / "README.md", "RESULTS-SUMMARY", summary + "\n\n" + "\n".join(short))
put(paper / "figure-reproduction" / "README.md", "RESULTS-TABLE", summary + "\n\n" + "\n".join(lines))

R = json.load(open(paper / "results.json"))
by = {i["id"]: i for i in R["items"]}


def hits(i):
    v = by[i]["values"]
    return sum(field_matches(x, v.get("tolerance")) for x in v["fields"]), len(v["fields"])


sm = R["summary"]
parts = [f"{sm[k]} {k.replace('_', ' ')}" for k in ("exact", "agrees", "partly", "inconclusive", "differs", "not_attempted") if sm.get(k)]
h1, n1 = hits("table1.power")
pw = [hits(t) for t in ("table2", "table3", "table4", "table5", "fig1b")]
status = (", ".join(parts) + f"; {sm['open_causes']} open causes (`results.json`): the lost simulation rebuilt as `stratpower` "
          f"and every setting rerun; Fig. 1A on the published axes; Table 1's powers and AUROC {h1} of {n1}; "
          f"Tables 2-5 and Fig. 1B {sum(h for h, _ in pw)} of {sum(n for _, n in pw)} values within tolerance, "
          f"most misses higher than the paper's; main claim holds")
put(paper.parent / "README.md", f"{paper.name}-STATUS", status, inline=True)
print("READMEs updated:", summary)

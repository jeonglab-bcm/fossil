"""Write the results tables (check_results.py --markdown on ../results.json) into the READMEs.

Usage: update_readmes.py PAPER_DIR

PAPER_DIR/README.md gets the summary line and a short table (item, verdict, measure) between
<!--RESULTS-SUMMARY--> markers; figure-reproduction/README.md gets the full table (with the causes)
between <!--RESULTS-TABLE--> markers; the repository README gets the paper's status between
<!--PMC3022898-STATUS--> markers. Every number comes from results.json or the committed outputs.
Run it after results.json changes; never edit those parts by hand.
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

r = subprocess.run([sys.executable, here / "check_results.py", paper / "results.json", "--markdown", "--root", paper],
                   capture_output=True, text=True, check=True)
lines = [l for l in r.stdout.splitlines() if l.startswith("|")]
summary = [l for l in r.stdout.splitlines() if l and not l.startswith("|") and not l.startswith("OK ")][-1]
short = ["| " + " | ".join([c.strip() for c in l.strip("|").split("|")][:3]) + " |" for l in lines]


def put(path, tag, body, inline=False):
    s = path.read_text()
    sep = "" if inline else "\n"
    new, n = re.subn(rf"<!--{tag}-->.*?<!--/{tag}-->", f"<!--{tag}-->{sep}{body}{sep}<!--/{tag}-->", s, flags=re.S)
    if n != 1:
        raise SystemExit(f"{path}: no <!--{tag}--> markers")
    path.write_text(new)


put(paper / "README.md", "RESULTS-SUMMARY", summary + "\n\n" + "\n".join(short))
put(paper / "figure-reproduction" / "README.md", "RESULTS-TABLE", summary + "\n\n" + "\n".join(lines))

R = json.load(open(paper / "results.json"))
by = {i["id"]: i for i in R["items"]}
F = facts_of(paper / "figure-reproduction" / "output")


def hits(i):
    from check_results import field_matches
    f = by[i]["values"]["fields"]
    return sum(field_matches(x, by[i]["values"].get("tolerance")) for x in f), len(f)


s1 = [hits(t) for t in ("tableS1", "tableS2", "tableS3", "tableS4", "tableS5", "tableS7")]
sm = R["summary"]
status = (f"{sm['agrees']} agree, {sm['partly']} partly, {sm['differs']} differs, {sm['not_attempted']} not attempted (`results.json`): "
          f"the SAS simulation rebuilt as `esrisk` and rerun; Tables S1-S5 and S7 {min(h for h, _ in s1)} to {max(h for h, _ in s1)} "
          f"of 112 cells within Monte Carlo error; Table S6 and the ESR_R log bars of Figs 1-4 behave as if eq. 10's first "
          f"term were left out ({F['s6_nofirst_within']} of 112 cells and {F['bars_nofirst_within']} of {F['bars']} bars without it, "
          f"{F['s6_within']} cells with it)")
put(paper.parent / "README.md", f"{paper.name}-STATUS", status, inline=True)
print("READMEs updated:", summary)

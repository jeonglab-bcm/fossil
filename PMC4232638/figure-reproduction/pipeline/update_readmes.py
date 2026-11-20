"""Write the results tables (check_results.py --markdown on ../results.json) into the READMEs.

Usage: update_readmes.py PAPER_DIR

PAPER_DIR/README.md gets the summary line and a short table (item, verdict, measure) between
<!--RESULTS-SUMMARY--> markers; figure-reproduction/README.md gets the full table (with the causes)
between <!--RESULTS-TABLE--> markers; the repository README gets the paper's status between
<!--PMC4232638-STATUS--> markers. Every number comes from results.json or the committed outputs.
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
    f = by[i]["values"]["fields"]
    exc = {e["field"] for e in by[i]["values"].get("exceptions", [])}
    f = [x for x in f if x["name"] not in exc]
    return sum(field_matches(x, by[i]["values"].get("tolerance")) for x in f), len(f)


sm = R["summary"]
kappa = [hits(k) for k in ("af3", "af5", "af11", "af13")]
c = json.load(open(paper / "figure-reproduction" / "output" / "comparison.json"))
status = (f"{sm['exact']} exact, {sm['agrees']} agree, {sm['partly']} partly, {sm['differs']} {'differs' if sm['differs'] == 1 else 'differ'}, "
          f"{sm['not_attempted']} not attempted (`results.json`): the lost statistics rebuilt as `mutbench` and rerun on the paper's spreadsheet; "
          f"every count of Tables 1 and 2 and every point value of Tables 3 and 4; {sum(h for h, _ in kappa):,} of {sum(n for _, n in kappa):,} kappa values "
          f"as printed; all {c['af17']['summary']['means']:,} combination means of Additional file 17 and of 18 within Monte Carlo error; "
          f"Figs 1 and 2 back; rankings of near ties (Figs 3 and 4) move with the random splits; main claim holds")
put(paper.parent / "README.md", f"{paper.name}-STATUS", status, inline=True)
print("READMEs updated:", summary)

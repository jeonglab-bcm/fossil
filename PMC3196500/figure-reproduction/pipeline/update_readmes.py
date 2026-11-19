"""Write the results tables (check_results.py --markdown on ../results.json) into the READMEs.

Usage: update_readmes.py PAPER_DIR

PAPER_DIR/README.md gets the summary line and a short table (item, verdict, measure) between
<!--RESULTS-SUMMARY--> markers; figure-reproduction/README.md gets the full table (with the causes)
between <!--RESULTS-TABLE--> markers; the repository README gets the paper's status between
<!--PMC3196500-STATUS--> markers. Every number comes from results.json or the committed outputs.
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
    new, n = re.subn(rf"<!--{tag}-->.*?<!--/{tag}-->", lambda m: f"<!--{tag}-->{sep}{body}{sep}<!--/{tag}-->", s, flags=re.S)
    if n != 1:
        raise SystemExit(f"{path}: no <!--{tag}--> markers")
    path.write_text(new)


put(paper / "README.md", "RESULTS-SUMMARY", summary + "\n\n" + "\n".join(short))
put(paper / "figure-reproduction" / "README.md", "RESULTS-TABLE", summary + "\n\n" + "\n".join(lines))

R = json.load(open(paper / "results.json"))
F = facts_of(paper / "figure-reproduction" / "output")
sm = R["summary"]
pix = [i for i in R["items"] if i["method"] == "pixels"]
pv = {v: sum(i["verdict"] == v for i in pix) for v in ("agrees", "partly", "inconclusive", "differs")}
status = (f"{sm['agrees']} agree, {sm['partly']} partly, {sm['inconclusive']} inconclusive, {sm['differs']} differ, "
          f"{sm['not_attempted']} not attempted (`results.json`): the lost simulation rebuilt as `oisim` and all 36 scenarios rerun; "
          f"Tables 1, S3 and S4 {F['table1_exact']}, {F['tableS3_exact']} and {F['tableS4_exact']} of 144 cells as printed "
          f"({F['table1_within_one_bin']}, {F['tableS3_within_one_bin']}, {F['tableS4_within_one_bin']} within one bin); "
          f"Table 2's OIS formula within one rounding step of {F['table2_within_one_step']} of 144 cells; "
          f"{len(pix)} figure panels: {pv['agrees']} agree, {pv['partly']} partly, {pv['inconclusive']} inconclusive, {pv['differs']} differ "
          f"(Figs S5-S7 are copies of S1-S3); main claim holds")
put(paper.parent / "README.md", f"{paper.name}-STATUS", status, inline=True)

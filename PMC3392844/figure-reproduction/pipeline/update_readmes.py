"""Write the results tables (check_results.py --markdown on ../results.json) into the READMEs.

Usage: update_readmes.py PAPER_DIR

PAPER_DIR/README.md gets the summary line and a short table (item, verdict, measure) between
<!--RESULTS-SUMMARY--> markers; figure-reproduction/README.md gets the full table (with the causes)
between <!--RESULTS-TABLE--> markers; the repository README gets the paper's status between
<!--PMC3392844-STATUS--> markers. Every number comes from results.json or the committed outputs.
Run it after results.json changes; never edit those parts by hand.
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
M = json.load(open(paper / "figure-reproduction" / "output" / "metrics.json"))
F = json.load(open(paper / "figure-reproduction" / "output" / "figures.json"))["figures"]
sm = R["summary"]
a, b = M["svm:chem"]["all"]["auc"], M["svm:chem+bio+pheno"]["all"]["auc"]
status = (f"{sm['exact']} exact, {sm['agrees']} agree, {sm['partly']} partly, {sm['differs']} differ, {sm['not_attempted']} not attempted (`results.json`): "
          f"the lost pipeline rebuilt as `adrfusion` and rerun on the authors' own training file and folds; Fig. 2's six ROC curves back "
          f"({100 * min(F['fig2']['published_near_ours'], F['fig2']['ours_near_published']):.0f}% of curve pixels within 2 px); "
          f"chem to chem+bio+pheno AUC {a:.4f} to {b:.4f} (paper 0.9054 to 0.9524); LR and naive Bayes rows differ (settings lost)")
sys.path.insert(0, str(here))
from build_page import main_claim_line  # noqa: E402

line = main_claim_line(M, R)
put(paper / "README.md", "CLAIMS-LINE", line, inline=True)
put(paper / "figure-reproduction" / "README.md", "CLAIMS-LINE", line, inline=True)
put(paper.parent / "README.md", f"{paper.name}-STATUS", status, inline=True)
print("READMEs updated:", summary)

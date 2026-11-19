"""Write the results tables (check_results.py --markdown on ../results.json) into the READMEs.

Usage: update_readmes.py PAPER_DIR

PAPER_DIR/README.md gets the summary line and a short table (item, verdict, measure) between
<!--RESULTS-SUMMARY--> markers; figure-reproduction/README.md gets the full table (with the causes)
between <!--RESULTS-TABLE--> markers; the repository README gets the paper's status between
<!--PMC4457112-STATUS--> markers. Every number comes from results.json or the committed outputs.
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
parts = [f"{sm[k]} {k.replace('_', ' ')}" for k in ("exact", "agrees", "partly", "inconclusive", "differs", "not_attempted") if sm.get(k)]
status = (", ".join(parts) + " (`results.json`): the RCT Tagger rebuilt as `rctconf` and retrained on the PubMed 2026 baseline "
          f"({F['dataset']} citations, {F['dataset_rct']} tagged RCT against the paper's 277,789); 2011 AUC "
          f"{F['m_auc11']} with MeSH and {F['c_auc11']} without (paper 0.973 and 0.966); "
          f"Tables 1-3 {F['table1_within'] + F['table2_within'] + F['table3_within']} of "
          f"{F['table1_fields'] + F['table2_fields'] + F['table3_fields'] - 8} values within 0.01, "
          f"{F['table1_printed'] + F['table2_printed'] + F['table3_printed']} at printed precision; Fig. 1 needs manual labels never released")
put(paper.parent / "README.md", f"{paper.name}-STATUS", status, inline=True)
print("READMEs updated:", summary)

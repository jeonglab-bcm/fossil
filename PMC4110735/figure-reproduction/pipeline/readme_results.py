"""Fill the Results sections of PMC4110735/README.md and figure-reproduction/README.md from results.json.

Usage: readme_results.py RESULTS_JSON   (run from the repository root after the pipeline)
Everything between <!--RESULTS--> and <!--/RESULTS--> is replaced: the summary line, the table that
check_results.py --markdown prints, and the claims line from results_notes.json.
"""
import json, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
res = sys.argv[1]
md = subprocess.run([sys.executable, str(HERE / "check_results.py"), res, "--markdown", "--skip-files"],
                    capture_output=True, text=True).stdout
table = "\n".join(l for l in md.splitlines() if l.startswith("|"))
summary = next(l for l in md.splitlines() if "exact" in l and l.rstrip().endswith("causes."))
R = json.loads(Path(res).read_text())
notes = json.loads((HERE.parent / "results_notes.json").read_text())
block = f"<!--RESULTS-->\n\n{R['summary']['items']} results. {summary}\n\n{table}\n\n{notes['page']['claims_line']}\n\n<!--/RESULTS-->"
for p in (HERE.parent.parent / "README.md", HERE.parent / "README.md"):
    s = p.read_text()
    s = re.sub(r"<!--RESULTS-->.*?<!--/RESULTS-->", block, s, flags=re.S) if "<!--/RESULTS-->" in s else s.replace("<!--RESULTS-->", block)
    p.write_text(s)
    print("wrote", p)

# the row in the repository's README table: counts from the summary
sm = R["summary"]
status = (f"{sm['exact']} exact, {sm['agrees']} agree, {sm['partly']} partly, {sm['differs']} differ, "
          f"{sm['not_attempted']} not attempted (`results.json`): Figs 2, 3 and 7 redrawn from public data; Fig. 4 draws "
          f"Table 2; GeCON rebuilt (`gecon`) ranks the DREAM pairs at chance, so the main claim does not hold; "
          f"GeneNetWeaver's simulation ported")
top = HERE.parent.parent.parent / "README.md"
s = top.read_text()
s = re.sub(r"(\| \[`PMC4110735`\]\(PMC4110735/\) \|[^\n]*\| )(<!--PMC4110735-status-->|[^|\n]*)( \|)", lambda m: m.group(1) + status + "<!--PMC4110735-status-->" + m.group(3), s)
top.write_text(s)
print("wrote", top)

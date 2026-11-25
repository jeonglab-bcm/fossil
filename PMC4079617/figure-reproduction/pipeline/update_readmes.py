"""Write the results tables (check_results.py --markdown on ../results.json) into the READMEs and the front page.

Usage: update_readmes.py PAPER_DIR

PAPER_DIR/README.md gets the summary line and a short table (item, verdict, measure) between
<!--RESULTS-SUMMARY--> markers; figure-reproduction/README.md gets the full table (with the causes) between
<!--RESULTS-TABLE--> markers; both get the claims line between <!--CLAIMS-LINE--> markers; package/README.md
gets the checks between <!--CHECKS--> markers; site/index.html gets the verdict stamp between <!--PMC4079617-VERDICT-->
markers. Every number comes from results.json or the committed outputs. Run it after results.json changes;
never edit those parts by hand.
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
claim_line = (f"The main claim {mv}. Every statement about bias, SE and MSE holds on our run but one, which the paper's own "
              f"Table 2 breaks as well: without contamination the two SEs differ by less than {F['se0_diff']}, yet can round to "
              f"different second decimals. The one table cell that misses is a misprint in Table 3 (0.013 where the paper's own "
              f"bias and SE give {F['typo_implied']}), and the convergence count of the Discussion belongs to SAS's optimizer, "
              f"which we cannot run.")
put(paper / "README.md", "RESULTS-SUMMARY", summary + "\n\n" + "\n".join(short))
put(paper / "figure-reproduction" / "README.md", "RESULTS-TABLE", summary + "\n\n" + "\n".join(lines))
put(paper / "figure-reproduction" / "README.md", "CLAIMS-LINE", claim_line)
put(paper / "README.md", "CLAIMS-LINE", claim_line)
H = json.load(open(paper / "figure-reproduction" / "output" / "comparison.json"))["hypotheses"]
WHAT = {"sample": "a fixed ceil(n rate/2) records per tail in every data set", "sample500": "the same at n = 500",
        "floor": "a fixed floor(n rate/2) per tail (against the fixed ceil)", "bottom": "the whole rate at the bottom of p_y",
        "top": "the whole rate at the top of p_y", "fitted": "a fixed number ranked by fitted p_y",
        "noquad": "Z^2 left out of the fitted models (non-linear columns)"}
hy = ["| Variant | Table | Variant within | Compared with | That reading within | RMS z, variant / that reading |",
      "| --- | --- | --- | --- | --- | --- |"]
for name, tabs in H.items():
    for t, s_ in tabs.items():
        base, who = (s_["sample_run"], "the fixed ceil reading") if "sample_run" in s_ else (s_["main_run"], "the main reading")
        hy.append(f"| {WHAT[name]} | {t} | {s_['within']} of {s_['fields']} | {who} | {base['within']} of {base['fields']} | "
                  f"{s_['rms_z']:.2f} / {base['rms_z']:.2f} |")
put(paper / "figure-reproduction" / "README.md", "HYPOTHESES", "\n".join(hy))
C = json.load(open(paper / "figure-reproduction" / "output" / "comparison.json"))
ct = ["| Table | Our run of the other sample size | Linear and non-linear columns swapped | RR rows swapped | Our run (the right design) | Our second run |",
      "| --- | --- | --- | --- | --- | --- |"]
for t, d in C["controls"].items():
    ct.append(f"| {C['tables'][t]['label']} | " + " | ".join(f"{v['within']}" for v in d.values())
              + f" | {C['replicate'][t]['within']} |")
put(paper / "figure-reproduction" / "README.md", "CONTROLS", "Cells of 144 within tolerance:\n\n" + "\n".join(ct))
put(paper / "package" / "README.md", "CHECKS",
    f"{F['within']} of {F['cells']} printed cells of Tables 1-3 and A1-A3 within Monte Carlo error (the miss is a "
    f"misprint of the paper), and its fits against statsmodels and an independent maximizer ({F['x_detail']}).", inline=True)

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

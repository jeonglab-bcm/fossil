"""Compare a fresh run with the committed results. Print a Markdown report. Exit 1 if Fig. 5,
which uses the paper's own data, no longer matches the published figure.

Usage: python3 check_reproduction.py <dir with the fresh outputs>
"""
import csv
import json
import os
import sys

import numpy as np
from PIL import Image

NEW = sys.argv[1] if len(sys.argv) > 1 else "."
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
OUTPUT = os.path.join(HERE, "..", "output")
new = lambda f: os.path.join(NEW, f)
old = lambda f: os.path.join(DATA, f)
out, ok = [], True


def line(item, result, status):
    out.append(f"| {item} | {result} | {status} |")


out += ["## PMC4247685 reproduction check", "", "| Item | Result | Status |", "| --- | --- | --- |"]

a, b = open(new("fig5_clinical.csv")).read(), open(old("fig5_clinical.csv")).read()
line("Fig. 5 data (Table S3 clinical rows) vs committed", "identical" if a == b else "differs",
     "same" if a == b else "DIFFERS")
ok &= a == b
t = json.load(open(new("fig5_tests.json")))
line("Fig. 5 logrank p, PFS / OS", f"{t['pfs']['p']:.4f} / {t['os']['p']:.4f} (paper 0.15 / 0.1)",
     "as committed" if abs(t["pfs"]["p"] - json.load(open(old("fig5_tests.json")))["pfs"]["p"]) < 1e-12
     else "DIFFERS")

f5 = json.load(open(new("fig5.json")))
good = min(f5["published_ink_within_2px_of_ours"], f5["our_ink_within_2px_of_published"]) >= 0.99
ok &= good
line("Fig. 5 render vs paper", f"{100 * f5['published_ink_within_2px_of_ours']:.1f}% / "
     f"{100 * f5['our_ink_within_2px_of_published']:.1f}% of ink within 2 px", "matches" if good else "MISMATCH")

c_new, c_old = json.load(open(new("s2_s3_check.json"))), json.load(open(old("s2_s3_check.json")))
line("Tables S2 / S3 probe lists", f"{c_new['shared']} shared of {c_new['s2']}; rows equal until {c_new['rows_equal_until']}",
     "same as committed" if c_new == c_old else "differs from committed")

if os.path.exists(new("fig34_summary.json")) and os.path.exists(old("fig34_summary.json")):
    s_new, s_old = json.load(open(new("fig34_summary.json"))), json.load(open(old("fig34_summary.json")))
    same = all(s_new[k] == s_old[k] for k in ("bicluster_samples", "control_samples", "features"))
    line("TCGA bicluster (Figs 3-4)", f"{s_new['bicluster_samples']} + {s_new['control_samples']} tumours, "
         f"{s_new['features']} CpG sites; PFS logrank p {s_new['pfs_logrank_p']:.2g}",
         "same as committed" if same else "differs from committed")
else:
    line("TCGA bicluster (Figs 3-4)", "no committed bicluster yet", "skipped")

rows = lambda f: list(csv.DictReader(open(f)))
a, b = rows(new("fig2_scores.csv")), rows(old("fig2_scores.csv"))
d = sum(1 for x, y in zip(a, b) if abs(float(x["F.score"]) - float(y["F.score"])) > 1e-12)
line("Fig. 2 scores vs committed", f"{d} of {len(b)} differ", "same" if d == 0 and len(a) == len(b) else "differs")

for fig in ("2", "3", "4", "5"):
    if not os.path.exists(new(f"fig{fig}_ours.png")):
        line(f"Fig. {fig} render", "not rendered in this run", "skipped")
        continue
    A = np.asarray(Image.open(new(f"fig{fig}_ours.png")).convert("L")).astype(float)
    B = np.asarray(Image.open(os.path.join(OUTPUT, f"fig{fig}_ours.png")).convert("L")).astype(float)
    dd = float(np.abs(A - B).mean()) if A.shape == B.shape else float("nan")
    m = json.load(open(new(f"fig{fig}.json")))
    line(f"Fig. {fig} render", f"mean abs grey difference {dd:.2f} vs committed; "
         f"{100 * m['published_ink_within_2px_of_ours']:.1f}% of paper ink within 2 px of ours",
         "same" if dd < 0.05 else "differs")

print("\n".join(out))
sys.exit(0 if ok else 1)

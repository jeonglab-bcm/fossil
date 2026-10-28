"""Compare a fresh run with the committed results. Print a Markdown report. Exit 1 if Table 1 does not match the paper.

Usage: python check_reproduction.py <dir with the fresh outputs>
"""
import csv, json, os, sys
import numpy as np
from PIL import Image

NEW = sys.argv[1] if len(sys.argv) > 1 else "."
HERE = os.path.dirname(os.path.abspath(__file__))
OLD_OUT = os.path.join(HERE, "..", "output")
new = lambda f: os.path.join(NEW, f)
rows = lambda p: list(csv.DictReader(open(p)))
out, ok = [], True

def line(item, result, status):
    out.append(f"| {item} | {result} | {status} |")

out += ["## PMC4081639 reproduction check", "", "| Item | Result | Status |", "| --- | --- | --- |"]

a, b = rows(new("fig2_data.csv")), rows(os.path.join(HERE, "fig2_data.csv"))
d = sum(1 for x, y in zip(a, b) if float(x["error"]) != float(y["error"]))
line("Fig. 2 data (x86 arithmetic) vs committed", f"{d} of {len(b)} points differ", "same" if d == 0 else "differs")
s = json.load(open(new("fig2_summary.json")))
line("Fig. 2: this platform's R vs x86 emulation", f"{s['native_vs_x86_emulation_differ']} of 300 differ on {s['system']} {s['machine']}",
     "same" if s["native_vs_x86_emulation_differ"] == 0 else "differs (expected on arm64)")

for fig in ("4", "5"):
    a, b = rows(new(f"fig{fig}_data.csv")), rows(os.path.join(HERE, f"fig{fig}_data.csv"))
    d = max(abs(float(x["error"]) - float(y["error"])) for x, y in zip(a, b))
    line(f"Fig. {fig} data vs committed", f"max abs difference {d:.3g}", "same" if d == 0 else "differs")

f_new, f_old = json.load(open(new("fig6_scale.json"))), json.load(open(os.path.join(HERE, "fig6_scale.json")))
line("Fig. 6 scale factors (new / committed)", ", ".join(f"{m} {f_new['factor'][m]:.1f} / {f_old['factor'][m]:.1f}" for m in ("mesh", "VGAM")), "timing, hardware-dependent")

t1 = json.load(open(new("table1_result.json")))
for site, v in t1.items():
    good = round(v["psi"], 5) == v["paper"]
    ok &= good
    line(f"Table 1 ψ, {site}", f"{v['psi']:.6f} (paper {v['paper']:.5f})", "matches" if good else "MISMATCH")

for tag in ("2", "4", "5", "5_own", "6", "6_measured"):
    p_new, p_old = new(f"fig{tag}_ours.png"), os.path.join(OLD_OUT, f"fig{tag}_ours.png")
    if not os.path.exists(p_new): continue
    A = np.asarray(Image.open(p_new).convert("L")).astype(float); B = np.asarray(Image.open(p_old).convert("L")).astype(float)
    d = float(np.abs(A - B).mean()) if A.shape == B.shape else float("nan")
    paper = json.load(open(new(f"fig{tag}.json")))["score"]
    line(f"Fig. {tag} render", f"mean abs grey difference: {d:.2f} vs committed render, {paper:.2f} vs paper", "same" if d < 0.05 else "differs")

print("\n".join(out))
sys.exit(0 if ok else 1)

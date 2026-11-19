#!/usr/bin/env python3
"""Read the bar heights of Fig. 3 from the R graphics file the publisher keeps with the article.

  read_published.py MOESM5.eps OUT_JSON

MOESM5 is R's own PostScript output of Fig. 3 (lattice, "R Graphics Output"): the squared bias
(red) and the variance (white) of each gene in each tissue type, drawn upward from zero at
0.01 pt precision. The published Fig. 3 is the same plot redrawn in Illustrator with the bars
signed by the bias. Heights are converted to MSE units with the y axis, calibrated on the 0 and 8
tick labels of each panel row (labels sit 3.59 pt below their tick, the same for every label).
Writes, for each gene and tissue type, bias2 and sigma2, with the drawing's resolution.
"""
import json
import re
import sys

eps, out = sys.argv[1:3]
body = open(eps, encoding="latin-1").read().split("%%EndProlog")[1].splitlines()
bars, texts = [], []
bg = None
i = 0
while i < len(body):
    line = body[i].strip()
    m = re.match(r"/bg \{ ([\d.]+) ([\d.]+) ([\d.]+) \} def", line)
    if m:
        bg = tuple(float(v) for v in m.groups())
    # A red bar: "np / x y m / 0 h l / w 0 l / 0 -h l / cp p3"
    if line == "np" and i + 5 < len(body) and body[i + 5].strip() == "cp p3":
        x, y = map(float, body[i + 1].split()[:2])
        h = float(body[i + 2].split()[1])
        bars.append({"part": "bias2", "bg": bg, "x": x, "y": y, "h": h})
        i += 6
        continue
    m = re.match(r"([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+) r p3", line)   # x y w h r: a white bar
    if m:
        x, y, w, h = map(float, m.groups())
        bars.append({"part": "sigma2", "bg": bg, "x": x, "y": y, "h": h})
    m = re.match(r"([-\d.]+) ([-\d.]+) \((.*)\) ([-\d.]+) ([-\d.]+) ([-\d.]+) t", line)
    if m:
        texts.append({"x": float(m.group(1)), "y": float(m.group(2)), "s": m.group(3), "rot": float(m.group(6))})
    i += 1

tissues = ["BM", "FIB", "LEU", "NB", "POOL"]
labels = [t for t in texts if t["rot"] == 0 and re.fullmatch(r"[A-Z][A-Z0-9]+", t["s"]) and t["s"] != "MSE"]
# The y-axis labels "0" and "8" of each panel row (bottom row labelled on the left, top row on the
# right) give its scale; every label sits the same 3.59 pt below its tick, so the label spacing is
# the tick spacing.
scale = {}
for t in texts:
    if t["rot"] == 0 and t["s"] in ("0", "8"):
        scale.setdefault("bottom" if t["y"] < 400 else "top", {})[t["s"]] = t["y"]
unit_pt = {row: (v["8"] - v["0"]) / 8 for row, v in scale.items()}
red, white = (1.0, 0.0, 0.0), (1.0, 1.0, 0.9804)
panel_x0, panel_w, slot = 90.20, 89.91, 14.985   # first panel's left edge, panel width, bar spacing (pt)
vals = {}
for b in bars:
    if b["y"] > 520:
        continue                      # legend keys
    if (b["part"] == "bias2" and b["bg"] != red) or (b["part"] == "sigma2" and b["bg"] != white):
        continue                      # strip backgrounds
    row = "bottom" if b["y"] < 400 else "top"
    names = sorted((t for t in labels if (t["y"] < 400) == (row == "bottom")), key=lambda t: t["x"])
    pi = int((b["x"] - panel_x0) // panel_w)
    ti = round((b["x"] - panel_x0 - pi * panel_w - 9.99) / slot)
    vals.setdefault(f"{names[pi]['s']}.{tissues[ti]}", {})[b["part"]] = b["h"] / unit_pt[row]
assert len(vals) == 50 and all(len(v) == 2 for v in vals.values()), len(vals)
doc = {"source": "MOESM5.eps (R Graphics Output of Fig. 3)",
       "pt_per_unit": unit_pt,
       "resolution": "heights at 0.01 pt; the scale from tick labels at 0.01 pt over 88.9 pt (relative 1.1e-4)",
       "bars": {k: {p: round(v, 6) for p, v in sorted(d.items())} for k, d in sorted(vals.items())}}
json.dump(doc, open(out, "w"), indent=1)
print(f"{len(vals)} bars,", {k: round(v, 4) for k, v in unit_pt.items()}, "pt per unit")

"""Render one figure from saved parameters (PDF, TeX, aligned PNG, fit summary).

Usage: python final.py <tag> [params.json] [outdir]; tag in 2, 4, 5, 5_own, 6, 6_measured.
Defaults: params/fig<tag>.json and ../output next to this script. Data files are read from the working directory.
"""
import json, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from fit_render import fit, SPEC, GREY

tag = sys.argv[1]; fig = tag[0]
prm = json.load(open(sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "params", f"fig{tag}.json")))
OUT = sys.argv[3] if len(sys.argv) > 3 else os.path.join(HERE, "..", "output")
os.makedirs(OUT, exist_ok=True)
r, al = fit(fig, prm["font"], prm["dpi"], prm["p"], keep=os.path.join(OUT, f"fig{tag}"))
Image.fromarray(al.clip(0, 255).astype(np.uint8)).save(os.path.join(OUT, f"fig{tag}_ours.png"), optimize=True)
s = SPEC[fig]
json.dump(dict(r, p=prm["p"], panel=GREY(s["pv"]), strip=GREY(s["strip"]) if fig == "6" else None),
          open(os.path.join(OUT, f"fig{tag}.json"), "w"), indent=1, default=int)
print(tag, "mean |diff| %.3f" % r["score"], "shift", r["shift"])

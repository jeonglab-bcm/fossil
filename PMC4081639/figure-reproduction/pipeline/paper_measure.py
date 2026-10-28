"""Measure the published figures: curve traces (Figs 2/4/5), Fig. 5 y-limits, Fig. 6 y-limits and box medians.

Usage: python paper_measure.py <dir with figure-{2,4,5,6}.jpg>
Writes paper_traces.json, fig5_scale.json and fig6_paper.json to the working directory.
"""
import json, os, sys
import numpy as np
from PIL import Image

PUB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "published")
img = lambda f: np.asarray(Image.open(os.path.join(PUB, f"figure-{f}.jpg")).convert("L")).astype(int)

traces = {}
for f, (x0, x1, y0, y1) in {"2": (143, 509, 15, 444), "4": (105, 433, 10, 419), "5": (77, 458, 15, 424)}.items():
    a = img(f); tr = []
    for x in range(x0, x1 + 1):
        ys = np.where(a[y0:y1 + 1, x] < 110)[0]
        if len(ys): tr.append((x, int(ys.min() + y0), int(ys.max() + y0)))
    traces[f"figure-{f}"] = tr
json.dump(traces, open("paper_traces.json", "w"))

# Fig. 5: major gridlines at 2000, 1000, -1000, -2000 (rows 49, 134, 305, 391); panel rows 15..424
k, b = np.polyfit([49.5, 134.5, 305.5, 391.5], [2000, 1000, -1000, -2000], 1)
json.dump({"ylim": [k * 425 + b, k * 15 + b]}, open("fig5_scale.json", "w"))

# Fig. 6: gridlines for 100, 10, 1 at rows 115, 192, 269 (77 px per decade); panel rows 61..312
a = img("6"); log = lambda row: (269.5 - row) / 77.0
facets = [(83, 158), (165, 240), (248, 323), (331, 406), (414, 489), (496, 571)]
med = {}
for n, (fa, fb) in zip([100, 1000, 10000, 100000, 1000000, 10000000], facets):
    w = fb - fa + 1
    for m, frac in (("mesh", 0.6 / 2.2), ("VGAM", 1.6 / 2.2)):
        if m == "VGAM" and n > 100000: continue
        cx = fa + frac * w; half = 0.9 * w / 2.2 / 2
        lo, hi = int(round(cx - half * 0.6)), int(round(cx + half * 0.6))
        rows = [y for y in range(61, 313) if (a[y, lo:hi + 1] < 130).mean() >= 0.9]
        runs, s, p = [], rows[0], rows[0]
        for r in rows[1:]:
            if r - p > 1: runs.append((s, p)); s = r
            p = r
        runs.append((s, p))
        t = max(runs, key=lambda t: t[1] - t[0])  # fattened median line, or a collapsed box
        med[f"{n}|{m}"] = 10 ** log((t[0] + t[1]) / 2 + 0.5)
json.dump({"ylim": [10 ** (-(313 - 269.5) / 77), 10 ** (2 + (115.5 - 61) / 77)], "medians": med}, open("fig6_paper.json", "w"), indent=1)
print("paper_measure: fig5 ylim", [round(v, 1) for v in json.load(open("fig5_scale.json"))["ylim"]], "fig6 medians", {k: round(v, 3) for k, v in med.items()})

"""Fit each published panel's axes (pixel to data) to its tick marks and printed tick labels.

  calibrate.py PUBLISHED_DIR OUT_JSON

For every panel in PUBLISHED_DIR/axes.json, finds the tick marks just outside the box (dark
pixels 2 to 7 px left of the box for y, below it for x), pairs them in order with the printed
labels, and fits value = a + b * pixel by least squares. Writes, per panel, the box, the fit,
its largest residual in pixels and the data values at the box edges (the plot's usr limits).
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

pub, out = Path(sys.argv[1]), Path(sys.argv[2])
spec = json.loads((pub / "axes.json").read_text())


def centers(mask):
    idx = np.where(mask)[0]
    groups, cur = [], [idx[0]]
    for i in idx[1:]:
        if i == cur[-1] + 1:
            cur.append(i)
        else:
            groups.append(cur)
            cur = [i]
    groups.append(cur)
    return [float(np.mean(g)) for g in groups]


res = {}
for fig, s in spec.items():
    if not fig.startswith("figure-"):
        continue
    a = np.asarray(Image.open(pub / f"{fig}.jpg").convert("L")).astype(float)
    for p in s["panels"]:
        x0, x1, y0, y1 = p["box"]
        ystrip = (a[y0 - 1:y1 + 2, x0 - 7:x0 - 2] < 170).sum(axis=1) >= 3
        xstrip = (a[y1 + 2:y1 + 7, x0 - 1:x1 + 2] < 170).sum(axis=0) >= 3
        yt = [c + y0 - 1 for c in centers(ystrip)]
        xt = [c + x0 - 1 for c in centers(xstrip)]
        out_p = {"box": p["box"], "size": [a.shape[1], a.shape[0]]}
        for axis, ticks, labels in (("x", xt, p["xticks"]), ("y", yt, sorted(p["yticks"], reverse=True))):
            if len(ticks) != len(labels):
                raise SystemExit(f"{p['id']} {axis}: {len(ticks)} tick marks for {len(labels)} labels: {ticks}")
            b, c = np.polyfit(ticks, labels, 1)
            resid = (np.array(labels) - (b * np.array(ticks) + c)) / b
            lo, hi = (x0, x1) if axis == "x" else (y1, y0)
            out_p[axis] = {"ticks_px": [round(t, 2) for t in ticks], "labels": labels, "per_px": b, "at0": c,
                           "max_resid_px": round(float(np.abs(resid).max()), 3),
                           "usr": [b * lo + c, b * hi + c]}
        res[p["id"]] = {**out_p, **{k: p[k] for k in ("n", "heading", "sizes") if k in p}}
out.write_text(json.dumps(res, indent=1) + "\n")
# The same, flat, for the R figure script
with open(out.with_suffix(".csv"), "w") as f:
    f.write("id,W,H,x0,x1,y0,y1,xusr0,xusr1,yusr0,yusr1\n")
    for k, v in res.items():
        f.write(",".join([k] + [str(t) for t in v["size"] + v["box"] + v["x"]["usr"] + v["y"]["usr"]]) + "\n")
for k, v in res.items():
    print(k, "x usr %.4f %.4f resid %.2f px" % (*v["x"]["usr"], v["x"]["max_resid_px"]),
          "| y usr %.5f %.5f resid %.2f px" % (*v["y"]["usr"], v["y"]["max_resid_px"]))

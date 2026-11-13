"""One-off hypothesis test for Fig. 5 (not part of the pipeline run). The paper draws one deletion
per size; this scores single deletions, each embedded two ways (the largest component only, or every
protein including those the deletion cut off), against the matching published curve.

Usage: fig5_single_deletions.py YHIGH.tsv PUBLISHED_DIR OUT.json [--repeats N]
(committed as output/run/fig5_single_deletions.json)
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import geodenoise as gd  # noqa: E402
import figtools as ft  # noqa: E402
import figures as F  # noqa: E402
from yeast import SEED, labels, nonedge_universe  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("yhigh")
ap.add_argument("published")
ap.add_argument("out")
ap.add_argument("--repeats", type=int, default=10)
a = ap.parse_args()

net = gd.read_network(a.yhigh)
n_all = net.n * (net.n - 1) // 2 - net.m
img = ft.load(Path(a.published) / "figure-5.png")
cal = ft.excel_axes(img, (12, 12, img.shape[1] - 12, img.shape[0] - 12), [i / 10 for i in range(11)], (0, 1))
pubs = F.pub_masks(img, F.EXCEL4, F.plot_region(img.shape, cal, [(745, 285, 1220, 535)]))
w = float(np.median([ft.line_width(m) for m in pubs if m.any()]))
ex = np.zeros(img.shape[:2], bool)
for m in pubs:
    ex |= ft.marker_mask(m, w)

rows = []
for dim in (4, 5, 6, 7):
    rng = np.random.default_rng(SEED)
    for ki, k in enumerate([500, 1000, 2000, 3000]):
        for r in range(a.repeats):
            drop = rng.choice(net.m, size=k, replace=False)
            keep = np.ones(net.m, bool)
            keep[drop] = False
            cur = gd.Network(net.nodes, net.edges[keep])
            dropped = [(net.nodes[x], net.nodes[y]) for x, y in net.edges[drop]]
            row = {"dimension": dim, "deleted": k, "repeat": r}
            for name, g in (("lcc", gd.largest_component(cur)), ("whole", cur)):
                D = gd.pairwise_distances(gd.embed(g, dim))
                ci, cj = nonedge_universe(g)
                pos = labels(g, ci, cj, dropped)
                d = D[ci, cj]
                x = [float((d[~pos] < e).sum() / n_all) for e in F.FIG5_GRID] + [1.0]
                y = [float((d[pos] < e).sum() / k) for e in F.FIG5_GRID] + [1.0]
                s = F.score_panel([pubs[ki]], [(x, y)], cal, img.shape, w, ex)[0]
                row[name] = round(s["score"], 4)
            rows.append(row)
            print(row, flush=True)

summary = {}
for dim in (4, 5, 6, 7):
    for k in (500, 1000, 2000, 3000):
        sel = [r for r in rows if r["dimension"] == dim and r["deleted"] == k]
        summary[f"{dim}:{k}"] = {v: {"median": round(float(np.median([r[v] for r in sel])), 4),
                                     "max": max(r[v] for r in sel)} for v in ("lcc", "whole")}
json.dump({"what": "Single deletions scored against the matching published Fig. 5 curve (share of "
                   "pixels within 2 px, both ways, the smaller); lcc embeds the largest component, "
                   "whole every protein", "repeats": a.repeats, "summary": summary, "runs": rows},
          open(a.out, "w"), indent=1)

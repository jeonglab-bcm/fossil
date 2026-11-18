"""Hypothesis tests for the Fig. 5 bin medians that miss (not part of the pipeline).

usage: fig5_tests.py RUN_DIR FIGURES_DIR OUT_JSON

Reads the bin medians that figures.py wrote to scores.json ("values") and tests three
explanations for the bins outside the margin of a new random draw:

1. raster: reading medians from the rendered dots biases them. Our medians read from our render
   against our medians computed from the cell values.
2. stretch: our pseudo time runs at another speed. Our cell-value medians with the pseudo time
   axis stretched by s in 0.85 to 1.15; hits at the best s against s = 1.
3. replicates: the margin leaves out the spread between Wanderlust replicates. The margin widened
   by the SD of the bin median over our three replicate orderings.
"""
import json
import sys
from pathlib import Path

import numpy as np


def medians(x, y, bins):
    out = []
    for a, b in zip(bins[:-1], bins[1:]):
        m = (x >= a) & (x < b)
        out.append(float(np.median(y[m])) if m.sum() else None)
    return out


def hits(pub, ours, margin):
    return int(sum(1 for p, o, t in zip(pub, ours, margin) if p is not None and o is not None and abs(p - o) <= t))


def main(run, figs, out):
    run = Path(run)
    V = json.loads((Path(figs) / "scores.json").read_text())["values"]
    d = np.load(run / "toggle_data.npz")
    geom = json.loads((run / "toggle_geometry.json").read_text())
    cells = np.array(geom["branches"]["C"]["cells"])
    res = {"genes": {}}
    tot = {"raster": 0, "cells": 0, "stretch_best": 0, "replicates": 0, "fields": 0}
    scales = np.round(np.arange(0.85, 1.151, 0.01), 2)
    stretch_hits = np.zeros(len(scales), int)
    per_gene = {}
    for gi, g in enumerate("ABCD"):
        v = V[f"fig5.g{g}"]
        bins = np.array(v["bins"])
        pub, margin = v["published"], v["margin"]
        reps = []
        for k in range(d["pt_C"].shape[0]):
            order = np.argsort(d["pt_C"][k])
            reps.append(medians(np.arange(len(order)), d["Xo"][cells][order][:, gi], bins))
        cell_med = reps[0]
        sd_rep = [float(np.std([r[i] for r in reps])) for i in range(len(bins) - 1)]
        wide = [float(np.sqrt(t ** 2 + (2 * np.sqrt(2) * s) ** 2)) for t, s in zip(margin, sd_rep)]
        order = np.argsort(d["pt_C"][0])
        y = d["Xo"][cells][order][:, gi]
        x = np.arange(len(order), dtype=float)
        sh = [hits(pub, medians(x * s, y, bins), margin) for s in scales]
        stretch_hits += np.array(sh)
        per_gene[g] = {"published": pub, "ours_raster": v["ours"], "ours_cells": [round(m, 1) for m in cell_med],
                       "raster_minus_cells": [None if a is None else round(a - b, 1) for a, b in zip(v["ours"], cell_med)],
                       "margin": margin, "margin_with_replicates": [round(w, 1) for w in wide],
                       "hits_raster": hits(pub, v["ours"], margin), "hits_cells": hits(pub, cell_med, margin),
                       "hits_replicates": hits(pub, v["ours"], wide)}
        tot["raster"] += per_gene[g]["hits_raster"]
        tot["cells"] += per_gene[g]["hits_cells"]
        tot["replicates"] += per_gene[g]["hits_replicates"]
        tot["fields"] += sum(1 for p in pub if p is not None)
    best = int(np.argmax(stretch_hits))
    tot["stretch_best"] = int(stretch_hits[best])
    res = {"genes": per_gene, "totals": tot, "stretch": {"scales": scales.tolist(), "hits": stretch_hits.tolist(),
                                                          "best_scale": float(scales[best])}}
    Path(out).write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(tot), "best stretch", scales[best])


if __name__ == "__main__":
    main(*sys.argv[1:4])

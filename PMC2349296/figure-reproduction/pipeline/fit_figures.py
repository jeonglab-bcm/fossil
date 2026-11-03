#!/usr/bin/env python3
"""Fit the presentation parameters of Figures 1 and 2 to the published images.

Draws the published Table 2/4 values (published_values.csv) so that the fit sees no data
differences, and scores candidates by chamfer distance per region (compare_figures.py).
Stages (each fixes its parameter before the next):
  1. pointsize            - tick-label and legend text size: shift-invariant chamfer of the
                            x/y tick labels (best over a +-6 px window)
  2. mgp[2], mgp[1]       - tick-label and axis-title distance (lines): chamfer at zero shift
  3. cex_pt               - point symbol size: chamfer in the data region
  4. legend_xi, legend_yi - legend spacing: chamfer in the legend box
Writes params/figure_params.R (fitted values) and fit_figures.csv (every candidate).

Usage: fit_figures.py RSCRIPT WORK_DIR
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from itertools import product
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from compare_figures import best_shift, chamfer, load  # noqa: E402

# Measured pixel indices of the tick marks and legend corner, + 0.5 for the pixel centre
# (R device coordinates put pixel k at [k, k + 1]).
BASE = {
    1: dict(width=407, height=231, x1=71.5, x5=389.5, y0=191.5, y100=14.5, legend_px=(246.5, 120.5)),
    2: dict(width=402, height=231, x1=71.5, x5=388.5, y0=192.5, y100=14.5, legend_px=(246.5, 121.5)),
}
START = dict(pointsize=10.0, mgp=(3.0, 1.0, 0.0), legend_xi=1.0, legend_yi=1.0, cex_pt=1.0)


def params_r(fit: dict[int, dict]) -> str:
    lines = [
        "# Presentation parameters for Figures 1 and 2 (written by fit_figures.py).",
        "# MEASURED from the published images (pixels): size, axis ticks (x = 1..5 -> x1..x5,",
        "# y = 0 and 100 -> y0, y100), legend box top-left corner, series grey (Fig. 2 mode 189 =",
        "# R \"gray\", 190). FITTED (not data): pointsize, mgp, cex_pt, legend_xi, legend_yi.",
        "fp <- list(",
        '  grey = "gray",',
        "  fig = list(",
    ]
    items = []
    for i in (1, 2):
        b, f = BASE[i], fit[i]
        items.append(
            f"    list(width = {b['width']}, height = {b['height']}, x1 = {b['x1']}, x5 = {b['x5']}, "
            f"y0 = {b['y0']}, y100 = {b['y100']},\n"
            f"         legend_px = c({b['legend_px'][0]}, {b['legend_px'][1]}), "
            f"pointsize = {f['pointsize']}, mgp = c({', '.join(str(m) for m in f['mgp'])}),\n"
            f"         legend_xi = {f['legend_xi']}, legend_yi = {f['legend_yi']}, cex_pt = {f['cex_pt']})"
        )
    lines.append(",\n".join(items))
    lines += ["  )", ")"]
    return "\n".join(lines) + "\n"


class Fitter:
    def __init__(self, rscript: str, work: Path):
        self.rscript, self.work = rscript, work
        work.mkdir(parents=True, exist_ok=True)
        self.pub = {i: load(HERE.parent / "published" / f"figure-{i}.jpg") for i in (1, 2)}
        self.regions = {i: {r["name"]: r["box"] for r in json.loads(
            (HERE / "params" / f"regions-figure-{i}.json").read_text())} for i in (1, 2)}
        self.log = []
        self.n = 0

    def render(self, fit):
        self.n += 1
        p = self.work / f"cand{self.n}.R"
        p.write_text(params_r(fit))
        prefix = self.work / f"cand{self.n}"
        subprocess.run([self.rscript, str(HERE / "figures.R"), str(HERE / "published_values.csv"),
                        str(p), str(prefix)], check=True, capture_output=True)
        return {i: load(Path(f"{prefix}-figure-{i}.png")) for i in (1, 2)}

    def mask(self, i, name):
        x0, x1, y0, y1 = self.regions[i][name]
        m = np.zeros(self.pub[i].shape, bool)
        m[y0:y1 + 1, x0:x1 + 1] = True
        return m

    def score(self, imgs, i, names, invariant=False):
        tot = 0.0
        for nm in names:
            if invariant:
                tot += best_shift(self.pub[i], imgs[i], self.regions[i][nm], window=6)["chamfer_at_best"]
            else:
                c = chamfer(self.pub[i], imgs[i], self.mask(i, nm))
                tot += 20.0 if c is None else c  # ink missing from the region: penalty
        return tot

    def stage(self, fit, name, key, values, names, invariant=False):
        for i in (1, 2):
            best = None
            for v in values:
                cand = {k: dict(fit[k]) for k in fit}
                cand[i][key] = v
                s = self.score(self.render(cand), i, names, invariant)
                self.log.append({"stage": name, "figure": i, "parameter": key, "value": v, "score": round(s, 4)})
                if best is None or s < best[0]:
                    best = (s, v)
            fit[i][key] = best[1]
            print(f"stage {name}: figure {i} {key} = {best[1]} (score {best[0]:.3f})", flush=True)
        return fit


def main():
    rscript, work = sys.argv[1], Path(sys.argv[2])
    f = Fitter(rscript, work)
    fit = {i: dict(START) for i in (1, 2)}
    fit = f.stage(fit, "1", "pointsize", [9 + 0.5 * k for k in range(11)], ["x_labels", "y_labels"], True)
    mgps = [(t, l, 0.0) for t, l in product([1.5, 2.0, 2.5, 3.0, 3.5], [0.5, 0.75, 1.0, 1.25, 1.5])]
    fit = f.stage(fit, "2", "mgp", mgps, ["x_labels", "y_labels", "y_title"])
    fit = f.stage(fit, "3", "cex_pt", [0.8 + 0.1 * k for k in range(9)], ["data"])
    fit = f.stage(fit, "4a", "legend_xi", [0.6 + 0.1 * k for k in range(10)], ["legend"])
    fit = f.stage(fit, "4b", "legend_yi", [0.6 + 0.1 * k for k in range(10)], ["legend"])
    for i in (1, 2):
        fit[i]["cex_pt"] = round(fit[i]["cex_pt"], 2)
        fit[i]["legend_xi"] = round(fit[i]["legend_xi"], 2)
        fit[i]["legend_yi"] = round(fit[i]["legend_yi"], 2)
    (HERE / "params" / "figure_params.R").write_text(params_r(fit))
    with open(HERE / "params" / "fit_figures.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(f.log[0]))
        w.writeheader()
        w.writerows(f.log)


if __name__ == "__main__":
    main()

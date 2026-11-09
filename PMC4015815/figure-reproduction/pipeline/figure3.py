"""Figure 3 on the published pixel grid, its scores and negative controls.

usage: figure3.py PUBLISHED_PNG AXES_JSON DR_CSV DT_CSV OUTDIR

The published frame, ticks, labels and legend are kept; the data layer inside the axes box
(outside the legend box) is erased and our two series are drawn in the published style, measured
from the figure: 15 px black squares and 17 px red circles, 1 px lines that stop 3 px short of
each marker (Origin's gapped line). Points are placed with the tick-fitted pixel map
(figure3_axes.py). Writes fig3_ours.png, fig3_overlay.png (published in grey, ours in blue),
and fig3_scores.json with the two-way trace scores of each series (2 px tolerance) and the
controls: the other method's values drawn in this series' place (wrong input) and our values
moved by +-0.0005 ROC (half a unit in Table 1's last digit) and by +-2.5 in dMAX (1% of the axis)
(near misses). DT_CSV may be '-' when SVM-DT has not been run.
"""
import csv
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from trace_score import two_way

SS = 4  # supersampling for antialiased drawing
STYLE_LINE_PX = 1  # measured: the published lines are about 1 px wide
LEGEND = (742, 1055, 514, 626)  # x0, x1, y0, y1 of the legend box in published pixels
STYLE = {"SVM-DR": {"rgb": (0, 0, 0), "marker": "square", "size": 15},
         "SVM-DT": {"rgb": (255, 0, 0), "marker": "circle", "size": 17}}


def mean_roc(path):
    by = {}
    with open(path) as fh:
        for r in csv.DictReader(fh):
            by.setdefault(int(r["dmax"]), []).append(float(r["roc"]))
    return {d: float(np.mean(v)) for d, v in sorted(by.items())}


def data_region(shape, ax):
    left, right, top, bottom = ax["box_px"]
    m = np.zeros(shape, bool)
    m[int(top) + 22:int(bottom) - 15, int(left) + 16:int(right) - 14] = True  # inside the ticks
    x0, x1, y0, y1 = LEGEND
    m[y0 - 2:y1 + 3, x0 - 2:x1 + 3] = False
    return m


def to_px(ax, dmax, roc):
    return ax["x_px"][0] + ax["x_px"][1] * dmax, ax["y_px"][0] + ax["y_px"][1] * roc


def draw_series(size, ax, points, style):
    """RGBA layer with one series drawn; points: list of (dmax, roc)."""
    W, H = size
    layer = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    dr = ImageDraw.Draw(layer)
    col = style["rgb"] + (255,)
    px = [to_px(ax, d, r) for d, r in points]
    half = style["size"] / 2.0
    for (x0, y0), (x1, y1) in zip(px[:-1], px[1:]):
        L = np.hypot(x1 - x0, y1 - y0)
        gap = half + 3.0
        if L <= 2 * gap:
            continue
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        a = (x0 + ux * gap, y0 + uy * gap)
        b = (x1 - ux * gap, y1 - uy * gap)
        dr.line([(a[0] * SS, a[1] * SS), (b[0] * SS, b[1] * SS)], fill=col, width=STYLE_LINE_PX * SS)
    for x, y in px:
        box = [(x - half) * SS, (y - half) * SS, (x + half) * SS, (y + half) * SS]
        if style["marker"] == "square":
            dr.rectangle(box, fill=col)
        else:
            dr.ellipse(box, fill=col)
    return layer.resize((W, H), Image.LANCZOS)


def series_mask(rgb, name):
    r, g, b = rgb[..., 0].astype(int), rgb[..., 1].astype(int), rgb[..., 2].astype(int)
    red = (r - g > 60) & (r - b > 60)
    if name == "SVM-DT":
        return red
    # black ink, away from the red series (its dark antialiased edges)
    near_red = ndimage.binary_dilation(red, iterations=3)
    return (r < 150) & (g < 150) & (b < 150) & (np.abs(r - g) < 40) & ~near_red


def render(pub_rgb, region, ax, series):
    base = pub_rgb.copy()
    base[region] = 255
    img = Image.fromarray(base).convert("RGBA")
    for name, pts in series.items():
        if pts:
            img = Image.alpha_composite(img, draw_series(img.size, ax, pts, STYLE[name]))
    return np.asarray(img.convert("RGB"))


def score(pub_rgb, region, ax, name, pts):
    ours = render(pub_rgb, region, ax, {name: pts})
    return two_way(series_mask(pub_rgb, name) & region, series_mask(ours, name) & region)


def main(published, axes_json, dr_csv, dt_csv, outdir):
    os.makedirs(outdir, exist_ok=True)
    pub = np.asarray(Image.open(published).convert("RGB"))
    ax = json.load(open(axes_json))
    region = data_region(pub.shape[:2], ax)
    ours = {"SVM-DR": mean_roc(dr_csv)}
    if dt_csv != "-" and os.path.exists(dt_csv):
        ours["SVM-DT"] = mean_roc(dt_csv)
    pts = {k: sorted(v.items()) for k, v in ours.items()}
    img = render(pub, region, ax, pts)
    Image.fromarray(img).save(os.path.join(outdir, "fig3_ours.png"))
    # overlay: published in light grey, ours in blue on top
    grey = np.asarray(Image.fromarray(pub).convert("L")).astype(float)
    ov = np.stack([grey * 0.35 + 165] * 3, -1)
    for name in pts:
        m = series_mask(render(pub, region, ax, {name: pts[name]}), name) & region
        ov[m] = (0, 90, 255) if name == "SVM-DR" else (0, 170, 120)
    ov[~region] = pub[~region]
    Image.fromarray(ov.astype(np.uint8)).save(os.path.join(outdir, "fig3_overlay.png"))

    published_series = {k: [(p["dmax"], p["roc"]) for p in v] for k, v in ax["series"].items()}
    res = {"tolerance_px": 2, "series": {}}
    for name, p in pts.items():
        other = "SVM-DT" if name == "SVM-DR" else "SVM-DR"
        s = {"ours": score(pub, region, ax, name, p), "controls": []}
        if other in published_series:
            wrong = [(d, r) for d, r in published_series[other]]
            s["controls"].append({"name": f"{other} values in place of {name}",
                                  "kind": "wrong_input",
                                  "score": score(pub, region, ax, name, wrong)["score"]})
        for dy in (0.0005, -0.0005):
            s["controls"].append({"name": f"ours {dy:+.4f} ROC", "kind": "near_miss",
                                  "score": score(pub, region, ax, name,
                                                 [(d, r + dy) for d, r in p])["score"]})
        for dx in (2.5, -2.5):
            s["controls"].append({"name": f"ours {dx:+.1f} in dMAX", "kind": "near_miss",
                                  "score": score(pub, region, ax, name,
                                                 [(d + dx, r) for d, r in p])["score"]})
        s["published_markers"] = published_series.get(name)
        s["ours_values"] = [[d, round(r, 6)] for d, r in p]
        # the published curve read off the figure and redrawn: what a perfect match scores
        s["published_redrawn"] = score(pub, region, ax, name, published_series[name])["score"]
        res["series"][name] = s
    json.dump(res, open(os.path.join(outdir, "fig3_scores.json"), "w"), indent=1)
    for name, s in res["series"].items():
        print(name, s["ours"], "redrawn", s["published_redrawn"],
              [(c["name"], c["score"]) for c in s["controls"]])


if __name__ == "__main__":
    main(*sys.argv[1:6])

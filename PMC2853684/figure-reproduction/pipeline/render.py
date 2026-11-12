"""Our figures, and our values drawn on the published ones.

    render.py analysis.json published_values.json PUBLISHED_DIR OUT_DIR

For each figure: `<fig>_ours.png`, our values drawn on their own in the paper's layout, and
`<fig>_overlay.png`, the published figure in grey with our values on top in magenta (points and
lines of Figs 2 and S1, bar tops and error-bar ends of Figs 4 and S2, cell counts and margins of
Fig. 3). Our values are placed with the axis calibrations read from the PDFs (read_published.py),
so a magenta mark sits on the published mark when the two agree.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image, ImageDraw, ImageOps  # noqa: E402

from read_published import FIG2_PANELS, FIG4_AXES, S1_AXES  # noqa: E402

MAGENTA = (220, 0, 160)
# R colours and point characters of Fig. 2 (supplement's RGB values); matplotlib markers alike.
STYLE = {
    "Neighborhood": ("#0000FF", "s"), "Oti1": ("#00FF00", "^"), "Oti2": ("#008B8B", "+"), "Oti3": ("#FF00FF", "s"),
    "GS1": ("#FF0000", "D"), "GS2": ("#FFA500", "X"), "GS3": ("#9966FF", "v"), "GS-All": ("#000000", "x"),
    "MCL": ("#008000", "o"), "VI-CutL": ("#808000", "*"), "VI-CutS": ("#FF6347", "o"), "Prop": ("#808080", "^"),
    "RW": ("#00FFFF", "s"), "Consensus": ("#8B4513", "D"),
}
FIVE_STYLE = {"Neighborhood": ("#3050a0", "s"), "GS-All": ("#111111", "x"), "VI-CutL": ("#6b6b10", "*"),
              "RW": ("#66ccdd", "p"), "Prop": ("#999999", "D")}
# Supplement page placement of each figure XObject: (x, y, scale) from the page content stream.
S1_PLACE = (153.901, 277.641, 0.40237)
S2_PLACE = {"a_precision": (79.544, 463.814, 0.40506), "a_recall": (307.818, 463.814, 0.40773),
            "b_precision": (79.544, 293.646, 0.40295), "b_recall": (307.818, 293.646, 0.4019)}
FIG3_BOX = (141.9, 659.7, 308.4, 826.1)  # heat map, PDF points (x0, y0, x1, y1)


class Placer:
    """PDF points of a page -> pixels of a published crop."""

    def __init__(self, crop, dpi):
        self.x0, self.top = crop["box_points"][0], crop["box_points"][1]
        self.h = crop["page_height"]
        self.s = dpi / 72

    def __call__(self, x, y):
        return ((x - self.x0) * self.s, (self.h - y - self.top) * self.s)


def inv(cal):
    p0, v0, p1, v1 = cal
    return lambda v: p0 + (v - v0) * (p1 - p0) / (v1 - v0)


def grey(path):
    im = Image.open(path).convert("L")
    im = ImageOps.autocontrast(im)
    im = Image.eval(im, lambda v: 255 - int((255 - v) * 0.45))
    return im.convert("RGB")


def mark(d, x, y, r=4, w=2):
    d.ellipse([x - r, y - r, x + r, y + r], outline=MAGENTA, width=w)


def overlay_curves(pub_png, crop, dpi, series, fx, fy, out, place=None):
    im = grey(pub_png)
    d = ImageDraw.Draw(im)
    P = Placer(crop, dpi)
    for m, pts in series.items():
        xy = []
        for r, p in pts:
            X, Y = fx(r), fy(p)
            if place:
                X, Y = place[0] + place[2] * X, place[1] + place[2] * Y
            xy.append(P(X, Y))
        if len(xy) > 1:
            d.line(xy, fill=MAGENTA, width=2)
        for x, y in xy:
            mark(d, x, y)
    im.save(out, optimize=True)


def ours_curves(series, out, xlim, ylim, title=None, size=(4.9, 4.7), legend=True):
    fig, ax = plt.subplots(figsize=size, dpi=150)
    for m, pts in series.items():
        if not pts:
            continue
        col, mk = STYLE[m]
        ax.plot([p[0] for p in pts], [p[1] for p in pts], "-", color=col, lw=1.2, marker=mk, ms=6, mfc="none", label=m)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_xlabel("Recall (% disease associations recovered)")
    ax.set_ylabel("Precision (% predictions correct)")
    if title:
        ax.set_title(title, loc="left", fontsize=10)
    if legend:
        ax.legend(fontsize=7, loc="upper right", frameon=True)
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)


def overlay_bars(pub_png, crop, dpi, xs, heights, err, fy, out, place=None):
    im = grey(pub_png)
    d = ImageDraw.Draw(im)
    P = Placer(crop, dpi)
    for (x0, x1), h, e in zip(xs, heights, err or [None] * len(xs)):
        def pp(x, y):
            if place:
                x, y = place[0] + place[2] * x, place[1] + place[2] * y
            return P(x, y)
        a, b = pp(x0, fy(h)), pp(x1, fy(h))
        d.line([a, b], fill=MAGENTA, width=3)
        if e is not None:
            xc = (x0 + x1) / 2
            for v in (h - e, h + e):
                c0, c1 = pp(xc - 2, fy(v)), pp(xc + 2, fy(v))
                d.line([c0, c1], fill=MAGENTA, width=3)
    im.save(out, optimize=True)


def ours_bars(fig_data, labels, xlabel, out, legend_fmt="{:.2f}"):
    fig, ax = plt.subplots(figsize=(4.9, 3.6), dpi=150)
    n = len(labels)
    xs = list(range(n))
    bars = [b if b is not None else 0 for b in fig_data["bars"]]
    ax.bar(xs, bars, width=0.8, color="#bfbf30", edgecolor="black",
           yerr=[e or 0 for e in fig_data["spreads"]["var_values"]], capsize=2)
    for x, c in zip(xs, fig_data["counts"]):
        ax.text(x, 0.03, str(c), ha="center", fontsize=8)
    for m, f in fig_data["fits"].items():
        col, mk = FIVE_STYLE[m]
        lo, hi = (0, 1) if n == 10 else (1, 6)
        # the paper draws the fit over the bars' x range (bin index = measure scaled to bins)
        scale = 10 if n == 10 else 1
        xx = [lo, hi]
        yy = [f["intercept"] + f["slope"] * v for v in xx]
        ax.plot([scale * v - (0.5 if n == 10 else 1.5) for v in xx], yy, "-", color=col, marker=mk, ms=3,
                label=f"{m} ({legend_fmt.format(f['r'])})")
    ax.set_xticks(xs)
    ax.set_xticklabels(labels, fontsize=7)
    ax.set_xlim(-0.5, n - 0.5)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("F1-measure of disease predictions")
    ax.legend(fontsize=6.5, loc="upper left" if n == 10 else "upper right")
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)


def main(argv):
    a = json.load(open(argv[1]))
    pub = json.load(open(argv[2]))
    pdir = Path(argv[3])
    out = Path(argv[4])
    out.mkdir(parents=True, exist_ok=True)
    meta = json.load(open(pdir / "crops.json"))
    dpi = meta["dpi"]
    crops = meta["crops"]

    # Fig. 2a, 2b and S1
    series = dict(a["fig2a"])
    ours_curves(series, out / "fig2a_ours.png", (-1, 41), (-2, 102), "(a) HPRD")
    pa = FIG2_PANELS["fig2a"]
    overlay_curves(pdir / "fig2a.png", crops["fig2a"], dpi, series, inv(pa["x"]), inv(pa["y"]), out / "fig2a_overlay.png")
    pb = FIG2_PANELS["fig2b"]
    b_methods = ["Oti2", "Oti3", "GS1", "GS2", "GS-All", "MCL", "VI-CutL", "VI-CutS"]
    series_b = {m: [p for p in a["fig2a"][m] if 0 <= p[0] <= 20 and 20 <= p[1] <= 80] for m in b_methods}
    ours_curves(series_b, out / "fig2b_ours.png", (-0.5, 20.5), (18, 82), "(b) clustering methods")
    overlay_curves(pdir / "fig2b.png", crops["fig2b"], dpi, series_b, inv(pb["x"]), inv(pb["y"]), out / "fig2b_overlay.png")
    ours_curves(a["figS1"], out / "figS1_ours.png", (-1, 41), (-2, 102), "OPHID")
    overlay_curves(pdir / "figS1.png", crops["figS1"], dpi, a["figS1"], inv(S1_AXES["x"]), inv(S1_AXES["y"]),
                   out / "figS1_overlay.png", place=S1_PLACE)

    # Fig. 3
    f3 = a["fig3"]
    mat = f3["matrix"]
    fig, ax = plt.subplots(figsize=(4.9, 4.3), dpi=150)
    import numpy as np

    m = np.array(mat, dtype=float)
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("r", ["#ffffff", "#f4a6a6", "#e62020", "#801010", "#000000"])
    ax.imshow(np.where(m > 0, m, np.nan), origin="lower", extent=(0, 1, 0, 1), cmap=cmap, vmin=0, vmax=142)
    for i in range(10):
        for j in range(10):
            if mat[i][j]:
                ax.text((j + 0.5) / 10, (i + 0.5) / 10, str(mat[i][j]), ha="center", va="center", fontsize=6)
    for j, c in enumerate(f3["columns"]):
        ax.text((j + 0.5) / 10, 1.02, str(c), ha="center", fontsize=7)
    for i, c in enumerate(f3["rows_top_down"]):
        ax.text(1.02, 1 - (i + 0.5) / 10, str(c), va="center", fontsize=7)
    ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8])
    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8])
    ax.grid(True, ls="--", color="k", lw=0.5)
    ax.set_xlabel("Max. recall amongst all 13 methods")
    ax.set_ylabel("Max. precision amongst all 13 methods")
    fig.tight_layout()
    fig.savefig(out / "fig3_ours.png")
    plt.close(fig)
    im = grey(pdir / "fig3.png")
    d = ImageDraw.Draw(im)
    P = Placer(crops["fig3"], dpi)
    x0, y0, x1, y1 = FIG3_BOX
    cw, ch = (x1 - x0) / 10, (y1 - y0) / 10
    for i in range(10):
        for j in range(10):
            if mat[i][j]:
                px, py = P(x0 + (j + 0.5) * cw, y0 + (i + 0.5) * ch)
                d.text((px - 6, py - 6), str(mat[i][j]), fill=MAGENTA)
    for j, c in enumerate(f3["columns"]):
        px, py = P(x0 + (j + 0.5) * cw, y1 + 9)
        d.text((px - 6, py - 22), str(c), fill=MAGENTA)
    for i, c in enumerate(f3["rows_top_down"]):
        px, py = P(x1 + 14, y1 - (i + 0.5) * ch)
        d.text((px + 18, py - 6), str(c), fill=MAGENTA)
    im.save(out / "fig3_overlay.png", optimize=True)

    # Fig. 4
    for k, labels, xl in (("fig4a", ["<10", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80-89", "90-100"],
                            "Neighborhood Homophily (%)"),
                          ("fig4b", ["1-2", "2-3", "3-4", "4-5", "> 5"], "Avg. pairwise distance among disease-associated proteins")):
        ours_bars(a[k], labels, xl, out / f"{k}_ours.png")
        ax = FIG4_AXES[k]
        xs = [(b["x0"], b["x1"]) for b in pub[k]["bars"]]
        overlay_bars(pdir / f"{k}.png", crops[k], dpi, xs, a[k]["bars"], a[k]["spreads"]["var_values"], inv(ax["y"]),
                     out / f"{k}_overlay.png")

    # Supp. Fig. S2: four panels on one page crop
    im = grey(pdir / "figS2.png")
    im.save(out / "figS2_overlay.png")
    from read_published import linear_map  # noqa: F401

    fy = inv((43.2, 0.0, 388.8, 1.05))
    for panel, place in S2_PLACE.items():
        overlay_bars(out / "figS2_overlay.png", crops["figS2"], dpi, pub["figS2"]["_x"][panel], a["figS2"][panel], None, fy,
                     out / "figS2_overlay.png", place=place)
    # overlay_bars greys its input each time; redraw from the published crop once with all panels
    base = grey(pdir / "figS2.png")
    d = ImageDraw.Draw(base)
    P = Placer(crops["figS2"], dpi)
    for panel, place in S2_PLACE.items():
        for (x0, x1), h in zip(pub["figS2"]["_x"][panel], a["figS2"][panel]):
            if h is None:
                continue
            pa_ = P(place[0] + place[2] * x0, place[1] + place[2] * fy(h))
            pb_ = P(place[0] + place[2] * x1, place[1] + place[2] * fy(h))
            d.line([pa_, pb_], fill=MAGENTA, width=3)
    base.save(out / "figS2_overlay.png", optimize=True)
    fig, axs = plt.subplots(2, 2, figsize=(8, 6), dpi=150)
    for axx, (panel, labels) in zip(axs.ravel(), (
            ("a_precision", ["<10", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80-89", "90-100"]),
            ("a_recall", ["<10", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80-89", "90-100"]),
            ("b_precision", ["1-2", "2-3", "3-4", "4-5", "> 5"]), ("b_recall", ["1-2", "2-3", "3-4", "4-5", "> 5"]))):
        vals = [v or 0 for v in a["figS2"][panel]]
        axx.bar(range(len(vals)), vals, color="#bfbf00", edgecolor="black")
        axx.set_xticks(range(len(vals)))
        axx.set_xticklabels(labels, fontsize=6)
        axx.set_ylim(0, 1.05)
        axx.set_title(panel.replace("_", ", ").replace("a,", "neighborhood homophily,").replace("b,", "pairwise distance,"), fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "figS2_ours.png")
    plt.close(fig)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
